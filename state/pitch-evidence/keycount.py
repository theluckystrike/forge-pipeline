import json,subprocess,urllib.request,sys
def flat(d,p=''):
    o={}
    for k,v in d.items():
        kp=p+'.'+k if p else k
        if isinstance(v,dict): o.update(flat(v,kp))
        else: o[kp]=v
    return o
def raw(repo,sha,path):
    try: return json.loads(urllib.request.urlopen(f'https://raw.githubusercontent.com/{repo}/{sha}/{path}',timeout=30).read())
    except Exception as e: return {}
T_add=T_chg=0
for n in [l.split('\t')[0] for l in open('medusa-prs.tsv')]:
    j=json.loads(subprocess.check_output(['gh','pr','view',n,'-R','medusajs/medusa','--json','headRefOid,baseRefOid,headRepository,headRepositoryOwner,files']))
    hrepo=j['headRepositoryOwner']['login']+'/'+j['headRepository']['name']
    add=chg=0
    for f in j['files']:
        b=flat(raw('medusajs/medusa',j['baseRefOid'],f['path'])); h=flat(raw(hrepo,j['headRefOid'],f['path']))
        a=len(set(h)-set(b)); c=sum(1 for k in set(h)&set(b) if h[k]!=b[k])
        add+=a; chg+=c
    print(n,'added',add,'changed',chg); T_add+=add; T_chg+=chg
print('TOTAL added',T_add,'changed',T_chg,'sum',T_add+T_chg)
