import sqlite3, datetime
db=sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
ts=datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
db.execute("""INSERT INTO contributions (id,ts,repo,issue,pr,category,score,status,pr_url,notes)
VALUES (?,?,?,?,?,?,?,?,?,?)""", (
    52, ts, 'reservoirpy/reservoirpy', 218, 249, 'docs', 100, 'OPEN',
    'https://github.com/reservoirpy/reservoirpy/pull/249',
    'reset parameter tutorial notebook (docs/source/user_guide/reset.ipynb) + toctree entry; verified runs (MSE no-reset 1.66e-08 vs reset 3.78e-06); uncontested 0-comment issue; diff 141+/1-'
))
db.commit()
# verify
db.row_factory=sqlite3.Row
r=db.execute("SELECT * FROM contributions WHERE id=52").fetchone()
print("INSERTED:", dict(r))
