import subprocess,json,base64
def blob(p):
    r=subprocess.run(['gh','api',f'repos/Kamalisk/arkhamdb-json-data/contents/{p}','--jq','.sha'],capture_output=True,text=True)
    sha=r.stdout.strip()
    r=subprocess.run(['gh','api',f'repos/Kamalisk/arkhamdb-json-data/git/blobs/{sha}','--jq','.content'],capture_output=True,text=True)
    return json.loads(base64.b64decode(r.stdout.replace('\n','')))
out=open('/tmp/tdc_glossary.txt','w')
listing=subprocess.run(['gh','api','repos/Kamalisk/arkhamdb-json-data/contents/translations/de/pack','--jq','.[].name'],capture_output=True,text=True).stdout.split()
print('de packs:',listing)
hits={'Retaliate':[], 'Elusive':[], 'Erzwungen':[], 'Forced':[], 'berflut':[]}
for pk in listing:
    try:
        files=subprocess.run(['gh','api',f'repos/Kamalisk/arkhamdb-json-data/contents/translations/de/pack/{pk}','--jq','.[].name'],capture_output=True,text=True).stdout.split()
        cards=[]
        for f in files:
            cards+=blob(f'translations/de/pack/{pk}/{f[:-5]}.json')
        for c in cards:
            t=(c.get('text') or '')
            for k in hits:
                if k.lower() in t.lower() and len(hits[k])<2:
                    hits[k].append((pk,c['code'],t[:90].replace('\n',' | ')))
    except Exception: pass
for k,v in hits.items():
    print('==',k,file=out)
    for x in v: print('  ',x,file=out)
out.close()
print('DONE')
