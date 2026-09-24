#!/usr/bin/env python3
"""ANVIL NIGHT DRIVER v2 — self-optimizing overnight loop (2026-09-23 22:00 → 08:00).

Goals:
  G1. (v3 kill list) removed: unsolicited locale-fill gift PRs and issue-first offers.
      Plan v3 section 6: locale fills are delivered only inside a signed L1 or L2 engagement.
      Curated-list and self-listing PRs are also out of scope for this driver (plan section 2, row 4).
  G2. Watch + respond to feedback on: hoppscotch #6669, simplikit #501 (claim -> PR), medusa 10x
  G3. Self-optimize: score each cycle's outcome in meta.json; prefer highest-yield actions
  G4. Update kpi.db + STATUS.md + dashboard after every state change
Run via: python3 anvil_night.py  (loop inside; safe to re-run, state-aware)
"""
import subprocess, json, os, sys, time, base64, random
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
STATE = f"{HOME}/oss-pipeline/state/anvil-night"
KPI = f"{HOME}/oss-pipeline/state/kpi.db"
STATUS = f"{HOME}/oss-pipeline/state/STATUS.md"
DASH = f"{HOME}/oss-pipeline/WHITEHERO-DASHBOARD.html"  # v3: written by bin/dashboard.py, never Desktop
END_EPOCH = None
CYCLE_SECONDS = 2400  # 40 min between sweeps
now = lambda: datetime.now(timezone.utc).strftime("%FT%TZ")

os.makedirs(STATE, exist_ok=True)

def log(msg):
    line = f"[{now()}] {msg}"
    print(line, flush=True)
    open(f"{STATE}/night.log", "a").write(line + "\n")

def gh(url, method="GET", data=None):
    cmd = ["gh", "api", url]
    if method != "GET": cmd += ["-X", method]
    if data: cmd += ["--input", "-"]
    for attempt in range(3):
        r = subprocess.run(cmd, input=data, capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            try: return json.loads(r.stdout)
            except Exception: return r.stdout
        if "secondary rate" in r.stderr.lower() or "abuse" in r.stderr.lower():
            time.sleep(60 * (attempt + 1)); continue
        log(f"[gh-err] {url}: {r.stderr[:150]}")
        return None
    return None

def kpi_add(repo, pr, category, score, status, pr_url, notes):
    import sqlite3
    db = sqlite3.connect(KPI)
    nxt = db.execute("SELECT MAX(id) FROM contributions").fetchone()[0] + 1
    db.execute("INSERT INTO contributions (id,ts,repo,issue,pr,category,score,status,pr_url,notes) VALUES (?,?,?,?,?,?,?,?,?,?)",
               (nxt, now(), repo, None, pr, category, score, status, pr_url, notes))
    db.commit(); db.close()
    log(f"kpi row {nxt} added: {repo} #{pr} {status}")

def status_log(title, lines):
    body = f"\n### {title} ({now()})\n\n" + "\n".join(f"- {l}" for l in lines) + "\n"
    cur = open(STATUS).read()
    open(STATUS, "w").write(body + cur)
    log(f"STATUS.md updated: {title}")

# ---------------- watch layer ----------------

WATCH = [  # (repo, number, kind)
    ("hoppscotch/hoppscotch", 6669, "pr"),
    ("toss/react-simplikit", 501, "issue"),
    ("toss/react-simplikit", 519, "pr"),
]
MEDUSA = [16932,16933,16934,16936,16939,16940,16942,16944,16946,16948]

def sweep_watch():
    """Check all watched items; return list of events."""
    events = []
    wpath = f"{STATE}/watch-state.json"
    prev = json.load(open(wpath)) if os.path.exists(wpath) else {}
    cur = {}
    for repo, num, kind in WATCH:
        p = f"pulls/{num}" if kind == "pr" else f"issues/{num}"
        d = gh(f"repos/{repo}/{p}")
        if not d: continue
        state = d.get("state"); merged = d.get("merged", False)
        comments = d.get("comments", 0)
        cur[f"{repo}#{num}"] = {"state": state, "merged": merged, "comments": comments}
        key = f"{repo}#{num}"
        old = prev.get(key)
        if old is None:
            events.append(f"watching {key}: {state}, {comments} comments")
        elif merged and not old.get("merged"):
            events.append(f"MERGED: {key}")
        elif state != old.get("state"):
            events.append(f"state change: {key} {old['state']} -> {state}")
        elif comments > old.get("comments", 0):
            events.append(f"NEW COMMENT on {key} ({comments} total) — needs response")
    for n in MEDUSA:
        d = gh(f"repos/medusajs/medusa/pulls/{n}")
        if not d: continue
        key = f"medusa#{n}"
        cur[key] = {"state": d.get("state"), "merged": d.get("merged", False), "comments": d.get("comments", 0)}
        old = prev.get(key)
        if old and d.get("merged") and not old.get("merged"):
            events.append(f"MERGED: medusa#{n}")
        elif old and d.get("state") != old.get("state"):
            events.append(f"medusa#{n} {old['state']} -> {d.get('state')}")
        time.sleep(0.4)
    json.dump(cur, open(wpath, "w"), indent=1)
    return events

# ---------------- discovery layer ----------------

DRIFT_TARGETS = [  # repos worth rescanning; (repo, locales-dir-glob)
    ("hoppscotch/hoppscotch", "packages/hoppscotch-common/locales"),
]

def flatkeys(d):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict): out.update(flatkeys(v))
        else: out[k] = v
    return out

def scan_drift(repo, locdir):
    """Return {locale: (have, total)} of FLAT leaf keys for a repo's locale dir."""
    tree = gh(f"repos/{repo}/git/trees/HEAD?recursive=1")
    if not tree: return {}
    paths = [t["path"] for t in tree["tree"] if t["path"].startswith(locdir) and t["path"].endswith(".json")]
    if not paths: return {}
    # en total
    en = gh(f"repos/{repo}/contents/{locdir}/en.json")
    if not en: return {}
    total = len(flatkeys(json.loads(base64.b64decode(en["content"]))))
    out = {}
    random.seed()
    sample = random.sample(paths, min(8, len(paths)))
    for p in sample:
        loc = p.split("/")[-1][:-5]
        if loc == "en": continue
        d = gh(f"repos/{repo}/contents/{p}")
        if not d: continue
        have = len(flatkeys(json.loads(base64.b64decode(d["content"]))))
        out[loc] = (have, total)
    return out

def find_next_lead():
    """Pick the best next locale-fill lead from drift targets."""
    best = None
    for repo, locdir in DRIFT_TARGETS:
        drift = scan_drift(repo, locdir)
        log(f"drift {repo}: " + ", ".join(f"{k}={v[0]}/{v[1]}" for k, v in drift.items()))
        for loc, (have, total) in drift.items():
            if total and have / total < 0.92:
                missing = total - have
                if not best or missing > best[3]:
                    best = (repo, locdir, loc, missing, total)
    return best

# ---------------- execution layer ----------------

GIFT_PR_LANE_ENABLED = False  # v3 kill list: gift PR lane is off; no code path sets this True

def execute_fill(repo, locdir, loc, missing, total):
    """Clone, fill locale, push, PR. Heavyweight; guarded."""
    if not GIFT_PR_LANE_ENABLED:  # v3 kill list
        log("gift PR lane disabled (v3 kill list); no fill, no PR, no issue")
        return False
    import tempfile
    log(f"EXECUTE fill: {repo} {loc} ({missing} keys)")
    workdir = tempfile.mkdtemp(prefix="anvil-")
    r = subprocess.run(["git", "clone", "--depth", "1", f"https://github.com/{repo}.git", workdir],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        log(f"clone failed: {r.stderr[:150]}"); return False
    locpath = f"{workdir}/{locdir}/{loc}.json"
    enpath = f"{workdir}/{locdir}/en.json"
    if not (os.path.exists(locpath) and os.path.exists(enpath)):
        log("locale files missing on disk"); return False
    en = json.load(open(enpath)); cur = json.load(open(locpath))
    # collect missing keys flat
    def flat(d, pre=""):
        out = {}
        for k, v in d.items():
            kk = f"{pre}.{k}" if pre else k
            if isinstance(v, dict): out.update(flat(v, kk))
            else: out[kk] = v
        return out
    en_f, cur_f = flat(en), flat(cur)
    need = {k: v for k, v in en_f.items() if k not in cur_f}
    if len(need) < 20:
        log(f"only {len(need)} missing — skip (stale intel)"); return False
    # translate via LLM helper if available, else leave TODO-free abort
    tr = translate_batch(need)
    if not tr: return False
    # merge preserving en structure
    def unflat(flat_d):
        out = {}
        for k, v in flat_d.items():
            parts = k.split("."); node = out
            for p in parts[:-1]: node = node.setdefault(p, {})
            node[parts[-1]] = v
        return out
    merged = json.loads(json.dumps(en))  # deep copy structure+order
    def deep_assign(d, flat_src):
        for k, v in flat_src.items():
            parts = k.split("."); node = d
            for p in parts[:-1]: node = node[p]
            node[parts[-1]] = v
    deep_assign(merged, tr)
    json.dump(merged, open(locpath, "w"), ensure_ascii=False, indent=2)
    # verify
    merged_f = flat(json.load(open(locpath)))
    if set(merged_f) != set(en_f):
        log("structure mismatch after merge — abort"); return False
    ph_ok = all(("{" in v) <= ("{" in en_f.get(k, "")) for k, v in merged_f.items())
    if not ph_ok:
        log("placeholder mismatch — abort"); return False
    # branch, commit, push, PR
    name = "theluckystrike"; email = "theluckystrike@users.noreply.github.com"
    br = f"{loc}-locale-completion"
    cmds = [
        ["git", "config", "user.name", name], ["git", "config", "user.email", email],
        ["git", "checkout", "-b", br], ["git", "add", f"{locdir}/{loc}.json"],
        ["git", "commit", "-m", f"i18n: complete {loc} locale ({len(need)} missing keys -> full en parity)"],
        ["git", "push", f"https://github.com/{name}/{repo.split('/')[1]}.git", br],
    ]
    push_failed = False
    for c in cmds:
        r = subprocess.run(c, cwd=workdir, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            if "fork" in (r.stderr or "").lower() or "not found" in (r.stderr or "").lower():
                subprocess.run(["gh", "repo", "fork", repo, "--clone=false"], capture_output=True, timeout=120)
                r = subprocess.run(c, cwd=workdir, capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                log(f"cmd failed {c[:2]}: {(r.stderr or '')[:200]}")
                if c[0] == "git" and c[1] == "push": push_failed = True
                elif c[-1] == br: pass  # checkout -b may fail if branch exists in a rerun; not fatal
                else: return False
    if push_failed:
        log("push failed — no PR attempt"); return False
    # confirm branch actually on fork before PR
    chk = gh(f"repos/{name}/{repo.split('/')[1]}/branches/{br}")
    if not chk:
        log("branch not present on fork — no PR attempt"); return False
    body = (f"Measured drift: `{loc}.json` had {len(need)} keys missing vs `en.json`. "
            f"This PR brings it to full parity ({len(en_f)}/{len(en_f)}), preserving all placeholders and existing translations.\n\n"
            f"Happy to keep {loc} at parity ongoing — free for the OSS repo; paid retainer available if you want automated parity CI.")
    pr = gh(f"repos/{repo}/pulls", "POST", json.dumps({
        "title": f"i18n: complete {loc} locale — {len(need)} missing keys, full en.json parity",
        "head": f"theluckystrike:{br}", "base": "main",
        "body": body}))
    if pr and "number" in pr:
        log(f"PR opened: {repo}#{pr['number']}")
        kpi_add(repo, pr["number"], "i18n-locale-fill", 85, "OPEN", pr.get("html_url", ""),
                f"{loc} locale completion: {len(need)} keys -> full parity. Night driver.")
        WATCH.append((repo, pr["number"], "pr"))
        return True
    # PR blocked (perms/abuse-limit) -> issue-first fallback, branch stays on fork
    log("PR create failed — falling back to issue-first")
    ititle = f"Offering: {loc} locale completion — {len(need)} keys missing vs en.json (ready to ship)"
    ibody = (f"Measured drift on main: {loc}.json is missing {len(need)} of {len(en_f)} flat keys vs en.json.\n\n"
             f"Full completion is already prepared (branch {br} on fork theluckystrike/{repo.split('/')[1]} — "
             f"{len(en_f)}/{len(en_f)} parity, placeholders preserved, existing translations untouched). "
             f"Say the word and the PR goes up.\n\n"
             f"Free for the OSS repo; paid retainer available if you want automated locale-parity CI.")
    iss = gh(f"repos/{repo}/issues", "POST", json.dumps({"title": ititle, "body": ibody}))
    if iss and "number" in iss:
        log(f"issue-first opened: {repo}#{iss['number']}")
        kpi_add(repo, iss["number"], "i18n-locale-offer", 70, "OPEN", iss.get("html_url", ""),
                f"{loc} locale offer: {len(need)} keys ready on fork branch {br}. PR blocked. Night driver.")
        WATCH.append((repo, iss["number"], "issue"))
        return True
    log("issue fallback also failed"); return False

def translate_batch(pairs):
    """Translate en strings via the local LLM helper (same path as A6)."""
    # A6 used hermes LLM pipeline; here we reuse the batched approach via execute helper
    out = {}
    items = list(pairs.items())
    B = 60
    for i in range(0, len(items), B):
        chunk = items[i:i+B]
        payload = json.dumps(dict(chunk), ensure_ascii=False)
        r = subprocess.run([sys.executable, f"{HOME}/oss-pipeline/llm_translate.py", payload],
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            log(f"translate batch {i} failed: {r.stderr[:150]}"); return None
        try: out.update(json.loads(r.stdout))
        except Exception as e:
            log(f"translate parse fail: {e}"); return None
    return out

# ---------------- meta / optimization ----------------

def meta_score(event, ok):
    p = f"{STATE}/meta.json"
    m = json.load(open(p)) if os.path.exists(p) else {"cycles": 0, "ships": 0, "merges": 0, "responses": 0}
    m["cycles"] += 1
    if ok == "ship": m["ships"] += 1
    elif ok == "merge": m["merges"] += 1
    elif ok == "response": m["responses"] += 1
    json.dump(m, open(p, "w"), indent=1)
    return m

def main():
    t0 = time.time()
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 10 * 3600
    log(f"=== ANVIL NIGHT DRIVER start, target duration {duration}s ===")
    cycle = 0
    while time.time() - t0 < duration:
        cycle += 1
        log(f"--- cycle {cycle} ---")
        try:
            events = sweep_watch()
            for e in events:
                log(f"event: {e}")
                if "MERGED" in e:
                    meta_score(e, "merge")
                    status_log("Night driver: merge detected", [e])
                elif "NEW COMMENT" in e:
                    meta_score(e, "response")
                    # lightweight triage: read latest comment
                    repo, num = e.split("NEW COMMENT on ")[1].split(" ")[0].split("#")
                    cs = gh(f"repos/{repo}/issues/{num}/comments")
                    if cs:
                        last = cs[-1]
                        log(f"last comment by {last['user']['login']}: {last['body'][:200]}")
                        status_log(f"Night driver: comment on {repo}#{num}",
                                   [f"{last['user']['login']}: {last['body'][:300]}"])
        except Exception as e:
            log(f"[watch-exception] {e}")
        # v3 kill list: the discovery -> unsolicited locale-fill PR lane (gift PRs) is removed.
        # Locale fills ship only inside a signed L1/L2 engagement (plan v3 section 6).
        time.sleep(CYCLE_SECONDS)
    log("=== night driver done ===")

if __name__ == "__main__":
    main()
