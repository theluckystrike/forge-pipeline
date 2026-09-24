#!/bin/bash
# usage: 08fetch.sh name url
S=/private/tmp/claude-501/-Users-mike-cloud-session-test/6a7524ee-68d0-4521-aef8-fbea27f1798b/scratchpad/r/08raw
n=$1; u=$2
code=$(curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36" -H "Accept-Language: en-US,en;q=0.9" --max-time 40 -o "$S/$n.html" -w '%{http_code}' "$u")
echo "$n $code $(wc -c < $S/$n.html) title=$(grep -o '<title>[^<]*' $S/$n.html | head -1 | cut -c8-90)"
