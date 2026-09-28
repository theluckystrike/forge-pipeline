import json,subprocess,tempfile,os,base64

UP='Kamalisk/arkhamdb-json-data'
FK='theluckystrike/arkhamdb-json-data'
HEAD='178f1fde264b0b03b78622c7a380eb87c7c88ca1'
BR='de/tdcc'

r=subprocess.run(['gh','api','-X','POST',f'repos/{FK}/git/refs','--input','-',
                  '-f',f'ref=refs/heads/{BR}','-f',f'sha={HEAD}'],capture_output=True,text=True)
# gh --input '-' reads stdin; safer: use -F via temp file
if r.returncode!=0:
    f=tempfile.NamedTemporaryFile('w',suffix='.json',delete=False)
    json.dump({'ref':f'refs/heads/{BR}','sha':HEAD},f); f.close()
    r=subprocess.run(['gh','api','-X','POST',f'repos/{FK}/git/refs','--input',f.name],capture_output=True,text=True)
    os.unlink(f.name)
print('branch:',r.stdout.strip() or r.stderr.strip())
