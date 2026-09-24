import sqlite3
db=sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
db.row_factory=sqlite3.Row
print('=== contributions (not closed) ===')
for r in db.execute("SELECT id,ts,repo,issue,pr,category,score,status,pr_url FROM contributions WHERE status NOT IN ('closed','merged','superseded') ORDER BY id"):
    print(f"  [{r['status']}] {r['repo']}#{r['issue']} pr={r['pr']} score={r['score']} :: {(r['pr_url'] or '')}")
print('=== runs (recent 10) ===')
for r in db.execute("SELECT id,ts,layer,discovered,verified,perfect,best_score,best_repo FROM runs ORDER BY id DESC LIMIT 10"):
    print(f"  {r['id']} {r['ts']} {r['layer']} dis={r['discovered']} ver={r['verified']} perf={r['perfect']} best={r['best_score']} @ {r['best_repo']}")
print('=== kpi ===')
for r in db.execute("SELECT * FROM kpi ORDER BY rowid DESC LIMIT 6"):
    print("  ", dict(r))