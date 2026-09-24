import sqlite3, datetime
db=sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
db.row_factory=sqlite3.Row
now=datetime.datetime.utcnow().isoformat()
# contributions_shipped counts OPEN+MERGED contributions
n=db.execute("SELECT COUNT(*) FROM contributions WHERE status IN ('OPEN','MERGED')").fetchone()[0]
db.execute("UPDATE kpi SET value=?, updated=? WHERE metric='contributions_shipped'", (str(n), now))
# commits_via_api increment by 2 (notebook + index.rst)
db.execute("UPDATE kpi SET value=?, updated=? WHERE metric='commits_via_api'", (str(44), now))
db.commit()
for r in db.execute("SELECT metric,value FROM kpi"):
    print(dict(r))
