import sqlite3
con = sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
cur = con.cursor()
print('=== MKPI (key metrics) ===')
for r in cur.execute("SELECT * FROM kpi"):
    print(r)
print()
print('=== ALL OPEN CONTRIBUTIONS ===')
for r in cur.execute("SELECT id,repo,issue,pr,status,pr_url FROM contributions WHERE status='OPEN' ORDER BY id"):
    print(r)
print()
print('=== RUNS count by layer ===')
for r in cur.execute("SELECT layer, COUNT(*) FROM runs GROUP BY layer"):
    print(r)
