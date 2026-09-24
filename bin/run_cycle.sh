#!/bin/bash
# WhiteHERO v3 one-command cycle: discover, qualify, audit, contacts, draft, gate, dashboard.
# Sends nothing. Usage: bin/run_cycle.sh [AUDIT_N]   (AUDIT_N = top targets to consider for audit, default 200)
set -u
cd /Users/mike/oss-pipeline || exit 1
N=${1:-200}
LOG=state/cycle-$(date +%Y%m%dT%H%M%S).log
step(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
run(){ step "RUN $*"; "$@" >>"$LOG" 2>&1; rc=$?; step "rc=$rc $1 $2"; return $rc; }
run python3 discover.py                                   || step "discover failed, continuing with existing targets"
run python3 qualify.py --batch 15 --from-db               || step "qualify failed, continuing"
run python3 audit_report.py --from-db "$N" --skip-done --workers 4 || step "audit failed, continuing"
run python3 contacts.py --top 400                         || step "contacts failed, continuing"
run python3 contacts.py --recompute
run python3 build_outreach.py --max-l1 40 --max-l2 20
run python3 outreach_gate.py
run python3 bin/dashboard.py
cp WHITEHERO-DASHBOARD.html /Users/mike/Desktop/WHITEHERO-DASHBOARD.html.tmp && mv /Users/mike/Desktop/WHITEHERO-DASHBOARD.html.tmp /Users/mike/Desktop/WHITEHERO-DASHBOARD.html
step "SUMMARY $(sqlite3 -cmd '.timeout 30000' state/kpi.db "select 'targets='||(select count(*) from targets)||' B>=0.4='||(select count(*) from targets where B>=0.4)||' audits='||(select count(*) from audits)||' audits3+='||(select count(*) from audits where stale_claims+failing_examples>=3)||' contacts='||(select count(*) from targets where contact_email is not null)||' drafts_unsent='||(select count(*) from outreach where sent_at is null and notes='draft')")"
python3 bin/send_outreach.py | tail -3 | tee -a "$LOG"
step "DONE log=$LOG"
