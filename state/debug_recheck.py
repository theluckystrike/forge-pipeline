import sqlite3
db=sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
db.row_factory=sqlite3.Row
rows=[dict(r) for r in db.execute("SELECT id,repo,issue,pr,status,pr_url FROM contributions WHERE status IN ('open','in_progress')")]
print("open/in_progress rows:", len(rows))
for r in rows[:3]:
    print("sample:", r)
# distinct statuses
print("statuses:", [dict(r) for r in db.execute("SELECT status, count(*) c FROM contributions GROUP BY status")])