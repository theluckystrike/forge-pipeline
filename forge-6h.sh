
#!/bin/bash
# FORGE 6h loop, started 2026-09-26 ~21:00 by Hermes orchestrator
END=$((SECONDS+21600))
CYCLE=0
while [ $SECONDS -lt $END ]; do
  CYCLE=$((CYCLE+1))
  echo "=== FORGE cycle $CYCLE $(date -u +%H:%M) ==="
  cd /Users/mike/Desktop/oss-contrib-pipeline
  # merge sweep of tracked PRs
  for pr in "calcom/cal.diy 30245" "calcom/cal.diy 30246" "calcom/cal.diy 30247" "PapillonApp/Papillon 840" "WiVRn/WiVRn 1136" "OWASP/cve-lite-cli 1239" "Kochava-Studios/witsy 596" "revenz/Fenrus 258" "Samuels-Development/ox_inventory 7"; do
    set -- $pr; st=$(gh api repos/$1/pulls/$2 --jq '.state+" m="+(.merged|tostring)+" "+.mergeable_state' 2>/dev/null)
    echo "$1#$2 $st"
  done
  # discovery cycle every 4th cycle (~2h)
  if [ $((CYCLE % 4)) -eq 1 ]; then
    cd /Users/mike/oss-pipeline && timeout 500 python3 pipeline.py 2>&1 | tail -6
  fi
  sleep 1800
done
echo "FORGE 6h loop complete $(date -u)"
