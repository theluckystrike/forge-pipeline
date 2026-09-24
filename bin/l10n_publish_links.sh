#!/bin/bash
# Owner runs this AFTER granting the Stripe CLI live key Products/Prices/Payment Links write
# (or after `stripe login` with a key that has them). It creates the 4 live SKUs once,
# rebuilds the /l10n page with live payment links, and deploys via git push (Vercel git integration).
set -euo pipefail
PIPE=~/oss-pipeline; REPO=~/zovo-workspaces/zovo-one-source
stripe get /v1/account --live | python3 -c "import json,sys;j=json.load(sys.stdin);assert j['id']=='acct_1MmUPwJKCamubEm1',j['id'];print('account ok',j['id'])"
if python3 -c "import json,sys;sys.exit(0 if (json.load(open('$PIPE/state/stripe.json')).get('live')) else 1)"; then
  echo "live SKUs already recorded in state/stripe.json, not creating again"
else
  python3 $PIPE/bin/mkstripe.py live
fi
python3 -c "
import json,subprocess
for k,v in json.load(open('$PIPE/state/stripe.json'))['live'].items():
    c=subprocess.run(['curl','-s','-o','/dev/null','-w','%{http_code}','-L',v['url']],capture_output=True,text=True).stdout
    print(k,v['url'],c); assert c=='200'
"
python3 $PIPE/bin/build_l10n.py
python3 $PIPE/tools/humanize_scan.py --strict $PIPE/site/l10n.html
test "$(grep -c 'buy.stripe.com' $PIPE/site/l10n.html)" -ge 2
cd $REPO; git fetch origin; git merge --ff-only origin/main
cp $PIPE/site/l10n.html public/l10n/index.html
git add public/l10n/index.html; git commit -m "l10n: add live Stripe payment links"; git push origin main
echo "pushed; Vercel production build takes about 27 min. Then: curl -s https://zovo.one/l10n | grep -c buy.stripe.com"
