import sqlite3
db = sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
cur = db.cursor()
print("=== contributions schema ===")
for r in cur.execute("PRAGMA table_info(contributions)"):
    print(r)
print("\n=== runs schema ===")
for r in cur.execute("PRAGMA table_info(runs)"):
    print(r)
print("\n=== recent runs ===")
try:
    for r in cur.execute("SELECT * FROM runs ORDER BY rowid DESC LIMIT 5"):
        print(r)
except Exception as e:
    print("runs query err:", e)
print("\n=== contribution status counts ===")
try:
    for r in cur.execute("SELECT status, COUNT(*) FROM contributions GROUP BY status"):
        print(r)
except Exception as e:
    print("counts err:", e)
db.close()