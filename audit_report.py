#!/usr/bin/env python3
"""audit_report.py: run audit_drift + audit_locale on a repo, write the one-page report, the evidence
dir, gate both (check_evidence + humanize_scan --strict), and insert an audits row in state/kpi.db.

Usage:
  python3 audit_report.py owner/repo [owner/repo ...]
  python3 audit_report.py --from-db 80 [--seed-locale 20] [--workers 4] [--skip-done]

Outputs: reports/<org>__<repo>.md and reports/<org>__<repo>/evidence/
DB: audits(target_id, stale_claims, failing_examples, locale_gap_keys, worst_locale, worst_pct,
    report_path, evidence_dir, created_at). stale_claims = version + count + engine findings;
    failing_examples = dead external links + missing relative link targets. worst_* is the worst
    tier-1 locale when any tier-1 locale exists, else the worst measured locale.
"""
import json, os, re, sqlite3, subprocess, sys, time, traceback, urllib.parse
from concurrent.futures import ThreadPoolExecutor
PIPE = os.path.expanduser("~/oss-pipeline")
sys.path.insert(0, PIPE)
import audit_locale as AL
import audit_drift as AD
import check_evidence as CE

DB = os.path.join(PIPE, "state", "kpi.db")
REPORTS = os.path.join(PIPE, "reports")
HUMANIZE = os.path.join(PIPE, "tools", "humanize_scan.py")
RUNLOG = os.path.join(PIPE, "state", "audit_run.log")

def log(msg):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(RUNLOG, "a") as f:
        f.write(line + "\n")

def code(s, n=150):
    """Inline code span safe for tables and the humanize scanner."""
    s = str(s).replace('`', "'").replace('|', '/').replace('\t', ' ').strip()
    s = re.sub(r'\s+', ' ', s)
    if len(s) > n:
        cut = s.rfind(' ', 0, n)
        s = s[:cut if cut > 40 else n].rstrip() + " ..."
    return f"`{s}`" if s else "` `"

def commit_sha(repo, branch):
    try:
        r = subprocess.run(["git", "ls-remote", f"https://github.com/{repo}.git", f"refs/heads/{branch}"],
                           capture_output=True, text=True, timeout=25)
        m = re.match(r'^([0-9a-f]{40})', r.stdout)
        return m.group(1) if m else None
    except Exception:
        return None

def target_row(org, repo):
    c = sqlite3.connect(DB, timeout=30)
    r = c.execute("select id, B, R, L, stars from targets where org=? and repo=?", (org, repo)).fetchone()
    c.close()
    return {"target_id": r[0], "B": r[1], "R": r[2], "L": r[3], "stars": r[4]} if r else {"target_id": None}

def pct(v):
    return f"{v:.1f}%"

def write_report(repo, meta, sha, loc, dr, summary, path):
    org, name = repo.split('/')
    day = summary["measured_at"][:10]
    F = dr["findings"]
    stale = [f for f in F if f["check"] in ("c_version_drift", "d_count_claim", "e_engine_claim")]
    broken = [f for f in F if f["check"] in ("a_dead_link", "b_missing_relative_target")]
    cc = dr["counts"]
    L = []
    full = meta.get("full_name") or repo
    L.append(f"# Docs drift and locale audit of {code(full)}")
    L.append("")
    if full.lower() != repo.lower():
        L.append(f"The target list names this repository {code(repo)}. GitHub now redirects that name to {code(full)}.")
        L.append("")
    L.append(f"Measured on {day} against commit {code(sha[:12] if sha else meta['default_branch'])} of the {code(meta['default_branch'])} branch. "
             "The checks are deterministic and cover the README and top-level `docs/*.md` files only. "
             "Each figure below can be traced to a command or file in the `evidence/` folder next to this report.")
    L.append("")
    L.append("## Summary")
    L.append("")
    L.append("| Measure | Result |")
    L.append("|---|---|")
    L.append(f"| Stale README claims (pinned versions, counts, engine minimums) | {len(stale)} |")
    L.append(f"| Broken links (dead external plus missing relative targets) | {len(broken)} |")
    L.append(f"| External links checked | {cc['links_checked']} |")
    L.append(f"| Relative links checked | {cc['relative_links_checked']} |")
    if loc.get("locale_group") and loc.get("en_keys"):
        wt = loc.get("worst_tier1")
        if wt:
            L.append(f"| Worst tier-1 locale | {code(wt['locale'])} {pct(wt['gap_pct'])} untranslated ({wt['gap_keys']} of {loc['en_keys']} keys) |")
        w = loc.get("worst")
        if w and (not wt or w["locale"] != wt["locale"]):
            L.append(f"| Worst locale overall | {code(w['locale'])} {pct(w['gap_pct'])} ({w['gap_keys']} keys) |")
        L.append(f"| Untranslated keys, all measured locales | {loc.get('total_gap_keys', 0)} across {loc.get('n_locales_measured', 0)} locales |")
    else:
        L.append("| Locale tree | none found |")
    L.append(f"| Measured defects (stale claims plus broken links) | {summary['defects']} |")
    L.append("")
    L.append("## Stale claims")
    L.append("")
    if stale:
        L.append("| Line | README text | Claimed | Measured |")
        L.append("|---|---|---|---|")
        for f in stale[:12]:
            L.append(f"| {f['line_no']} | {code(f['line'], 110)} | {code(f['claimed'], 60)} | {code(f['measured'], 90)} |")
        if len(stale) > 12:
            L.append("")
            L.append(f"The table shows 12 of {len(stale)} stale claims. The rest are in `evidence/drift.json`.")
        L.append("")
        L.append("How each value was measured is stored per finding in `evidence/drift.json` (field `measured_by`).")
    else:
        vc = len(dr.get("version_claims", [])); kc = len(dr.get("count_claims", [])); ec = len(dr.get("engine_claims", []))
        L.append(f"No README claim failed a check. Claims compared against the tree or manifests: {vc} pinned install versions, "
                 f"{kc} count claims, {ec} engine minimums.")
    L.append("")
    L.append("## Broken links")
    L.append("")
    if broken:
        L.append("| File and line | Link | Result |")
        L.append("|---|---|---|")
        for f in broken[:15]:
            L.append(f"| {code(f['file'] + ':' + str(f['line_no']), 60)} | {code(f['claimed'], 90)} | {code(f['measured'], 70)} |")
        if len(broken) > 15:
            L.append("")
            L.append(f"The table shows 15 of {len(broken)} broken links. The rest are in `evidence/drift.json`.")
        L.append("")
        L.append("A dead link is one that answered 404 or 410, or whose host did not resolve, on a HEAD request, a GET, and a second GET a few seconds later "
                 "(`curl -L` with an 8 second timeout). Timeouts, 403 and 5xx answers are not counted. "
                 "A missing relative target is a link path that does not exist in the recursive git tree of this commit.")
    else:
        rel = (f"and all {cc['relative_links_checked']} relative links resolve to files or folders in the tree."
               if cc['relative_links_checked'] else "and the documents contain no relative links.")
        L.append(f"None of the {cc['links_checked']} external links returned 404, 410 or a DNS failure, " + rel)
    L.append("")
    L.append("## Locale parity")
    L.append("")
    if loc.get("locale_group") and loc.get("en_keys"):
        nsf = len(loc["src_files"])
        srcs = code(loc["src_files"][0]) if nsf == 1 else f"({nsf} files, starting with {code(loc['src_files'][0])})"
        L.append(f"The English source {srcs} holds {loc['en_keys']} keys. {loc['n_locales_measured']} locales were compared key by key"
                 + (" (a seeded sample plus every tier-1 locale)" if loc.get("sampled") else "")
                 + ". A key counts as untranslated when it is missing, empty, or byte-identical to the English value. "
                 "Identical values are not counted when the English text is shorter than 3 characters, a URL, a number or only placeholders.")
        L.append("")
        if loc.get("tier1"):
            L.append("| Tier-1 locale | File code | Untranslated | Missing | Same as English |")
            L.append("|---|---|---|---|---|")
            for t in AL.TIER1:
                v = loc["tier1"].get(t)
                if v:
                    L.append(f"| {t} | {code(v['locale'])} | {pct(v['gap_pct'])} ({v['gap_keys']} keys) | {v['missing']} | {v['identical']} |")
            L.append("")
        absent = loc.get("tier1_absent") or []
        if absent:
            L.append("No locale file exists for " + ", ".join(code(a) for a in absent) + ".")
            L.append("")
        w = loc.get("worst")
        if w:
            L.append(f"The weakest locale overall is {code(w['locale'])} at {pct(w['gap_pct'])} ({w['gap_keys']} keys). "
                     "The full key lists for the tier-1 locales and the weakest locale are in `evidence/locale_gap_keys.json`.")
    elif loc.get("english_only"):
        eo = loc["english_only"]
        langs = ", ".join(code(x) for x in eo["languages"])
        lead = "The UI strings are English-only. " if len(eo["languages"]) == 1 else ""
        L.append(f"{lead}{code(eo['src_files'][0])} holds {eo['en_keys']} English keys"
                 + (f" across {len(eo['src_files'])} files" if len(eo['src_files']) > 1 else "")
                 + f", and the locale folder holds these language codes only: {langs}. "
                 "With fewer than three languages the tree was not measured for parity.")
    else:
        L.append("No locale tree with at least three languages and an English source was found in the git tree, "
                 "so the product ships in one language or keeps its strings outside this repository.")
    L.append("")
    L.append("## Reproduce")
    L.append("")
    L.append("```")
    L.append(f"python3 audit_drift.py {repo}")
    L.append(f"python3 audit_locale.py {repo}")
    if loc.get("raw_url_example"):
        L.append(f"curl -sL {loc['raw_url_example']}")
    L.append("```")
    L.append("")
    L.append("Evidence files are `meta.json`, `drift.json`, `links.tsv`, `relative_links.tsv`, `locale.json`, `locale_gap_keys.json`, "
             "`readme.txt`, `manifests/` and `tree_paths.raw`.")
    L.append("")
    open(path, "w").write("\n".join(L))

def run_one(repo, extra=None):
    t0 = time.time()
    org, name = repo.split('/')
    slug = f"{org}__{name}"
    rpath = os.path.join(REPORTS, slug + ".md")
    evdir = os.path.join(REPORTS, slug, "evidence")
    os.makedirs(os.path.join(evdir, "manifests"), exist_ok=True)
    meta = AL.gh(f"repos/{repo}")
    if not meta:
        return {"repo": repo, "err": "repo meta not found"}
    if meta.get("full_name") and meta["full_name"].lower() != repo.lower():
        log(f"{repo} redirects to {meta['full_name']}")
    branch = meta["default_branch"]
    sha = commit_sha(meta.get("full_name", repo), branch)
    tree = AL.gh(f"repos/{repo}/git/trees/{sha or urllib.parse.quote(branch)}?recursive=1")
    if not tree:
        return {"repo": repo, "err": "tree not available"}
    ref = sha or branch
    loc = AL.audit(repo, meta=meta, tree=tree, ref=ref)
    dr = AD.audit(repo, meta=meta, tree=tree, locale_n=loc.get("n_locales_total"), ref=ref)
    F = dr["findings"]
    stale = sum(1 for f in F if f["check"] in ("c_version_drift", "d_count_claim", "e_engine_claim"))
    failing = sum(1 for f in F if f["check"] in ("a_dead_link", "b_missing_relative_target"))
    wt = loc.get("worst_tier1") or loc.get("worst")
    tr = target_row(org, name)
    summary = {"repo": repo, "full_name": meta.get("full_name"), "branch": branch, "commit": sha, "stars": meta.get("stargazers_count"),
               "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "target": tr, "selection": extra or {},
               "stale_claims": stale, "failing_examples": failing, "defects": stale + failing,
               "locale_gap_keys": loc.get("total_gap_keys") if loc.get("locale_group") else None,
               "worst_locale": wt["locale"] if wt else None, "worst_pct": wt["gap_pct"] if wt else None,
               "worst_locale_rule": "worst tier-1 locale if any tier-1 locale exists, else worst measured locale",
               "claims_checked": {"version": len(dr.get("version_claims", [])), "count": len(dr.get("count_claims", [])),
                                  "engine": len(dr.get("engine_claims", []))},
               "method": {"dead_link_rule": "dead = HTTP 404 or 410 or DNS failure (curl exit 6) on HEAD, then GET, then a GET re-check; "
                                            "curl -L --max-time 8; timeouts, 403, 429 and 5xx are not counted; max 60 unique links",
                          "identical_exempt": "identical to English is not a gap when the English value is under 3 chars, a URL, a number or placeholder-only",
                          "report_table_caps": {"stale_rows": 12, "link_rows": 15},
                          "count_claim_rule": "differs by more than 10 percent; N+ claims flagged only when the tree has under 90 percent of N"},
               "drift_counts": dr["counts"], "tree_files": len([t for t in tree["tree"] if t["type"] == "blob"]),
               "tree_truncated": tree.get("truncated", False),
               "commands": [f"gh api repos/{repo}", f"git ls-remote https://github.com/{repo}.git refs/heads/{branch}",
                            f"gh api 'repos/{repo}/git/trees/{ref}?recursive=1'", f"python3 audit_drift.py {repo}", f"python3 audit_locale.py {repo}"]}
    # evidence
    dj = {k: v for k, v in dr.items() if not k.startswith('_')}
    json.dump(dj, open(os.path.join(evdir, "drift.json"), "w"), indent=1, ensure_ascii=False)
    with open(os.path.join(evdir, "links.tsv"), "w") as f:
        f.write("file\tline_no\turl\thead_code\thead_exit\tget_code\tget_exit\trecheck_code\trecheck_exit\tdead\treason\n")
        for r in dr["links_checked"]:
            f.write("\t".join(str(r.get(k, "")) for k in ("file", "line_no", "url", "head_code", "head_exit", "get_code", "get_exit",
                                                           "recheck_code", "recheck_exit", "dead", "reason")) + "\n")
    with open(os.path.join(evdir, "relative_links.tsv"), "w") as f:
        f.write("file\tline_no\tlink\tresolved\texists\n")
        for r in dr["relative_checked"]:
            f.write(f"{r['file']}\t{r['line_no']}\t{r['link']}\t{r['resolved']}\t{r['exists']}\n")
    for p, t in dr.get("_docs", []):
        fn = "readme.txt" if p == dr.get("readme_path") else "doc__" + p.replace('/', '__') + ".txt"
        open(os.path.join(evdir, fn), "w").write(t)
    for p, t in dr.get("_manifest_texts", {}).items():
        open(os.path.join(evdir, "manifests", p.replace('/', '__') + ".txt"), "w").write(t)
    lj = {k: v for k, v in loc.items() if k != "gap_key_lists"}
    json.dump(lj, open(os.path.join(evdir, "locale.json"), "w"), indent=1, ensure_ascii=False)
    keep = set(v["locale"] for v in (loc.get("tier1") or {}).values())
    if loc.get("worst"):
        keep.add(loc["worst"]["locale"])
    json.dump({c: v for c, v in (loc.get("gap_key_lists") or {}).items() if c in keep},
              open(os.path.join(evdir, "locale_gap_keys.json"), "w"), indent=1, ensure_ascii=False)
    with open(os.path.join(evdir, "tree_paths.raw"), "w") as f:
        f.write("\n".join(t["path"] for t in tree["tree"]))
    summary["commit_short"] = sha[:12] if sha else None
    summary["n_src_files"] = len(loc.get("src_files") or [])
    json.dump(summary, open(os.path.join(evdir, "meta.json"), "w"), indent=1, ensure_ascii=False)
    run = {"seconds": round(time.time() - t0, 1)}
    write_report(repo, meta, sha, loc, dr, summary, rpath)
    # gates
    toks, missing = CE.check(rpath, evdir)
    h = subprocess.run([sys.executable, HUMANIZE, "--strict", rpath], capture_output=True, text=True)
    run["evidence_gate"] = "pass" if not missing else "fail: " + " ".join(missing[:20])
    run["humanize_gate"] = "pass" if h.returncode == 0 else "fail: " + h.stdout.strip().splitlines()[-1][:200]
    if not missing and h.returncode == 0:
        c = sqlite3.connect(DB, timeout=30)
        c.execute("delete from audits where report_path=?", (rpath,))
        c.execute("insert into audits(target_id, stale_claims, failing_examples, locale_gap_keys, worst_locale, worst_pct, report_path, evidence_dir, created_at) "
                  "values(?,?,?,?,?,?,?,?,?)", (tr.get("target_id"), stale, failing, summary["locale_gap_keys"], summary["worst_locale"],
                                               summary["worst_pct"], rpath, evdir, summary["measured_at"]))
        c.commit(); c.close()
        run["db"] = "inserted"
    else:
        run["db"] = "skipped (gate failed)"
        if h.returncode:
            open(os.path.join(REPORTS, slug, "humanize.out"), "w").write(h.stdout)
    # gate results live beside the evidence dir, never inside it, so they cannot satisfy the evidence check
    json.dump(run, open(os.path.join(REPORTS, slug, "gates.json"), "w"), indent=1)
    log(f"{repo} stale={stale} failing={failing} gap={summary['locale_gap_keys']} worst={summary['worst_locale']} {summary['worst_pct']} "
        f"evidence={run['evidence_gate'][:40]} humanize={run['humanize_gate'][:60]} db={run['db']} {run['seconds']}s")
    summary.update(run)
    return summary

def select_targets(n_db, n_seed):
    c = sqlite3.connect(DB, timeout=30)
    rows = c.execute("select id, org, repo, B, L from targets where B >= 0.4 order by B desc, L desc limit ?", (n_db,)).fetchall()
    total = c.execute("select count(*), sum(B>=0.4) from targets").fetchone()
    c.close()
    sel = [(f"{o}/{r}", {"source": "targets", "target_id": i, "B": b, "L": l}) for i, o, r, b, l in rows]
    have = {s[0].lower() for s in sel}
    seed = json.load(open(os.path.join(PIPE, "seed", "locale_targets.json")))["rows"][:n_seed]
    for row in seed:
        if row[0].lower() not in have:
            sel.append((row[0], {"source": "seed/locale_targets.json", "seed_rank": seed.index(row) + 1}))
            have.add(row[0].lower())
    return sel, total

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(2)
    workers = int(a[a.index("--workers") + 1]) if "--workers" in a else 4
    if "--from-db" in a:
        n = int(a[a.index("--from-db") + 1])
        ns = int(a[a.index("--seed-locale") + 1]) if "--seed-locale" in a else 0
        sel, total = select_targets(n, ns)
        snap = os.path.join(PIPE, "state", f"audit_selection_{time.strftime('%Y%m%dT%H%M%S')}.json")
        json.dump({"query": "select id, org, repo, B, L from targets where B >= 0.4 order by B desc, L desc limit %d" % n,
                   "targets_total_and_B_ge_0.4": total, "seed_locale_top": ns, "selection": sel}, open(snap, "w"), indent=1)
        log(f"selection: {len(sel)} repos ({total}), snapshot {snap}")
    else:
        sel = [(r, {"source": "cli"}) for r in a if '/' in r and not r.startswith('-')]
    if "--skip-done" in a:
        c = sqlite3.connect(DB, timeout=30)
        done = {os.path.basename(p)[:-3] for (p,) in c.execute("select report_path from audits")}
        c.close()
        sel = [s for s in sel if s[0].replace('/', '__') not in done]
    def go(s):
        try:
            return run_one(s[0], s[1])
        except Exception as e:
            log(f"{s[0]} ERROR {e!r} {traceback.format_exc()[-400:]}")
            return {"repo": s[0], "err": repr(e)}
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(go, sel))
    ok = sum(1 for r in res if r.get("db") == "inserted")
    log(f"done: {ok}/{len(res)} inserted; REST calls logged total {AL._calls_used()}")

if __name__ == "__main__":
    main()
