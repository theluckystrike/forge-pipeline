import sqlite3, datetime
db = sqlite3.connect('/Users/mike/Desktop/oss-contrib-pipeline/kpi.db')
cur = db.cursor()
now = datetime.datetime.utcnow().isoformat(timespec='seconds')
cur.execute("insert into contributions (ts,repo,issue,pr,category,score,status,pr_url,notes) values (?,?,?,?,?,?,?,?,?)",
 (now,'Kamalisk/arkhamdb-json-data',None,1806,'translation',100,'OPEN',
  'https://github.com/Kamalisk/arkhamdb-json-data/pull/1806',
  'S48b gap patch: sfk Ruins of Ib de text committed to de-core2026-and-gap (commit c703493); core 15 + and 5 text gaps confirmed already covered on PR branch; full EN parity verified 0 untranslated across all 3 packs'))
cur.execute("insert into runs (ts,layer,discovered,verified,perfect,best_score,best_repo,notes) values (?,?,?,?,?,?,?,?)",
 (now,'L5',1,1,1,100,'arkhamdb-json-data','S48b gap scan + sfk commit shipped'))
db.commit()
print('total',cur.execute("select count(*) from contributions").fetchone()[0],
      'merged',cur.execute("select count(*) from contributions where status='MERGED'").fetchone()[0],
      'open',cur.execute("select count(*) from contributions where status='OPEN'").fetchone()[0])
