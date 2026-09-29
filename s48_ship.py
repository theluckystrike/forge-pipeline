# Ship both files via Contents API PUT to fork branch de-core2026-and-gap.
import subprocess,json,base64,tempfile,os,sys

FORK='theluckystrike/arkhamdb-json-data'
BR='de-core2026-and-gap'
SHIPS=[
 ('translations/de/pack/core/core_2026.json','s48_new_translations_de_pack_core_core_2026.json','add German translations for 30 core set 2026 cards'),
 ('translations/de/pack/investigator/and.json','s48_new_translations_de_pack_investigator_and.json','add German translations for 6 and pack cards'),
]
for path,fn,msg in SHIPS:
    content=open(fn,'rb').read()
    # get current sha of file on fork branch
    r=subprocess.run(['gh','api',f'repos/{FORK}/contents/{path}?ref={BR}'],capture_output=True,text=True)
    if r.returncode==0:
        fsha=json.loads(r.stdout)['sha']
    else:
        fsha=None
    payload={'message':msg,'content':base64.b64encode(content).decode(),'branch':BR}
    if fsha: payload['sha']=fsha
    f=tempfile.NamedTemporaryFile('w',delete=False,suffix='.json');json.dump(payload,f);f.close()
    r=subprocess.run(['gh','api',f'repos/{FORK}/contents/{path}','-X','PUT','--input',f.name],capture_output=True,text=True)
    os.unlink(f.name)
    if r.returncode!=0:
        print('FAIL',path,r.stderr[:300]); sys.exit(1)
    out=json.loads(r.stdout)
    print('COMMITTED',path,'->',out['commit']['sha'][:12], msg)
