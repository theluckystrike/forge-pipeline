import subprocess,re
r=subprocess.run(['gh','run','view','--job','108809602508','--repo','WiVRn/WiVRn','--log'],capture_output=True,text=True)
missing=[]
for line in r.stdout.splitlines():
    m=re.search(r'de translation for (.*) is missing$',line)
    if m: missing.append(m.group(1).strip().strip("'\""))
with open('/tmp/wivrn_missing.txt','w') as f:
    for s in missing: f.write(s+'\n')
print(len(missing))
for s in missing[:40]: print(repr(s))
