import subprocess,json,base64,polib
raw_missing=open('/tmp/wivrn_missing_raw.txt').read().splitlines()
def get(p,ref='master'):
    d=subprocess.run(['gh','api',f'repos/WiVRn/WiVRn/contents/{p}?ref={ref}'],capture_output=True,text=True)
    return base64.b64decode(json.loads(d.stdout)['content']).decode()
fr_client=get('locale/fr/wivrn.po'); fr_dash=get('locale/fr/wivrn-dashboard.po')
pc=polib.pofile(fr_client); pd=polib.pofile(fr_dash)
cids={e.msgid for e in pc}; dids={e.msgid for e in pd}
res={'client':[],'dashboard':[],'UNKNOWN':[]}
for m in raw_missing:
    inner=m[1:-1] if m[0] in '\'"' else m
    if inner in cids: res['client'].append(inner)
    elif inner in dids: res['dashboard'].append(inner)
    else: res['UNKNOWN'].append(inner)
for k in res:
    print('==',k,len(res[k]))
    for s in res[k]: print('  ',repr(s))
json.dump(res,open('/tmp/wivrn_split.json','w'))
