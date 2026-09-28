import subprocess,json,base64,re,collections

def blob(p):
    r=subprocess.run(['gh','api',f'repos/Kamalisk/arkhamdb-json-data/contents/{p}','--jq','.sha'],capture_output=True,text=True)
    sha=r.stdout.strip()
    r=subprocess.run(['gh','api',f'repos/Kamalisk/arkhamdb-json-data/git/blobs/{sha}'],capture_output=True,text=True)
    return json.loads(base64.b64decode(json.loads(r.stdout)['content']).decode('utf-8'))

# Extract DE glossary from existing translated pack files (tcu = innsmouth-ish, use tde pack we know is translated)
gloss=collections.defaultdict(set)
patterns={
 'victory display':r'victory display',
 'shroud':r'shroud',
 'clue':r'clue',
 'doom':r'doom',
 'skill test':r'skill test',
 'hunter kw':r'Hunter',
 'alert':r'Alert',
 'aloof':r'Aloof',
 'retaliate':r'Retaliate',
 'massive':r'Massive',
 'relentless':r'Relentless',
 'surge':r'Surge',
 'peril':r'Peril',
 'forced':r'Forced',
 'revelation':r'Revelation',
 'objective':r'Objective',
 'prey':r'Prey',
 'spawn':r'Spawn',
 'threat area':r'threat area',
 'discard pile':r'discard pile',
 'encounter deck':r'encounter deck',
 'campaign log':r'Campaign Log',
 'hand size':r'hand size',
 'attacks of opportunity':r'attacks of opportunity',
}
pairs_file='/tmp/de_pairs.txt'
out=open(pairs_file,'w')
import os
packs=['tde','tcu','tic','tfa']
for pk in packs:
    p=f'pack/{pk}/{pk}.json'
    try:
        en=blob(p)
    except Exception as e:
        print('skip',pk,e); continue
    try:
        de=blob(f'translations/de/{p}')
    except Exception as e:
        print('node',pk,e); continue
    d={c['code']:c for c in de}
    for c in en:
        t=c.get('text'); 
        if not t: continue
        dt=d.get(c['code'],{}).get('text')
        if not dt or dt==t: continue
        out.write(f'### {c["code"]}\nEN: {t}\nDE: {dt}\n\n')
out.close()
print('pairs written', os.path.getsize(pairs_file))
