import sqlite3, datetime
db=sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
db.row_factory=sqlite3.Row
# update run 37 to reflect the shipped candidate
db.execute("""UPDATE runs SET best_repo=?, best_score=?, notes=? WHERE id=37""", (
    'reservoirpy/reservoirpy',
    100,
    'W29 cron. 0 new merges 0 new feedback. Responded to stellar-docs Copilot finding (removed holds-two-sides rationale, reply posted). Recalibrated 300-star rubric surfaced 100/100 candidates but all contested (apisix, NVIDIA, numba, libredb, nutshell) or already handled (react-simplikit#500 via own PR#519). SHIPPED reservoirpy#218 reset tutorial PR#249 (uncontested 0-comment, verified runs, diff 141+/1-).'
))
db.commit()
r=db.execute("SELECT id,ts,layer,discovered,verified,perfect,best_score,best_repo FROM runs WHERE id=37").fetchone()
print("UPDATED run 37:", dict(r))
