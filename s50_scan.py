# Find biggest en-pack vs de-pack card-count gaps across all cycles (rate-limit friendly, sequential).
import subprocess,json,base64,time
def ls(p):
    for a in range(4):
        d=subprocess.run(['gh','api',f'repos/Kamalisk/arkhamdb-json-data/contents/{p}'],capture_output=True,text=True)
        if d.returncode==0:
            return [(x['name'],x['size']) for x in json.loads(d.stdout)]
        time.sleep(20*(2**a))
    return []
def ncards(p):
    for a in range(4):
        d=subprocess.run(['gh','api',f'repos/Kamalisk/arkhamdb-json-data/contents/{p}'],capture_output=True,text=True)
        if d.returncode==0:
            j=json.loads(d.stdout)
            raw=base64.b64decode(j['content']).decode()
            return len(json.loads(raw))
        time.sleep(20*(2**a))
    return -1
out=[]
for cycle in ['cob','core','dwl','eoe','fhv','investigator','parallel','promo','ptc','return','side','tcu','tdc','tde','tfa','tic','tsk']:
    en=ls(f'pack/{cycle}')
    try:
        de=dict(ls(f'translations/de/pack/{cycle}'))
    except Exception:
        de={}
    for name,size in en:
        if name not in de:
            out.append((cycle,name,size,'MISSING-FILE'))
        elif size==0:
            out.append((cycle,name,size,'EMPTY'))
    time.sleep(1)
print(len(out),'gap files')
for row in out: print(row)
open('/tmp/s50_gaps.txt','w').write(repr(out))
