#!/bin/bash
# Hourly auto-approve + armed send, runs alongside sprint6h-v2 for the 6h window.
# Auto-approves only drafts that pass outreach_gate clean, respects 8/day 40/week caps (enforced by send_outreach).
set -u
cd /Users/mike/oss-pipeline || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
LOG=state/auto-send.log
START=$(date +%s)
while [ $(( $(date +%s) - START )) -lt 21600 ]; do
  echo "[$(date -u +%FT%TZ)] auto-send cycle" >> "$LOG"
  # approve any clean queued drafts not yet in approved.txt
  python3 - >> "$LOG" 2>&1 <<'PYEOF'
import os, sqlite3, sys
sys.path.insert(0, '.')
import outreach_gate
q = 'outreach/queue'
appr_path = 'outreach/approved.txt'
appr = set()
if os.path.exists(appr_path):
    appr = {l.strip() for l in open(appr_path) if l.strip()}
conn = sqlite3.connect('state/kpi.db', timeout=30)
new = []
for f in sorted(os.listdir(q)) if os.path.isdir(q) else []:
    if not f.endswith('.txt') or f in appr:
        continue
    p = os.path.join(q, f)
    problems = [r for r, _ in outreach_gate.check(p, conn)]
    if not problems:
        new.append(f)
if new:
    with open(appr_path, 'a') as fh:
        fh.write('\n'.join(new) + '\n')
print(f"auto-approved {len(new)} drafts: {new[:5]}")
PYEOF
  python3 bin/send_outreach.py --arm >> "$LOG" 2>&1
  sleep 3600
done
echo "[$(date -u +%FT%TZ)] auto-send window complete" >> "$LOG"
