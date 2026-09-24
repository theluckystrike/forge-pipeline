import json,subprocess,urllib.request,os
def flat(d,p=''):
    o={}
    for k,v in d.items():
        kp=p+'.'+k if p else k
        o.update(flat(v,kp)) if isinstance(v,dict) else o.__setitem__(kp,v)
    return o
def raw(repo,sha,path):
    return json.loads(urllib.request.urlopen(f'https://raw.githubusercontent.com/{repo}/{sha}/{path}',timeout=30).read())
for n in [l.split('\t')[0] for l in open('medusa-prs.tsv')]:
    j=json.loads(subprocess.check_output(['gh','pr','view',n,'-R','medusajs/medusa','--json','headRefOid,headRepository,headRepositoryOwner,files,statusCheckRollup']))
    hrepo=j['headRepositoryOwner']['login']+'/'+j['headRepository']['name']
    checks={(c.get('name') or c.get('context')):(c.get('conclusion') or c.get('state')) for c in j['statusCheckRollup']}
    out=[]
    for f in j['files']:
        en=flat(raw(hrepo,j['headRefOid'],os.path.dirname(f['path'])+'/en.json')); h=flat(raw(hrepo,j['headRefOid'],f['path']))
        out.append(f"{os.path.basename(f['path'])} missing={len(set(en)-set(h))} en={len(en)}")
    print(n,'; '.join(out),'| checks:',checks)
