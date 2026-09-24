#!/usr/bin/env python3
"""WhiteHERO v3 stage 2: Qualify (plan section 6, Phase 1 step 1.2). stdlib + gh + curl only.

Modes
  qualify.py OWNER/REPO                 qualify one repo, print JSON (no DB write unless --write)
  qualify.py --batch 15 --from-db [--limit N]
                                        qualify targets rows with B IS NULL (15 repos per GraphQL
                                        query), then compute L for rows with B >= 0.4 and L IS NULL
  qualify.py --rescore                  recompute B, R from saved raw evidence (no API calls)
  qualify.py --lane L2 --seed seed/locale_targets.json --limit 20
                                        print target ids: seed-study repos + English-only flagships,
                                        not hard-excluded, ranked by B then L
  qualify.py --lane L5 --filter "partner|integration program" --limit 10
                                        print target ids: B >= 0.4 rows whose org homepage matches the
                                        regex (homepage fetched once, cached gzip in state/qualify-web)

Scoring (plan section 6)
  Hard exclusions first (B = 0): blocklist (state/blocklist.txt, or the plan's 12 names if absent),
  pushed > 90 d ago, archived, not found, owner is a User ('user-owned'). A CONTRIBUTING AI ban is
  not an exclusion (section 6 lists only the blocklist); it sets ai_policy='ban' and denies the 0.10.
  B = 0.20 org + 0.15 (website or isVerified) + 0.25 funding/revenue signal
      + 0.15 paid tooling in tree + 0.15 (commits >= 1000 and merged PRs >= 100)
      + 0.10 disclosure-only AI policy
  funding/revenue signal = no FUNDING.yml AND org homepage (not GitHub Pages / readthedocs)
      matches pricing or enterprise. funding_signal stores every matched keyword.
  R = 0.30 if contributions has a MERGED PR in this repo (contact 0.40 and defects 0.30 are
      filled later by the contacts and audit agents).
  L = 0.50 (median external merge < 48 h over the last 30 merged PRs)
      + 0.30 * min(1, maintainer interactions on external PRs in 30 d / 10)
      + 0.20 (pushed within 30 d)
  score = B * R * L
Evidence: state/qualify-raw/<org>__<repo>.json holds raw GraphQL + web + computed fields.
"""
import datetime, gzip, hashlib, json, os, re, sqlite3, statistics, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

PIPE = os.path.expanduser("~/oss-pipeline")
DB = os.path.join(PIPE, "state/kpi.db")
RAW = os.path.join(PIPE, "state/qualify-raw")
WEB = os.path.join(PIPE, "state/qualify-web")
BLOCK = os.path.join(PIPE, "state/blocklist.txt")
FLAGSHIP_FILE = os.path.join(PIPE, "state/flagships.json")
BUDGET_FILE = os.path.join(PIPE, "state/qualify-budget.json")
GQL_CAP = int(os.environ.get("QUALIFY_GQL_CAP", "4000"))  # my share of GraphQL points (brief)
GQL_FLOOR = 400      # never drive the shared GraphQL pool below this; sleep until reset instead
FALLBACK_BLOCK = ["tldraw", "ghostty", "zig", "netbsd", "gimp", "gentoo", "qemu", "tt-metal",
                  "documenso", "activepieces", "nuxt", "curl"]
TOOL_PATHS = {"crowdin": "crowdin.yml", "tx": ".tx/config", "lokalise": "lokalise.yml",
              "sentry": ".sentryclirc", "datadog": "datadog.yaml"}
WEB_RE = re.compile(r'/pricing|pricing|enterprise|book a demo|careers|jobs|customers', re.I)
AI_RE = re.compile(r'\b(AI|A\.I\.|LLMs?|Copilot|ChatGPT|Claude|Cursor|generative|AI[- ]generated|AI[- ]assisted|machine[- ]generated|language models?)\b')
BAN_RE = re.compile(r"\bban(ned|s)?\b|not accept|won't accept|will not accept|do not accept|don't accept|not allowed|prohibit|forbid|not permitted|reject(ed)? (any|all)", re.I)
DISC_RE = re.compile(r'disclos', re.I)
TODAY = datetime.datetime.now(datetime.timezone.utc)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"

# ---------------------------------------------------------------- quota
def rate():
    r = subprocess.run(["gh", "api", "rate_limit", "--jq", ".resources"], capture_output=True, text=True, timeout=30)
    d = json.loads(r.stdout)
    return {"core": d["core"]["remaining"], "search": d["search"]["remaining"],
            "graphql": d["graphql"]["remaining"], "greset": d["graphql"]["reset"]}

def budget_load():
    try: return json.load(open(BUDGET_FILE))
    except Exception: return {"graphql_points": 0, "queries": 0, "web_fetches": 0}

def budget_save(b):
    json.dump(b, open(BUDGET_FILE, "w"))

BUD = budget_load()

def gate(need=20):
    """Yield (sleep until reset) rather than drain the shared pool; stop at my cap."""
    if BUD["graphql_points"] + need > GQL_CAP:
        raise SystemExit(f"STOP: my GraphQL cap reached ({BUD['graphql_points']} of {GQL_CAP} points)")
    rl = rate()
    if rl["graphql"] < GQL_FLOOR + need:
        s = max(1, rl["greset"] - int(time.time()) + 5)
        print(f"  graphql remaining {rl['graphql']}; yielding {s}s until reset", flush=True)
        time.sleep(s)

def gql(query):
    delay = 20
    for t in range(4):
        r = subprocess.run(["gh", "api", "graphql", "-f", "query=" + query], capture_output=True, text=True, timeout=240)
        try:
            d = json.loads(r.stdout)
        except Exception:
            d = None
        if d and "data" in d and d["data"] is not None:
            cost = (d["data"].get("rateLimit") or {}).get("cost", 1)
            BUD["graphql_points"] += cost; BUD["queries"] += 1; budget_save(BUD)
            return d
        err = (r.stdout[:300] + " " + r.stderr[:300]).strip()
        print(f"  graphql error try {t+1}: {err}", flush=True)
        if t < 3:
            time.sleep(delay); delay *= 2
    raise SystemExit("STOP: graphql failed after 20/40/80 s backoff: " + err)

# ---------------------------------------------------------------- inputs
def blocklist():
    if os.path.exists(BLOCK):
        ents = []
        for line in open(BLOCK):
            line = line.split("#", 1)[0].strip()
            if line:
                ents.append(line.split()[0].strip().lower().rstrip("/"))
        if ents:
            return ents, "state/blocklist.txt"
    return FALLBACK_BLOCK, "fallback (plan 0.7 names)"

def blocked(org, repo, ents):
    o, r, full = org.lower(), repo.lower(), f"{org}/{repo}".lower()
    for e in ents:
        e = e.replace("https://github.com/", "")
        if "/" in e:
            if full == e: return e
        elif o == e or r == e:
            return e
    return None

def our_merged(con, org, repo):
    n = con.execute("select count(*) from contributions where lower(repo)=lower(?) and upper(status)='MERGED'",
                    (f"{org}/{repo}",)).fetchone()[0]
    return n > 0

# ---------------------------------------------------------------- GraphQL
def esc(s): return s.replace('\\', '').replace('"', '')

def frag_b(i, org, repo):
    objs = " ".join(f'{k}: object(expression:"HEAD:{p}"){{ oid }}' for k, p in TOOL_PATHS.items())
    return f'''r{i}: repository(owner:"{esc(org)}",name:"{esc(repo)}"){{
  nameWithOwner stargazerCount pushedAt isArchived isFork homepageUrl
  primaryLanguage{{name}} licenseInfo{{spdxId}}
  defaultBranchRef{{ name target{{ ... on Commit{{ history{{ totalCount }} }} }} }}
  mergedPRs: pullRequests(states:MERGED){{ totalCount }}
  owner{{ __typename login ... on Organization{{ websiteUrl isVerified }} }}
  fund1: object(expression:"HEAD:.github/FUNDING.yml"){{ oid }}
  fund2: object(expression:"HEAD:FUNDING.yml"){{ oid }}
  {objs}
  contrib1: object(expression:"HEAD:CONTRIBUTING.md"){{ ... on Blob{{ byteSize text }} }}
  contrib2: object(expression:"HEAD:.github/CONTRIBUTING.md"){{ ... on Blob{{ byteSize text }} }}
}}'''

def frag_l(i, org, repo):
    return f'''r{i}: repository(owner:"{esc(org)}",name:"{esc(repo)}"){{
  merged: pullRequests(states:MERGED, last:30, orderBy:{{field:CREATED_AT, direction:ASC}}){{
    nodes{{ number createdAt mergedAt authorAssociation author{{ __typename login }} }} }}
  recent: pullRequests(last:30, orderBy:{{field:CREATED_AT, direction:ASC}}){{
    nodes{{ number createdAt authorAssociation author{{ __typename login }} comments{{ totalCount }} reviews{{ totalCount }} }} }}
}}'''

def batch_query(frag, pairs):
    body = "\n".join(frag(i, o, r) for i, (o, r) in enumerate(pairs))
    return "query{ rateLimit{ cost remaining resetAt }\n" + body + "\n}"

# ---------------------------------------------------------------- website
def is_static_docs_host(url, headers):
    h = (urlparse(url).hostname or "").lower()
    if h.endswith((".github.io", ".readthedocs.io", ".readthedocs.org", ".rtfd.io")) or h in ("github.com", "readthedocs.org"):
        return True
    hl = headers.lower()
    return "\nserver: github.com" in hl or "x-rtd-" in hl or "x-readthedocs" in hl

def web_key(url): return hashlib.sha1(url.encode()).hexdigest()[:16]

def fetch_site(url, refetch=False):
    """Fetch homepage once (10 s, follow redirects, 300 KB cap); cache meta + gzip body."""
    if not url: return None
    if not re.match(r'^https?://', url): url = "https://" + url
    k = web_key(url); meta_p = os.path.join(WEB, k + ".json")
    if os.path.exists(meta_p) and not refetch:
        return json.load(open(meta_p))
    hdr_p = os.path.join(WEB, k + ".hdr")
    try:
        p = subprocess.Popen(["curl", "-sL", "-m", "10", "-A", UA, "-D", hdr_p, "-o", "-",
                              "-w", "", url], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        body = p.stdout.read(300_000)
        p.kill(); p.wait()
    except Exception as e:
        body = b""
    headers = open(hdr_p, errors="replace").read() if os.path.exists(hdr_p) else ""
    finals = re.findall(r'(?im)^location:\s*(\S+)', headers)
    final = url
    for loc in finals:
        final = loc if loc.startswith("http") else final
    text = body.decode("utf-8", "replace")
    matches = sorted(set(m.lower() for m in WEB_RE.findall(text)))
    static = is_static_docs_host(final, "\n" + headers)
    status = re.findall(r'(?m)^HTTP/\S+\s+(\d{3})', headers)
    meta = {"url": url, "final_url": final, "status": status[-1] if status else None, "bytes": len(body),
            "static_docs_host": static, "matches": matches, "fetched_at": TODAY.isoformat(timespec="seconds")}
    with gzip.open(os.path.join(WEB, k + ".html.gz"), "wb") as f: f.write(body)
    json.dump(meta, open(meta_p, "w"))
    BUD["web_fetches"] += 1
    return meta

def site_text(url):
    if not url: return ""
    if not re.match(r'^https?://', url): url = "https://" + url
    p = os.path.join(WEB, web_key(url) + ".html.gz")
    if not os.path.exists(p): fetch_site(url)
    try: return gzip.open(p).read().decode("utf-8", "replace")
    except Exception: return ""

def site_url(x):
    own = (x or {}).get("owner") or {}
    return own.get("websiteUrl") or (x or {}).get("homepageUrl") or ""

# ---------------------------------------------------------------- scoring
def ai_policy(text):
    if not text: return "no-contributing"
    hits = [m.start() for m in AI_RE.finditer(text)]
    if not hits: return "none"
    ban = disc = False
    for h in hits:
        w = text[max(0, h - 300): h + 300]
        for b in BAN_RE.finditer(w):
            pre, post = w[max(0, b.start() - 30): b.start()], w[b.end(): b.end() + 12]
            negated = not b.group(0).lower().startswith(("not", "won't", "will not", "do not", "don't")) and \
                re.search(r"\b(not|no|never)\b|n't", pre, re.I)
            if negated or re.match(r"\W{0,3}\s*No\b", post):
                continue          # "does not prohibit", "not (yet) banned", "banned? No."
            ban = True
        if DISC_RE.search(w): disc = True
    if ban: return "ban"
    if disc: return "disclosure"
    return "mentions-ai"

def days_since(ts):
    return (TODAY - datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))).days

def compute_b(org, repo, x, site, block_ents, con):
    c = {"exclusion": None}
    if x is None:
        c["exclusion"] = "not-found"; return 0.0, c
    own = x["owner"]; is_org = own["__typename"] == "Organization"
    commits = (((x.get("defaultBranchRef") or {}).get("target") or {}).get("history") or {}).get("totalCount", 0)
    merged = x["mergedPRs"]["totalCount"]
    contrib = (x.get("contrib1") or {}).get("text") or (x.get("contrib2") or {}).get("text") or ""
    has_contrib = bool(x.get("contrib1") or x.get("contrib2"))
    funding_yml = bool(x.get("fund1") or x.get("fund2"))
    tms = [k for k in TOOL_PATHS if x.get(k)]
    pol = ai_policy(contrib) if has_contrib else "no-contributing"
    website = site_url(x)
    fund_ok = False; fsig = None
    if site:
        m = site["matches"]
        fsig = ",".join(m) if m else None
        if site["static_docs_host"]: fsig = (fsig + ";" if fsig else "") + "static-docs-host"
        fund_ok = any(k in ("pricing", "/pricing", "enterprise") for k in m) and not site["static_docs_host"]
        if fund_ok and funding_yml:
            fsig += ";void:FUNDING.yml"; fund_ok = False
    comp = {
        "org": 0.20 if is_org else 0.0,
        "website_or_verified": 0.15 if is_org and (own.get("websiteUrl") or own.get("isVerified")) else 0.0,
        "funding_signal": 0.25 if fund_ok else 0.0,
        "paid_tooling": 0.15 if tms else 0.0,
        "commits_prs": 0.15 if commits >= 1000 and merged >= 100 else 0.0,
        "ai_disclosure_only": 0.10 if pol == "disclosure" else 0.0,
    }
    b_raw = round(sum(comp.values()), 2)
    pushed_days = days_since(x["pushedAt"]) if x.get("pushedAt") else 9999
    b_hit = blocked(org, repo, block_ents) or blocked(*x["nameWithOwner"].split("/", 1), block_ents)
    if b_hit: c["exclusion"] = f"blocklist:{b_hit}"
    elif x.get("isArchived"): c["exclusion"] = "archived"
    elif pushed_days > 90: c["exclusion"] = "pushed>90d"
    elif not is_org: c["exclusion"] = "user-owned"
    c.update({"name_with_owner": x["nameWithOwner"], "owner_type": own["__typename"], "commits": commits,
              "merged_prs": merged, "website": website or None, "is_verified": own.get("isVerified"),
              "license": (x.get("licenseInfo") or {}).get("spdxId"), "funding_yml": funding_yml,
              "funding_signal": fsig, "tms": ",".join(tms) or None, "ai_policy": pol,
              "pushed_days": pushed_days, "stars": x["stargazerCount"],
              "lang": (x.get("primaryLanguage") or {}).get("name"), "components": comp, "B_raw": b_raw,
              "our_merged_pr": our_merged(con, org, repo)})
    return (0.0 if c["exclusion"] else b_raw), c

EXTERNAL = {"CONTRIBUTOR", "FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER", "NONE"}

def is_bot(n):
    a = n.get("author") or {}
    return a.get("__typename") == "Bot" or (a.get("login") or "").endswith("[bot]")

def compute_l(y, pushed_days):
    merged = [n for n in ((y or {}).get("merged") or {}).get("nodes", []) if n and n.get("mergedAt")]
    ext = [n for n in merged if n["authorAssociation"] in EXTERNAL and not is_bot(n)]
    lat = [(datetime.datetime.fromisoformat(n["mergedAt"].replace("Z", "+00:00")) -
            datetime.datetime.fromisoformat(n["createdAt"].replace("Z", "+00:00"))).total_seconds() / 3600 for n in ext]
    med = round(statistics.median(lat), 1) if len(lat) >= 3 else None
    recent = [n for n in ((y or {}).get("recent") or {}).get("nodes", []) if n]
    ext30 = [n for n in recent if n["authorAssociation"] in EXTERNAL and not is_bot(n) and days_since(n["createdAt"]) <= 30]
    inter = sum(n["comments"]["totalCount"] + n["reviews"]["totalCount"] for n in ext30)
    comp = {"median_ext_merge_lt_48h": 0.50 if med is not None and med < 48 else 0.0,
            "comment_velocity": round(0.30 * min(1.0, inter / 10), 3),
            "pushed_30d": 0.20 if pushed_days <= 30 else 0.0}
    return round(sum(comp.values()), 3), {"external_merged_n": len(ext), "median_ext_merge_h": med,
                                          "external_prs_30d": len(ext30), "interactions_30d": inter,
                                          "L_components": comp}

# ---------------------------------------------------------------- pipeline
def raw_path(org, repo): return os.path.join(RAW, f"{org}__{repo}.json".replace("/", "_"))

def qualify_pairs(pairs, con, block_ents, refetch=False):
    """pairs: list of (org, repo). Returns list of result dicts (B phase only)."""
    gate(30)
    d = gql(batch_query(frag_b, pairs))
    data = d["data"]
    errs = [e for e in d.get("errors", []) if e.get("type") != "NOT_FOUND"]
    if errs:
        raise SystemExit("STOP: B query returned errors (file-presence nulls would be unreliable): " + json.dumps(errs[:3])[:500])
    xs = [data.get(f"r{i}") for i in range(len(pairs))]
    urls = {}
    for x in xs:
        if x and x["owner"]["__typename"] == "Organization":
            u = site_url(x)
            if u: urls[u] = None
    with ThreadPoolExecutor(8) as ex:
        for u, meta in zip(urls, ex.map(lambda u: fetch_site(u, refetch), list(urls))):
            urls[u] = meta
    budget_save(BUD)
    out = []
    for (org, repo), x in zip(pairs, xs):
        site = urls.get(site_url(x)) if x else None
        B, c = compute_b(org, repo, x, site, block_ents, con)
        R = 0.30 if c.get("our_merged_pr") else 0.0
        res = {"org": org, "repo": repo, "B": B, "R": R, **c}
        rec = {"org": org, "repo": repo, "qualified_at": TODAY.isoformat(timespec="seconds"),
               "graphql_b": x, "graphql_errors": [e for e in d.get("errors", []) if (e.get("path") or [None])[0] == f"r{pairs.index((org, repo))}"],
               "rateLimit": data.get("rateLimit"), "web": site, "computed": res}
        json.dump(rec, open(raw_path(org, repo), "w"), indent=1)
        out.append(res)
    return out

def latency_pairs(pairs_pd, con=None):
    """pairs_pd: list of (org, repo, pushed_days). Adds L to raw files; returns {(org,repo): (L, info)}."""
    gate(60)
    pairs = [(o, r) for o, r, _ in pairs_pd]
    d = gql(batch_query(frag_l, pairs))
    res = {}
    for i, (o, r, pdays) in enumerate(pairs_pd):
        y = d["data"].get(f"r{i}")
        bad = [e for e in d.get("errors", []) if (e.get("path") or [None])[0] == f"r{i}"]
        if bad or y is None or any(n is None for k in ("merged", "recent") for n in (y.get(k) or {}).get("nodes", [])):
            # RESOURCE_LIMITS_EXCEEDED nulls PR nodes in heavy batches: re-ask this repo alone
            print(f"  L retry alone {o}/{r}: {bad[0].get('type') if bad else 'null nodes'}", flush=True)
            d1 = gql(batch_query(frag_l, [(o, r)]))
            y = d1["data"].get("r0")
            if y is None or d1.get("errors") or any(n is None for k in ("merged", "recent") for n in (y.get(k) or {}).get("nodes", [])):
                raise SystemExit(f"STOP: L query still incomplete for {o}/{r}: {json.dumps(d1.get('errors'))[:300]}")
        L, info = compute_l(y, pdays)
        p = raw_path(o, r)
        rec = json.load(open(p)) if os.path.exists(p) else {"org": o, "repo": r}
        rec["graphql_l"] = y; rec["latency"] = info; rec["latency_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"); rec["computed"]["L"] = L
        json.dump(rec, open(p, "w"), indent=1)
        res[(o, r)] = (L, info)
    return res

def write_row(con, res):
    con.execute("""update targets set stars=?, commits=?, merged_prs=?, owner_type=?, website=?, funding_signal=?,
                   tms=?, ai_policy=?, B=?, R=?, lang=coalesce(lang, ?) where org=? and repo=?""",
                (res.get("stars"), res.get("commits"), res.get("merged_prs"), res.get("owner_type"), res.get("website"),
                 res.get("funding_signal"), res.get("tms"), res.get("ai_policy"), res["B"], res["R"], res.get("lang"),
                 res["org"], res["repo"]))

def run_batch(size, limit):
    con = sqlite3.connect(DB, timeout=30)
    ents, src = blocklist()
    print(f"blocklist: {len(ents)} entries from {src}", flush=True)
    rows = con.execute("select org, repo from targets where B is null order by id" + (f" limit {int(limit)}" if limit else "")).fetchall()
    print(f"B phase: {len(rows)} rows with B IS NULL; graphql remaining {rate()['graphql']}", flush=True)
    done = 0
    for i in range(0, len(rows), size):
        chunk = rows[i:i + size]
        out = qualify_pairs(chunk, con, ents)
        for res in out: write_row(con, res)
        con.commit(); done += len(chunk)
        print(f"  B {done}/{len(rows)}  points used {BUD['graphql_points']}  web fetches {BUD['web_fetches']}", flush=True)
    # L phase for rows passing the B gate
    lrows = con.execute("select org, repo from targets where B >= 0.4 and L is null order by id").fetchall()
    print(f"L phase: {len(lrows)} rows with B >= 0.4 and L IS NULL", flush=True)
    lsize = min(size, 5)
    for i in range(0, len(lrows), lsize):
        chunk = []
        for o, r in lrows[i:i + lsize]:
            rec = json.load(open(raw_path(o, r)))
            chunk.append((o, r, rec["computed"].get("pushed_days", 9999)))
        lres = latency_pairs(chunk)
        for (o, r), (L, info) in lres.items():
            B, R = con.execute("select B, R from targets where org=? and repo=?", (o, r)).fetchone()
            con.execute("update targets set L=?, score=? where org=? and repo=?", (L, round(B * R * L, 4), o, r))
        con.commit()
        print(f"  L {min(i+lsize, len(lrows))}/{len(lrows)}  points used {BUD['graphql_points']}", flush=True)
    # rows below the gate: score = 0 (B*R*L with L not computed)
    con.execute("update targets set score=0 where B is not null and B < 0.4 and score is null")
    con.commit()
    n_left = con.execute("select count(*) from targets where B is null").fetchone()[0]
    con.execute("insert into runs(ts, layer, discovered, verified, notes) values(?,?,?,?,?)",
                (TODAY.isoformat(timespec="seconds"), "v3-qualify", len(rows), done,
                 f"B computed {done}; L computed {len(lrows)}; B null remaining {n_left}; graphql points {BUD['graphql_points']}; web fetches {BUD['web_fetches']}; blocklist {src}"))
    con.commit()
    print(f"done. B null remaining: {n_left}; graphql points used total {BUD['graphql_points']}")

def run_single(full, write=False, refetch=False):
    org, repo = full.split("/", 1)
    con = sqlite3.connect(DB, timeout=30)
    ents, src = blocklist()
    res = qualify_pairs([(org, repo)], con, ents, refetch)[0]
    if res["B"] >= 0.4:
        L, info = latency_pairs([(org, repo, res["pushed_days"])])[(org, repo)]
        res["L"] = L; res["latency"] = info; res["score"] = round(res["B"] * res["R"] * L, 4)
    if write:
        write_row(con, res)
        if "L" in res:
            con.execute("update targets set L=?, score=? where org=? and repo=?", (res["L"], res["score"], org, repo))
        con.commit()
    print(json.dumps(res, indent=1, default=str))

def run_rescore():
    """Recompute B and R from state/qualify-raw + state/qualify-web (no API calls)."""
    con = sqlite3.connect(DB, timeout=30)
    ents, src = blocklist()
    n = 0
    for org, repo in con.execute("select org, repo from targets where B is not null").fetchall():
        p = raw_path(org, repo)
        if not os.path.exists(p): continue
        rec = json.load(open(p)); x = rec.get("graphql_b")
        site = fetch_site(site_url(x)) if x and x["owner"]["__typename"] == "Organization" and site_url(x) else None
        B, c = compute_b(org, repo, x, site, ents, con)
        R = 0.30 if c.get("our_merged_pr") else 0.0
        res = {"org": org, "repo": repo, "B": B, "R": R, **c}
        if "L" in rec.get("computed", {}): res["L"] = rec["computed"]["L"]
        rec["computed"] = res
        json.dump(rec, open(p, "w"), indent=1)
        write_row(con, res)
        L = con.execute("select L from targets where org=? and repo=?", (org, repo)).fetchone()[0]
        con.execute("update targets set score=? where org=? and repo=?", (round(B * R * L, 4) if L is not None else 0, org, repo))
        n += 1
    con.commit()
    print(f"rescored {n} rows from raw evidence (blocklist {src})")

def flagship_set():
    try: return {v["fullName"].lower() for v in json.load(open(FLAGSHIP_FILE)).values()}
    except Exception: return set()

def run_lane(lane, seed, filt, limit):
    con = sqlite3.connect(DB, timeout=30)
    rows = con.execute("select id, org, repo, B, L, owner_type from targets where B is not null").fetchall()
    if lane == "L2":
        want = set(flagship_set())
        if seed:
            want |= {r[0].lower() for r in json.load(open(os.path.join(PIPE, seed) if not os.path.isabs(seed) else seed))["rows"]}
        sel = []
        for id_, o, r, B, L, ot in rows:
            if f"{o}/{r}".lower() not in want: continue
            p = raw_path(o, r)
            comp = json.load(open(p))["computed"] if os.path.exists(p) else {}
            exc = comp.get("exclusion")
            if exc and exc != "user-owned": continue       # L2 does not require an org owner
            sel.append((comp.get("B_raw", B) or 0, L or 0, id_, o, r))
    else:
        sel = [((B or 0), (L or 0), id_, o, r) for id_, o, r, B, L, ot in rows if (B or 0) >= 0.4]
    sel.sort(key=lambda t: (-t[0], -t[1], t[2]))
    rx = re.compile(filt, re.I) if filt else None
    n = 0
    for B, L, id_, o, r in sel:
        if rx:
            p = raw_path(o, r)
            url = (json.load(open(p))["computed"].get("website") if os.path.exists(p) else None)
            m = rx.search(site_text(url)) if url else None
            if not m: continue
            print(f"{id_}\t{o}/{r}\tB={B}\tL={L}\tmatch={m.group(0)!r}\t{url}")
        else:
            print(f"{id_}\t{o}/{r}\tB={B}\tL={L}")
        n += 1
        if limit and n >= limit: break

def main():
    a = sys.argv[1:]
    def opt(name, default=None):
        return a[a.index(name) + 1] if name in a and a.index(name) + 1 < len(a) else default
    if "--lane" in a:
        return run_lane(opt("--lane"), opt("--seed"), opt("--filter"), int(opt("--limit", "0")))
    if "--rescore" in a:
        return run_rescore()
    if "--batch" in a:
        return run_batch(int(opt("--batch", "15")), opt("--limit"))
    pos = [x for x in a if "/" in x and not x.startswith("-")]
    if pos:
        return run_single(pos[0], write="--write" in a, refetch="--refetch" in a)
    print(__doc__); sys.exit(2)

if __name__ == "__main__":
    main()
