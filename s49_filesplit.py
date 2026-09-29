import subprocess,re
r=subprocess.run(['gh','run','view','--job','108809602508','--repo','WiVRn/WiVRn','--log'],capture_output=True,text=True)
seen=set()
for line in r.stdout.splitlines():
    m=re.search(r'file=(\S+)::',line)
    m2=re.search(r'translation for (.*) is missing',line)
    if m and m2:
        key=(m.group(1),m2.group(1))
        if key not in seen:
            seen.add(key)
            print(m.group(1), repr(m2.group(1))[:90])
