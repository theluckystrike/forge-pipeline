#!/usr/bin/env python3
"""Regression test: an org listed in state/contacted.tsv never gets a draft (exampleorg case).
Runs build_outreach.py against a throwaway DB and outreach dir. Exit 0 = pass."""
import os, sqlite3, subprocess, sys, tempfile

PIPE = os.path.expanduser("~/oss-pipeline")
with tempfile.TemporaryDirectory() as d:
    dbp, out, ev = os.path.join(d, "t.db"), os.path.join(d, "out"), os.path.join(d, "ev")
    os.makedirs(os.path.join(out, "queue")); os.makedirs(ev)
    import json
    dead = [{"check": "a_dead_link", "file": "README.md", "line_no": 10 + i, "claimed": f"https://example.org/page{i}",
             "measured": "HTTP 404"} for i in range(3)]
    json.dump({"findings": dead, "counts": {"a_dead_link": 3, "links_checked": 40, "relative_links_checked": 5}},
              open(os.path.join(ev, "drift.json"), "w"))
    json.dump({}, open(os.path.join(ev, "locale.json"), "w"))
    rep = os.path.join(d, "r.md")
    open(rep, "w").write("| Broken links | 3 |\n| External links checked | 40 |\n| Relative links checked | 5 |\n"
                         + "".join(f"| README.md:{10 + i} | https://example.org/page{i} | HTTP 404 |\n" for i in range(3)))
    tsv = os.path.join(d, "contacted.tsv")
    open(tsv, "w").write("exampleorg\t2026-09-24\thello@example.com\tprior contact\n")
    schema = subprocess.run(["sqlite3", os.path.join(PIPE, "state", "kpi.db"), ".schema"], capture_output=True, text=True).stdout
    c = sqlite3.connect(dbp); c.executescript(schema)
    for tid, org, repo, mail in [(7, "exampleorg", "example", "hello@example.com"), (8, "acme", "widget", "hello@acme.io")]:
        c.execute("insert into targets(id,org,repo,owner_type,B,score,contact_email,contact_source,tms) values(?,?,?,?,?,?,?,?,?)",
                  (tid, org, repo, "Organization", 0.8, 0.9, mail, "https://example.com", ""))
        c.execute("insert into audits(target_id,stale_claims,failing_examples,locale_gap_keys,report_path,evidence_dir) values(?,0,3,NULL,?,?)",
                  (tid, rep, ev))
    c.commit()
    env = dict(os.environ, OUTREACH_DB=dbp, OUTREACH_DIR=out, OUTREACH_CONTACTED=tsv)
    print(subprocess.run([sys.executable, os.path.join(PIPE, "build_outreach.py")], env=env, capture_output=True, text=True, check=True).stdout)
    q = sorted(os.listdir(os.path.join(out, "queue")))
    rows = c.execute("select target_id from outreach").fetchall()
    g = subprocess.run([sys.executable, os.path.join(PIPE, "outreach_gate.py")], env=env, capture_output=True, text=True)
    print(g.stdout.splitlines()[1:4])
    ok = q == ["8-L1.txt"] and rows == [(8,)] and g.returncode == 0
    print("PASS" if ok else "FAIL", "queue:", q, "outreach rows:", rows)
    sys.exit(0 if ok else 1)
