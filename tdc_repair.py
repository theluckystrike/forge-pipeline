import re

def load_fixes(path):
    # fixes file: entries like "key": "value",  possibly spanning raw lines; parse leniently by json-ish
    txt=open(path).read()
    txt=txt[txt.index('{'):txt.rindex('}')+1]
    import json
    try:
        return json.loads(txt)
    except Exception:
        # fallback: use ast with triple-quote normalization? bail
        raise

def replace_entries(path, fixes):
    lines=open(path).read().split('\n')
    out=[]
    skip=False
    for ln in lines:
        if skip:
            if ln.rstrip().endswith('",') or ln.rstrip().endswith('"'):
                skip=False
            continue
        m=re.match(r'\s*"([0-9a-zb]+)\|([a-z]+)":', ln)
        if m and m.group(1)+'|'+m.group(2) in fixes and 'None' not in ln[:40]:
            v=fixes[m.group(1)+'|'+m.group(2)]
            out.append(json_key(m.group(1),m.group(2))+json_val(v)+',')
            skip=True
            continue
        out.append(ln)
    open(path,'w').write('\n'.join(out))

def json_key(c,f): return '"%s|%s": '%(c,f)
def json_val(v): return json.dumps(v,ensure_ascii=False)

if __name__=='__main__':
    import json,sys
    fixes=json.load(open('/tmp/tdc_fixes.json'))
    for n in range(6):
        p=f'/Users/mike/oss-pipeline/tdc_de_c{n}.py'
        s=open(p).read()
        mine={k:v for k,v in fixes.items() if '"'+k+'"' in s}
        if mine:
            replace_entries(p,mine)
            print(n,sorted(mine))
