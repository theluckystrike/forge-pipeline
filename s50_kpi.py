import sqlite3
db=sqlite3.connect('/Users/mike/Desktop/oss-contrib-pipeline/kpi.db')
cur=db.cursor()
tot=cur.execute("select count(*) from contributions").fetchone()[0]
merged=cur.execute("select count(*) from contributions where upper(status)='MERGED'").fetchone()[0]
opn=cur.execute("select count(*) from contributions where upper(status)='OPEN'").fetchone()[0]
md=f"""# FORGE KPI (2026-09-29)

- Contributions total: {tot}
- Merged: {merged}
- Open: {opn}
- Latest: S48 arkhamdb-json-data PR #1806 (de core_2026+and, 36 cards, closes #1805)
- S46 PI-Desktop PR #1180 MERGED 09-28 by vastsa (maintainer merge milestone)
- S49 WiVRn PR #1136 CI repaired (26 de strings for new settings)
- S50 in progress: Children of Blood (cob) full de translation, 119 cards
- Rating: 96/100 (merge milestone claimed: PI-Desktop #1180)
"""
open('/Users/mike/oss-pipeline/KPI.md','w').write(md)
open('/Users/mike/Desktop/oss-contrib-pipeline/KPI.md','w').write(md)
print('KPI.md written',tot,merged,opn)
