import sqlite3
db=sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
db.row_factory=sqlite3.Row
print("=== last 3 contributions ===")
for r in db.execute("SELECT * FROM contributions ORDER BY id DESC LIMIT 3"):
    print(dict(r))
print("=== max id ===")
print(db.execute("SELECT MAX(id) FROM contributions").fetchone()[0])
