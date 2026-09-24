#!/bin/bash
# PARK WATCH — poll goal targets every 10 min, print ALERT line on any change
cd /Users/mike/oss-pipeline
STATE=state/anvil-night/park-watch.txt
prev=$(cat "$STATE" 2>/dev/null)
snap() {
  h6669=$(gh api repos/hoppscotch/hoppscotch/issues/6669 --jq '"\(.state):\(.comments)"' 2>/dev/null)
  h6671=$(gh api repos/hoppscotch/hoppscotch/issues/6671 --jq '"\(.state):\(.comments)"' 2>/dev/null)
  h6672=$(gh api repos/hoppscotch/hoppscotch/issues/6672 --jq '"\(.state):\(.comments)"' 2>/dev/null)
  h6676=$(gh api repos/hoppscotch/hoppscotch/issues/6676 --jq '"\(.state):\(.comments)"' 2>/dev/null)
  j9054=$(gh api repos/janhq/jan/pulls/9054 --jq '"\(.state):\(.merged):\(.comments)"' 2>/dev/null)
  s523=$(gh api repos/toss/react-simplikit/pulls/523 --jq '"\(.state):\(.merged):\(.comments)"' 2>/dev/null)
  s501=$(gh api repos/toss/react-simplikit/issues/501 --jq '"\(.state):\(.comments)"' 2>/dev/null)
  c30229=$(gh api repos/calcom/cal.diy/pulls/30229 --jq '"\(.state):\(.merged):\(.comments)"' 2>/dev/null)
  c30230=$(gh api repos/calcom/cal.diy/pulls/30230 --jq '"\(.state):\(.merged):\(.comments)"' 2>/dev/null)
  f9394=$(gh api repos/formbricks/formbricks/issues/9394 --jq '"\(.state):\(.comments)"' 2>/dev/null)
  echo "j9054=$j9054|6669=$h6669|6671=$h6671|6672=$h6672|6676=$h6676|s523=$s523|s501=$s501|c30229=$c30229|c30230=$c30230|f9394=$f9394"
}
prev=$(snap)
while true; do
  sleep 600
  cur=$(snap)
  ts=$(date -u +%H:%M:%SZ)
  if [ "$cur" != "$prev" ]; then
    echo "ALERT [$ts] goal state changed:"
    echo "  was: $prev"
    echo "  now: $cur"
    echo "$cur" > "$STATE"
    prev="$cur"
  else
    echo "[$ts] parked, no change — $cur"
  fi
done
