import subprocess,json,base64,hashlib,os

REPO='Kamalisk/arkhamdb-json-data'
def api(path):
    r=subprocess.run(['gh','api',path],capture_output=True,text=True)
    assert r.returncode==0, r.stderr
    return json.loads(r.stdout)
def blob(p):
    d=api(f'repos/{REPO}/contents/{p}')
    return d['sha'], base64.b64decode(d['content']).decode()

targets={
 'pack/core/core_2026.json':[12020,12031,12032,12049,12050,12064,12065,12073,12077,12078,12090,12091,12092,12093,12101],
 'pack/investigator/and.json':[60361,60371,60372,60379,60384],
 'pack/tde/sfk_encounter.json':[6132],
}
de=json.load(open('/Users/mike/oss-pipeline/s48_de.json'))  # code -> {name,text}

for p,codes in targets.items():
    sha,raw=blob(p)
    pack=json.loads(raw)
    changed=0
    for card in pack:
        code=int(card['code'])
        if code in codes:
            t=de[str(code)]
            # cards may omit name; match on text identity with de.arkhamdb real_text instead
            assert card['text'].strip()==t['en_text'].strip() or card['text'].strip()==t['de_text'].strip(), (code, card['text'][:60])
            card['text']=t['de_text']
            changed+=1
    assert changed==len(codes), (p,changed)
    out=json.dumps(pack,ensure_ascii=False,indent=2)
    fn='/Users/mike/oss-pipeline/s48_'+p.replace('/','_')
    open(fn,'w').write(out)
    # roundtrip sanity: parse again, confirm only text fields of targets differ
    chk=json.loads(out)
    old=json.loads(raw)
    diffs=[]
    for o,n in zip(old,chk):
        if o!=n:
            keys=[k for k in o if o[k]!=n.get(k)]
            diffs.append((o['code'],keys))
    print(p,'ok changed',changed,'diffkeys',diffs, 'sha256',hashlib.sha256(out.encode()).hexdigest()[:12])
