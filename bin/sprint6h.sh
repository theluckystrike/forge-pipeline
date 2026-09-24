#!/bin/bash
# WhiteHERO v3 6-hour autonomous sprint loop.
# Runs 8 sprints of ~45min each. Each sprint:
#   1. full pipeline cycle (discover, qualify, audit, drafts, gate)
#   2. new contribution work: ship a fix/PR where a qualified target + issue exists
#   3. watcher pass (PR status updates, red flags)
#   4. KPI snapshot -> state/kpi-history.csv, dashboard rebuild, STATUS.md sprint entry
#   5. commit + push everything
# Usage: bash bin/sprint6h.sh   (background; writes state/sprint6h.log)
set -u
cd /Users/mike/oss-pipeline || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
START=$(date +%s)
DURATION=$((6*3600))
SPRINT=0
LOG=state/sprint6h.log
echo "[$(date -u +%FT%TZ)] sprint6h start, duration 6h" >> "$LOG"

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

  # 1. pipeline cycle (discovers/qualifies/audits/drafts)
  bash bin/run_cycle.sh 60 >> "$LOG" 2>&1

  # 2. watcher pass on open PRs (status changes, red flags)
  bash bin/watch.sh >> "$LOG" 2>&1

  # 4. KPI snapshot + dashboard
  KPI=$(kpi_snapshot)
  python3 bin/dashboard.py >> "$LOG" 2>&1
  cp WHITEHERO-DASHBOARD.html /Users/mike/Desktop/WHITEHERO-DASHBOARD.html.tmp \
    && mv /Users/mike/Desktop/WHITEHERO-DASHBOARD.html.tmp /Users/mike/Desktop/WHITEHERO-DASHBOARD.html

  # 5. commit + push
  git add -A 2>/dev/null; git add -f state/kpi.db state/kpi-history.csv state/sprint6h.log 2>/dev/null
  git commit -q -m "sprint6h S$SPRINT kpi=$KPI" 2>/dev/null
  git push origin main -q 2>/dev/null

  ELAPSED=$(( $(date +%s) - T0 ))
  echo "[$(date -u +%FT%TZ)] === SPRINT $SPRINT done in ${ELAPSED}s kpi=$KPI ===" >> "$LOG"

  # sleep remainder up to 45min per sprint
  LEFT=$(( 2700 - ELAPSED ))
  [ "$LEFT" -gt 0 ] && sleep "$LEFT"
done
echo "[$(date -u +%FT%TZ)] sprint6h COMPLETE after $SPRINT sprints" >> "$LOG"
