# S50 ship: fork branch, single commit of translations/de/pack/cob/cob.json, PR.
import subprocess,json,base64,tempfile,os

UP='Kamalisk/arkhamdb-json-data'
FORK='theluckystrike/arkhamdb-json-data'
BR='de-cob-translations'
PATH='translations/de/pack/cob/cob.json'

def run(args):
    r=subprocess.run(args,capture_output=True,text=True)
    assert r.returncode==0,(r.stdout,r.stderr)
    return r.stdout

# base sha
sha=run(['gh','api',f'repos/{UP}/git/ref/heads/master','--jq','.object.sha']).strip()
print('base',sha)
# create branch on fork
run(['gh','api','-X','POST',f'repos/{FORK}/git/refs','-f',f'ref=refs/heads/{BR}','-f',f'sha={sha}'])
print('branch created')
# commit content
content=open('/Users/mike/oss-pipeline/s50_de_cob.json','rb').read()
p=tempfile.NamedTemporaryFile('w',delete=False,suffix='.json')
json.dump({'message':'add German translations for Children of Blood cards','content':base64.b64encode(content).decode(),'branch':BR},p); p.close()
r=run(['gh','api','-X','PUT',f'repos/{FORK}/contents/{PATH}','--input',p.name,'--jq','.commit.sha'])
print('commit',r.strip())
PYEOF