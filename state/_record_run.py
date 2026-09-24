import sqlite3
from datetime import datetime
db = sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
cur = db.cursor()
ts = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
cur.execute("""INSERT INTO runs (ts, layer, discovered, verified, perfect, best_score, best_repo, notes)
VALUES (?,?,?,?,?,?,?,?)""", (
    ts, 'full-sprint-w31', 63, 7, 0, 100,
    'OWASP/cve-lite-cli#1000 (trap)',
    'W31 cron. Step1: 2 new merges (adlerqa/wardeniq#32, chrisalunlloyd2-sudo/mindpalace#81) flipped MERGED. Step2: 0 new actionable reviewer feedback on 6 tracked PRs. Step3: standard L1 found 2 perfect_100 (both false positives: cashubtc/nutshell#500 already-resolved trap, toss/react-simplikit#500 already covered by own PR#519). Widened discovery prototype (_wide_classify.py) added claim-chatter classification + docs-only axis; found hyphenated good-first-issue label bug (rubric checks spaces). Docs axis surfaced OWASP/cve-lite-cli#1000 SCORE=100 but maintainer-coached trap, serde-rs/serde#1500=97 (recency 28d), meilisearch/meilisearch-rust#800=92 (stale). Step4: NO genuine exact-100 candidate -> 0 ships (dry-run). Lesson: claim-chatter "I would like to work on this" = genuine claim not harmless chatter; exact-100 needs all-max components AND genuine uncontestedness, both rare.'
))
db.commit()
# verify
for r in cur.execute("SELECT rowid, ts, layer, discovered, perfect, best_repo FROM runs ORDER BY rowid DESC LIMIT 1"):
    print("inserted:", r)
print("total runs:", cur.execute("SELECT COUNT(*) FROM runs").fetchone()[0])
db.close()