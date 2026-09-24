import sqlite3, datetime
db=sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
ts=datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
notes=("W29 cron. 0 new merges 0 new feedback. Responded to stellar-docs Copilot finding "
       "(removed holds-two-sides rationale, reply posted). Widened probe surfaced 11 scoring-100 "
       "candidates but ALL contested (open covering PR, maintainer duplicate warning, or claim "
       "comment). apisix 13395/10893 covering PRs closed-unmerged but maintainer said close others "
       "duplicate. NVIDIA 16 has 2 open PRs. numba 2598 already merged. Nothing ships. "
       "Exact-100 bottleneck confirmed structural not discovery.")
db.execute("INSERT INTO runs (ts,layer,discovered,verified,perfect,best_score,best_repo,notes) "
           "VALUES (?,?,?,?,?,?,?,?)",
           (ts,'full-sprint-w29',29,4,0,100,'apache/apisix',notes))
db.commit()
# read back
db.row_factory=sqlite3.Row
r=db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT 1").fetchone()
print("INSERTED run id", r['id'])
print("  ts", r['ts'], "| layer", r['layer'])
print("  discovered", r['discovered'], "verified", r['verified'], "perfect", r['perfect'])
print("  best_score", r['best_score'], "best_repo", r['best_repo'])
print("  notes", r['notes'][:120], "...")