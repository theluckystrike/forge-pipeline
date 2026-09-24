#!/bin/bash
# usage: fetch.sh name url  -> saves html and prints text
D=/private/tmp/claude-501/-Users-mike-cloud-session-test/6a7524ee-68d0-4521-aef8-fbea27f1798b/scratchpad/r/raw
n=$1; u=$2
code=$(curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36" -o "$D/$n.html" -w "%{http_code} %{url_effective}" --max-time 40 "$u")
echo "== $n $u -> $code"
python3 - "$D/$n.html" <<'PY'
import sys,re,html
s=open(sys.argv[1],encoding='utf-8',errors='ignore').read()
s=re.sub(r'(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>','',s)
s=re.sub(r'(?i)<br\s*/?>|</p>|</div>|</li>|</h\d>|</tr>','\n',s)
s=re.sub(r'<[^>]+>',' ',s)
s=html.unescape(s)
s=re.sub(r'[ \t]+',' ',s)
s=re.sub(r'\n\s*\n+','\n',s)
print(s[:12000])
PY
