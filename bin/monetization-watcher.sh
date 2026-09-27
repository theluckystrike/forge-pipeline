#!/bin/bash
# Monetization-signal watcher: exits 42 when a tracked PR merges, gains comments, or an outreach reply lands.
cd /Users/mike/oss-pipeline || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
END=$((SECONDS+21600))
while [ $SECONDS -lt $END ]; do
  rm -f state/monetization-baseline.tmp
  for pr in "baptisteArno/typebot.io 2610" "baptisteArno/typebot.io 2611" \
            "toss/react-simplikit 523" "janhq/jan 9054" \
            "calcom/cal.diy 30229" "calcom/cal.diy 30230" \
            "hoppscotch/hoppscotch 6669"; do
    set -- $pr
    st=$(gh api "repos/$1/pulls/$2" --jq 'if .merged then "MERGED" else .state end' 2>/dev/null)
    if [ "$st" = "MERGED" ]; then
      echo "[$(date -u +%FT%TZ)] MERGE SIGNAL $1#$2" >> state/monetization-signals.log
      exit 42
    fi
    c=$(gh api "repos/$1/issues/$2/comments" --jq 'length' 2>/dev/null)
    prev=$(awk -v k="$1#$2" '$1==k {print $2}' state/monetization-baseline.txt 2>/dev/null)
    if [ -n "$prev" ] && [ -n "$c" ] && [ "$c" -gt "$prev" ]; then
      echo "[$(date -u +%FT%TZ)] COMMENT SIGNAL $1#$2 $prev->$c" >> state/monetization-signals.log
      exit 42
    fi
    echo "$1#$2 $c" >> state/monetization-baseline.tmp
  done
  mv state/monetization-baseline.tmp state/monetization-baseline.txt
  r=$(sqlite3 state/kpi.db "select count(*) from outreach where replied=1" 2>/dev/null)
  if [ "${r:-0}" -gt 0 ]; then
    echo "[$(date -u +%FT%TZ)] REPLY SIGNAL count=$r" >> state/monetization-signals.log
    exit 42
  fi
  sleep 900
done
echo "[$(date -u +%FT%TZ)] watcher done, no signals in 6h" >> state/monetization-signals.log
