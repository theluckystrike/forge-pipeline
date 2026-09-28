import json,subprocess,tempfile,os,hashlib,base64

FK='theluckystrike/arkhamdb-json-data'
BR='de/tdcc'
PATH='translations/de/pack/tdc/tdcc.json'
LOCAL='/tmp/tdcc_de_out.json'

# 1. get current blob sha on the branch
r=subprocess.run(['gh','api',f'repos/{FK}/contents/{PATH}?ref={BR}','--jq','.sha'],capture_output=True,text=True)
sha=r.stdout.strip()
print('blob sha',sha)

# 2. commit new content
content=open(LOCAL,'rb').read()
payload={'message':'Add German translations for The Drowned City campaign cards',
         'content':base64.b64encode(content).decode(),'branch':BR}
if sha: payload['sha']=sha
f=tempfile.NamedTemporaryFile('w',suffix='.json',delete=False)
json.dump(payload,f); f.close()
r=subprocess.run(['gh','api','-X','PUT',f'repos/{FK}/contents/{PATH}','--input',f.name,
                  '--jq','{sha:.content.sha,size:.commit.size}'],capture_output=True,text=True)
print('commit:',r.stdout.strip() or r.stderr.strip())
os.unlink(f.name)
print('local md5',hashlib.md5(content).hexdigest(),'bytes',len(content))
