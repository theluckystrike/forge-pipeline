import sqlite3
db = sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
c = db.cursor()
print('=== CONTRIBUTIONS ===')
for r in c.execute("SELECT id, ts, repo, issue, pr, category, score, status, pr_url FROM contributions ORDER BY id"):
    print(r)
print('=== RUNS (last 10) ===')
for r in c.execute("SELECT id, ts, layer, discovered, verified, perfect, best_score, best_repo FROM runs ORDER BY id DESC LIMIT 10"):
    print(r)
print('=== KPI ===')
for r in c.execute("SELECT * FROM kpi"):
    print(r)