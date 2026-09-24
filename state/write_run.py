import sqlite3
from datetime import datetime
con=sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db'); cur=con.cursor()
ts=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
# runs row for this full sprint
cur.execute(
  "INSERT INTO runs(ts,layer,discovered,verified,perfect,best_score,best_repo,notes) VALUES(?,?,?,?,?,?,?,?)",
  (ts,'full-sprint-w28',25,4,0,97,'marqo-ai/marqo',
   'W28 cron. 0 new merges 0 new feedback. Rubric bug found raw sum 105 not 100 blocks genuine perfects. Clamp to 100 plus documentation label adds to risk both fixed in pipeline.py. Widened discovery prototyped. Top genuine 97 under 100 gate. Nothing shipped dry run.'))
con.commit()
print('runs row added id', cur.lastrowid)
# display counts
for r in cur.execute("SELECT status,count(*) FROM contributions GROUP BY status"):
    print(r)
