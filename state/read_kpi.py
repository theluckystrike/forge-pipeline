import sqlite3
con = sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
cur = con.cursor()
print('=== SCHEMA ===')
for r in cur.execute("SELECT sql FROM sqlite_master WHERE type='table'"):
    print(r[0])
    print('---')
print('=== RUNS (last 12) ===')
for r in cur.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 12'):
    print(r)
print()
print('=== KPI TABLE ===')
for r in cur.execute('SELECT * FROM kpi'):
    print(r)
print()
print('=== CONTRIBUTIONS counts ===')
for r in cur.execute("SELECT status, COUNT(*) FROM contributions GROUP BY status"):
    print(r)
