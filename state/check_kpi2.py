import sqlite3
db=sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
db.row_factory=sqlite3.Row
print("=== last 5 runs ===")
for r in db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 5"):
    print(dict(r))
print("\n=== kpi table ===")
for r in db.execute("SELECT * FROM kpi"):
    print(dict(r))
print("\n=== contributions count by status ===")
for r in db.execute("SELECT status, COUNT(*) c FROM contributions GROUP BY status"):
    print(dict(r))