import subprocess,json,base64,os,sys

def blob(repo,p):
    r=subprocess.run(['gh','api',f'repos/{repo}/contents/{p}','--jq','.sha'],capture_output=True,text=True)
    sha=r.stdout.strip()
    if not sha: return None
    r=subprocess.run(['gh','api',f'repos/{repo}/git/blobs/{sha}'],capture_output=True,text=True)
    try:
        return json.loads(base64.b64decode(json.loads(r.stdout)['content']).decode())
    except Exception:
        return None

out=open('/tmp/s48_gap.txt','w')
r=subprocess.run(['gh','api','repos/Kamalisk/arkhamdb-json-data/contents/translations/de/pack','--jq','.[].name'],capture_output=True,text=True)
packs=r.stdout.split()
for pk in packs:
    r=subprocess.run(['gh','api',f'repos/Kamalisk/arkhamdb-json-data/contents/translations/de/pack/{pk}','--jq','.[].name'],capture_output=True,text=True)
    files=r.stdout.split()
    for f in files:
        p=f'translations/de/pack/{pk}/{f}'
        d=blob('Kamalisk/arkhamdb-json-data',p)
        en=blob('Kamalisk/arkhamdb-json-data',f'pack/{pk}/{f}')
        if not en: continue
        dmap={c['code']:c.get('text') for c in (d or [])}
        un=sum(1 for c in en if c.get('text') and not dmap.get(c['code']))
        total=sum(1 for c in en if c.get('text'))
        if un:
            line=f'{pk}/{f} untranslated {un}/{total}'
            print(line); out.write(line+'\n'); out.flush()
out.close()
print('DONE')
