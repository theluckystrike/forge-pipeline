
#!/bin/bash
# FORGE 6h loop, started 2026-09-26 ~21:00 by Hermes orchestrator
END=$((SECONDS+21600))
CYCLE=0
while [ $SECONDS -lt $END ]; do
  CYCLE=$((CYCLE+1))
  echo "=== FORGE cycle $CYCLE $(date -u +%H:%M) ==="
  cd /Users/mike/Desktop/oss-contrib-pipeline
  # merge sweep of tracked PRs
  for num in 16932 16934 17014; do
    st=$(gh api repos/medusajs/medusa/pulls/$num --jq '.state+" m="+(.merged|tostring)+" "+.mergeable_state' 2>/dev/null)
    echo "medusa#$num $st"
  done
  for pr in "Kochava-Studios/witsy 596" "revenz/Fenrus 258" "Samuels-Development/ox_inventory 7" "dumpus-app/dumpus-app 446" "666ghj/MiroFish 826" "jsxc/jsxc 1136"; do
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
