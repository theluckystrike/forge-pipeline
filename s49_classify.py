import re
# no file= attribute in notices; split by which source file contains the msgid.
missing=[]
for line in open('/tmp/wivrn_log.txt'):
    m=re.search(r'translation for (".*"|\'.*\') is missing',line)
    if m: missing.append(m.group(1))
print(len(missing),'unique order')
# Dedup preserving order
seen=set(); out=[]
for s in missing:
    if s not in seen: seen.add(s); out.append(s)
open('/tmp/wivrn_missing_raw.txt','w').write('\n'.join(out))
# classify: which are client (_ in .cpp under client/) vs dashboard (i18n under dashboard/)
# Search upstream master source for each string
import subprocess,urllib.parse
def grep_repo(q):
    r=subprocess.run(['gh','api',f'search/code?q={urllib.parse.quote(q)}+repo:WiVRn/WiVRn'],capture_output=True,text=True)
    try:
        j=json.loads(r.stdout)
        return [i['path'] for i in j.get('items',[])][:3]
    except Exception:
        return ['ERR '+r.stderr[:80]]
import json
for s in out[:30]:
    inner=s[1:-1] if s[0] in '\'"' else s
    paths=grep_repo('"'+inner[:40]+'"')
    print(repr(inner[:50]),'->',paths)
