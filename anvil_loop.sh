#!/bin/bash
# ANVIL 6h autonomous loop driver. State lives in ~/oss-pipeline/state/anvil-loop/
# Each cycle runs one sprint script, updates STATUS + dashboard, then next.
set -u
DIR="$HOME/oss-pipeline/state/anvil-loop"
LOG="$DIR/loop.log"
STATE="$DIR/state.json"
mkdir -p "$DIR"
[ -f "$STATE" ] || echo '{"cycle":0,"max_cycles":4,"started":"'"$(date -u +%FT%TZ)"'","goal":"revenue"}' > "$STATE"

CYCLE=$(python3 -c "import json;print(json.load(open('$STATE'))['cycle'])")
MAX=$(python3 -c "import json;print(json.load(open('$STATE'))['max_cycles'])")
echo "[$(date -u +%FT%TZ)] ANVIL loop cycle $((CYCLE+1))/$MAX starting" >> "$LOG"

case $((CYCLE)) in
  0) SPRINT="A1";;
  1) SPRINT="A2";;
  2) SPRINT="A3";;
  3) SPRINT="A4";;
  *) SPRINT="A1";;
esac
echo "[$(date -u +%FT%TZ)] executing sprint $SPRINT" >> "$LOG"
python3 "$HOME/oss-pipeline/anvil_sprint.py" "$SPRINT" >> "$LOG" 2>&1

python3 - <<EOF
import json
s=json.load(open("$STATE"))
s["cycle"]+=1
s["last_sprint"]="$SPRINT"
json.dump(s,open("$STATE","w"))
EOF
echo "[$(date -u +%FT%TZ)] cycle done" >> "$LOG"
