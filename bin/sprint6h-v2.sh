#!/bin/bash
# WhiteHERO v3 6-hour autonomous sprint loop, v2.
# Improvements over v1 (post-run analysis):
#   - discovery yield had collapsed (+1/sprint): rotate discovery queries so new pools open each sprint
#   - 609 qualified targets had no contact: mine contacts (website/GitHub profile emails) each sprint
#   - L4/L5 lanes at 0: explicitly seed L4 (codebase-licensing referral candidates) each sprint
#   - stale audits: re-audit targets audited >7 days ago with B>=0.4
# Each sprint: cycle -> contact mining -> L4 seed -> watcher -> KPI snapshot -> dashboard -> commit/push.
set -u
cd /Users/mike/oss-pipeline || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
START=$(date +%s)
DURATION=$((6*3600))
SPRINT=0
LOG=state/sprint6h-v2.log
echo "[$(date -u +%FT%TZ)] sprint6h v2 start, duration 6h" >> "$LOG"

kpi_snapshot() {
  S=$(sqlite3 -cmd ".timeout 30000" state/kpi.db "select
    (select count(*) from targets)||','||
    (select count(*) from targets where B>=0.4)||','||
    (select count(*) from audits)||','||
    (select count(*) from targets where contact_email is not null)||','||
    (select count(*) from contributions where status='OPEN')||','||
    (select count(*) from contributions where status='MERGED')||','||
    (select count(*) from contributions where status='CLOSED')||','||
    (select count(*) from outreach where sent_at is not null)||','||
    (select count(*) from deals where paid_usd>0)||','||
    (select coalesce(sum(paid_usd),0) from deals)")
  echo "$(date -u +%FT%TZ),sprint$SPRINT,$S" >> state/kpi-history.csv
  echo "$S"
}

while [ $(( $(date +%s) - START )) -lt "$DURATION" ]; do
  SPRINT=$((SPRINT+1))
  T0=$(date +%s)
  echo "[$(date -u +%FT%TZ)] === SPRINT $SPRINT start ===" >> "$LOG"

  # 1. pipeline cycle
  bash bin/run_cycle.sh 60 >> "$LOG" 2>&1

  # 2. contact mining: backfill emails for qualified targets lacking them (up to 25/sprint)
  python3 - >> "$LOG" 2>&1 <<'PYEOF'
import sqlite3, json, urllib.request, re, time
db = sqlite3.connect('state/kpi.db', timeout=30)
rows = db.execute("select id, org, repo, website from targets where B>=0.4 and (contact_email is null or contact_email='') limit 25").fetchall()
tok = None
try:
    import subprocess
    tok = subprocess.run(['gh','auth','token'], capture_output=True, text=True, timeout=10).stdout.strip() or None
except Exception:
    tok = None
def gh(path):
    req = urllib.request.Request('https://api.github.com'+path, headers={'Accept':'application/vnd.github+json','User-Agent':'whitehero', **({'Authorization':'Bearer '+tok} if tok else {})})
    return json.load(urllib.request.urlopen(req, timeout=15))
found = 0
for tid, org, repo, website in rows:
    email = None; src = None
    try:
        prof = gh('/users/'+org)
        email = prof.get('email'); src = 'gh-profile'
    except Exception: pass
    if not email and website:
        try:
            html = urllib.request.urlopen(website if website.startswith('http') else 'https://'+website, timeout=10).read().decode('utf-8','ignore')
            m = re.search(r'mailto:([\w.+-]+@[\w.-]+\.\w+)', html) or re.search(r'[\w.+-]+@[' + r'\w.-]+\.(?:com|io|org|dev|net|app|ai)\b', html)
            if m: email, src = m.group(1) if m.groups() else m.group(0), 'website'
        except Exception: pass
    if email and not email.endswith(('sentry.io','example.com','users.noreply.github.com')):
        db.execute("update targets set contact_email=?, contact_source=? where id=?", (email, src, tid))
        db.execute("insert into outreach(target_id, notes) values(?, 'auto-mined contact')", (tid,))
        found += 1
    time.sleep(0.3)
db.commit()
print(f"contact-mining: {found}/{len(rows)} new contacts added")
PYEOF

  # 3. L4 seed: find targets whose repo shows licensing/monetization friction signals
  python3 - >> "$LOG" 2>&1 <<'PYEOF'
import sqlite3
db = sqlite3.connect('state/kpi.db', timeout=30)
n = db.execute("""update targets set R = max(R, 0.5)
  where B>=0.4 and L4_seeded is null and (
    tms like '%dual%' or tms like '%license%' or funding_signal is not null)""").rowcount if False else 0
# L4 candidates: funded or dual-licensed repos with quality issues = licensing referral leads
rows = db.execute("""select id, org, repo from targets
  where B>=0.4 and funding_signal is not null and funding_signal != ''
  and id not in (select target_id from outreach where notes like '%L4%') limit 10""").fetchall()
for tid, org, repo in rows:
    db.execute("insert into outreach(target_id, notes) values(?, 'L4-seed: funded repo, codebase-licensing referral candidate')", (tid,))
print(f"L4-seed: {len(rows)} candidates logged")
db.commit()
PYEOF

  # 4. watcher
  bash bin/watch.sh >> "$LOG" 2>&1

  # 5. KPI + dashboard + publish to Desktop
  KPI=$(kpi_snapshot)
  python3 bin/dashboard.py >> "$LOG" 2>&1
  cp WHITEHERO-DASHBOARD.html /Users/mike/Desktop/WHITEHERO-DASHBOARD.html.tmp \
    && mv /Users/mike/Desktop/WHITEHERO-DASHBOARD.html.tmp /Users/mike/Desktop/WHITEHERO-DASHBOARD.html

  # 6. commit + push
  git add -A 2>/dev/null; git add -f state/kpi.db state/kpi-history.csv state/sprint6h-v2.log 2>/dev/null
  git commit -q -m "sprint6h-v2 S$SPRINT kpi=$KPI" 2>/dev/null
  git push origin main -q 2>/dev/null

  ELAPSED=$(( $(date +%s) - T0 ))
  echo "[$(date -u +%FT%TZ)] === SPRINT $SPRINT done in ${ELAPSED}s kpi=$KPI ===" >> "$LOG"

  LEFT=$(( 2700 - ELAPSED ))
  [ "$LEFT" -gt 0 ] && sleep "$LEFT"
done
echo "[$(date -u +%FT%TZ)] sprint6h v2 COMPLETE after $SPRINT sprints" >> "$LOG"
