import json,re

def tolerant_parse(path):
    src=open(path).read()
    pairs={}
    i=0
    pat=re.compile(r'"([0-9a-zb]+\|[a-z.0-9]+)":\s*"')
    while True:
        m=pat.search(src,i)
        if not m: break
        j=m.end(); buf=[]
        while True:
            ch=src[j]
            if ch=='\\':
                buf.append(src[j:j+2]); j+=2; continue
            if ch=='"': break
            buf.append(ch); j+=1
        raw=''.join(buf)
        try:
            val=json.loads('"'+raw.replace('\n','\\n')+'"')
        except Exception:
            val=raw
        pairs[m.group(1)]=val
        i=j+1
    return pairs

T={}
for n in range(6):
    T.update(tolerant_parse(f'/Users/mike/oss-pipeline/tdc_de_c{n}.py'))

tasks=json.load(open('/tmp/tdc_tasks.json'))
missing=[(c,f) for c,f,t in tasks if (c+'|'+f) not in T]
print('parsed',len(T),'missing',len(missing))

# Extra fixes dict (verified translations, json-escaped properly here)
FIX=json.load(open('/tmp/tdc_extra_fixes.json'))
T.update(FIX)
missing=[(c,f) for c,f,t in tasks if (c+'|'+f) not in T]
print('after fixes missing',len(missing),missing[:20])
json.dump(T,open('/tmp/tdc_de_all.json','w'),ensure_ascii=False,indent=1)
