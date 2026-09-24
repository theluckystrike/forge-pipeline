import sqlite3
db = sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
c = db.cursor()
c.execute("UPDATE contributions SET status='MERGED', notes=notes || ' | merged 2026-09-21T18:54Z by samyak-commits (sha 73c1753)' WHERE id=12")
c.execute("UPDATE contributions SET status='MERGED', notes=notes || ' | merged 2026-09-21T17:56Z by chrisalunlloyd2-sudo (sha 1080949)' WHERE id=42")
db.commit()
# read back
for rid in (12,42):
    r = c.execute("SELECT id, repo, pr, status, notes FROM contributions WHERE id=?", (rid,)).fetchone()
    print(r)
print('MERGED count now:', c.execute("SELECT COUNT(*) FROM contributions WHERE status='MERGED'").fetchone()[0])
print('OPEN count now:', c.execute("SELECT COUNT(*) FROM contributions WHERE status='OPEN'").fetchone()[0])