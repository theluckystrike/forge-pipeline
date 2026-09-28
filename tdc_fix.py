import json,re

def replace_entries(path, fixes):
    lines=open(path).read().split('\n')
    out=[]
    cur=None
    skip=False
    for ln in lines:
        if skip:
            if ln.startswith('"') or ln=='}':
                skip=False
            else:
                continue
        m=re.match(r'"([0-9a-zb]+)\|text"',ln)
        if m and m.group(1) in fixes:
            out.append(fixes[m.group(1)])
            skip=True
            continue
        m2=re.match(r'"([0-9a-zb]+)\|subname"',ln)
        if m2 and (m2.group(1),'subname') in fixes:
            k=m2.group(1)
            out.append(f'"{k}|subname": {fixes[(k,"subname")]!r},')
            skip=True
            continue
        out.append(ln)
    open(path,'w').write('\n'.join(out))
    ns={}
    exec(open(path).read(),ns)
    return ns['T']

if __name__=='__main__':
    tasks=json.load(open('/tmp/tdc_tasks.json'))
    for n in (0,1,2,3):
        p=f'/Users/mike/oss-pipeline/tdc_de_c{n}.py'
        T=replace_entries(p,{})
        missing=[(c,f) for c,f,t in tasks[n*64:(n+1)*64] if (c+'|'+f) not in T]
        print(n,'entries',len(T),'missing',missing)
