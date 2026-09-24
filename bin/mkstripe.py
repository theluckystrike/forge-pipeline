#!/usr/bin/env python3
# Creates the 4 WhiteHERO v3 SKUs (product, price, payment link) in the Stripe account the CLI is bound to.
# usage: python3 mkstripe.py test|live   -> writes state/stripe.json[mode]
# Refuses nothing on its own: check `stripe get /v1/account --live` first. Not idempotent: running twice creates duplicates.
import json,subprocess,sys
MODE=sys.argv[1]  # live or test
flag=['--live'] if MODE=='live' else []
def call(path,params):
    cmd=['stripe','post',path]+flag
    for k,v in params: cmd+=['-d',f'{k}={v}']
    out=subprocess.run(cmd,capture_output=True,text=True)
    j=json.loads(out.stdout or out.stderr)
    if 'error' in j: print('ERROR',path,j['error']); sys.exit(1)
    return j
items=[
 ('locale','Locale completion (one locale to 100% parity)','One locale file brought to 100% key parity with your source locale, delivered as a merge-ready pull request. LLM translation, placeholder-exact, CI-validated, human spot check on 10% of strings.',50000,None,True),
 ('retainer','Maintenance retainer','10 to 15 pull requests per month on your repos: locale parity, stale docs numbers, broken examples. Cancel any month.',150000,'month',False),
 ('audit','Repo audit (drift and locale parity)','Written report for one repository: locale parity per language, stale README numbers, examples that fail to build.',5000,None,False),
 ('first20','First 20 fixes','Twenty fixes from your repo audit, delivered as merge-ready pull requests against your repository.',90000,None,False),
]
res={}
for key,name,desc,amt,interval,adj in items:
    p=call('/v1/products',[('name',name),('description',desc),('metadata[lane]','L2' if key in('locale',) else 'L1'),('metadata[source]','whitehero-v3')])
    pp=[('product',p['id']),('unit_amount',amt),('currency','usd'),('metadata[source]','whitehero-v3')]
    if interval: pp.append(('recurring[interval]',interval))
    pr=call('/v1/prices',pp)
    lp=[('line_items[0][price]',pr['id']),('line_items[0][quantity]',1),('billing_address_collection','required'),('tax_id_collection[enabled]','true'),('metadata[source]','whitehero-v3'),('metadata[sku]',key)]
    if adj: lp+= [('line_items[0][adjustable_quantity][enabled]','true'),('line_items[0][adjustable_quantity][minimum]',1),('line_items[0][adjustable_quantity][maximum]',20)]
    pl=call('/v1/payment_links',lp)
    res[key]={'product':p['id'],'name':name,'price':pr['id'],'unit_amount':amt,'currency':'usd','recurring':interval,'payment_link':pl['id'],'url':pl['url'],'livemode':pl['livemode']}
    print(key,p['id'],pr['id'],pl['id'],pl['url'],pl['livemode'])
import os
SP=os.path.expanduser('~/oss-pipeline/state/stripe.json')
try: st=json.load(open(SP))
except Exception: st={}
st[MODE]=res
json.dump(st,open(SP,'w'),indent=2)
