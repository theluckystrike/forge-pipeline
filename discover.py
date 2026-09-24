#!/usr/bin/env python3
"""WhiteHERO v3 stage 1: Discover (plan section 7, Phase 1 step 1.1).

gh search repos per language (stars 200..20000, updated within 90 d of a pinned date),
plus the locale-study seed (seed/locale_targets.json) and the 17 English-only flagships
(plan section 5 L2). Inserts into targets(org, repo, lang, stars, discovered_at),
deduped by UNIQUE(org, repo) with INSERT OR IGNORE. stdlib + gh only.

Usage: python3 discover.py [--dry-run]
"""
import datetime, json, os, subprocess, sqlite3, sys, time

PIPE = os.path.expanduser("~/oss-pipeline")
DB = os.path.join(PIPE, "state/kpi.db")
DATE_FILE = os.path.join(PIPE, "state/discover-date.txt")
QLOG = os.path.join(PIPE, "state/discover-queries.log")
SEED = os.path.join(PIPE, "seed/locale_targets.json")
FLAGSHIP_FILE = os.path.join(PIPE, "state/flagships.json")
LANGS = ["TypeScript", "Python", "Go", "Rust", "Java", "C#"]
FLAGSHIPS = ["n8n", "Novu", "PostHog", "Supabase", "Langfuse", "Flowise", "Budibase", "Appsmith",
             "Dub", "Windmill", "Dokploy", "Plausible", "Zed", "Warp", "Prefect", "MindsDB", "Wazuh"]
# expected repo-name token per flagship, used to reject a wrong top hit from gh search
FLAG_HINT = {"Plausible": "analytics", "Warp": "warp", "Dub": "dub", "Zed": "zed"}

def log(msg):
    with open(QLOG, "a") as f:
        f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')}\t{msg}\n")

def rate():
    r = subprocess.run(["gh", "api", "rate_limit", "--jq",
                        ".resources | {core:.core.remaining, search:.search.remaining, graphql:.graphql.remaining, sreset:.search.reset}"],
                       capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)

def wait_search(need):
    rl = rate()
    if rl["search"] < need:
        s = max(1, rl["sreset"] - int(time.time()) + 2)
        print(f"  search remaining {rl['search']} < {need}; sleeping {s}s", flush=True)
        time.sleep(s)

def gh_json(args, tries=4):
    delay = 20
    for t in range(tries):
        r = subprocess.run(args, capture_output=True, text=True, timeout=180)
        if r.returncode == 0:
            return json.loads(r.stdout)
        err = r.stderr.strip()[:300]
        print(f"  gh error (try {t+1}): {err}", flush=True)
        log(f"ERROR\t{' '.join(args)}\t{err}")
        if t < tries - 1:
            time.sleep(delay); delay *= 2
    raise SystemExit("gh failed after backoff 20/40/80 s: " + " ".join(args))

def pinned_date():
    if os.path.exists(DATE_FILE):
        return open(DATE_FILE).read().strip()
    d = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
    with open(DATE_FILE, "w") as f:
        f.write(d + "\n")
    return d

def main():
    dry = "--dry-run" in sys.argv
    date = pinned_date()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    rows = {}  # (org, repo) -> (lang, stars, source)
    search_calls = 0
    for lang in LANGS:
        args = ["gh", "search", "repos", "--language", lang, "--stars", "200..20000",
                "--updated", f">{date}", "--sort", "stars", "--limit", "200",
                "--json", "fullName,stargazersCount,owner,pushedAt,description,homepage"]
        wait_search(3)
        log("QUERY\t" + " ".join(a if " " not in a and ">" not in a else repr(a) for a in args))
        res = gh_json(args); search_calls += 2
        log(f"RESULT\t{lang}\t{len(res)} repos")
        print(f"{lang}: {len(res)} repos", flush=True)
        for x in res:
            org, repo = x["fullName"].split("/", 1)
            rows.setdefault((org, repo), (lang, x["stargazersCount"], "search:" + lang))
        time.sleep(2.5)
    # seed: locale study rows (all rows kept; lane selection takes the top 20)
    seed = json.load(open(SEED))["rows"]
    for r in seed:
        org, repo = r[0].split("/", 1)
        rows.setdefault((org, repo), (None, r[1], "seed:locale"))
    # flagships: resolve with gh search, top by stars whose name matches
    flag_map = json.load(open(FLAGSHIP_FILE)) if os.path.exists(FLAGSHIP_FILE) else {}
    for name in FLAGSHIPS:
        if name in flag_map:
            fn, st, lg = flag_map[name]["fullName"], flag_map[name]["stars"], flag_map[name].get("lang")
        else:
            wait_search(2)
            args = ["gh", "search", "repos", name, "--sort", "stars", "--limit", "5",
                    "--json", "fullName,stargazersCount,language"]
            log("QUERY\t" + " ".join(args))
            res = gh_json(args); search_calls += 1
            hint = FLAG_HINT.get(name, name).lower()
            pick = next((x for x in res if x["fullName"].split("/")[1].lower() == hint), None) or \
                   next((x for x in res if hint in x["fullName"].lower()), None) or res[0]
            fn, st, lg = pick["fullName"], pick["stargazersCount"], pick.get("language")
            flag_map[name] = {"fullName": fn, "stars": st, "lang": lg,
                              "candidates": [x["fullName"] for x in res]}
            log(f"FLAGSHIP\t{name}\t{fn}\t{st}\tcandidates={[x['fullName'] for x in res]}")
            time.sleep(2.5)
        org, repo = fn.split("/", 1)
        rows.setdefault((org, repo), (lg, st, "flagship:" + name))
        print(f"flagship {name} -> {fn} ({st})", flush=True)
    with open(FLAGSHIP_FILE, "w") as f:
        json.dump(flag_map, f, indent=1)
    print(f"candidate rows: {len(rows)}; search calls ~{search_calls}")
    if dry:
        return
    con = sqlite3.connect(DB, timeout=30)
    before = con.execute("select count(*) from targets").fetchone()[0]
    for (org, repo), (lang, stars, src) in rows.items():
        con.execute("insert or ignore into targets(org, repo, lang, stars, discovered_at) values(?,?,?,?,?)",
                    (org, repo, lang, stars, now))
    after = con.execute("select count(*) from targets").fetchone()[0]
    dup = con.execute("select count(*) from (select lower(org), lower(repo), count(*) c from targets group by 1,2 having c>1)").fetchone()[0]
    qstr = f'gh search repos --language <lang> --stars 200..20000 --updated ">{date}" --sort stars --limit 200 (langs {",".join(LANGS)}) + seed/locale_targets.json ({len(seed)}) + 17 flagships'
    con.execute("insert into runs(ts, layer, discovered, verified, notes) values(?,?,?,?,?)",
                (now, "v3-discover", after - before, after, f"date pinned {date}; query: {qstr}; dup(org,repo)={dup}"))
    con.commit()
    log(f"INSERTED\t{after-before} new; targets now {after}; dup={dup}")
    print(f"inserted {after-before}; targets now {after}; case-insensitive dup groups={dup}")

if __name__ == "__main__":
    main()
