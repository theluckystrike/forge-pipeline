import sqlite3
con = sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
cur = con.cursor()
print('=== TABLES ===')
for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(r)
print()
print('=== CONTRIBUTIONS ===')
cols = [d[0] for d in cur.execute('SELECT * FROM contributions LIMIT 1').description]
print('COLS:', cols)
for r in cur.execute('SELECT * FROM contributions ORDER BY id DESC LIMIT 60'):
    print(r)
print()
print('=== RUNS (last 8) ===')
for r in cur.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 8'):
    print(r)
