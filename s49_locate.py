# Determine which po files (de/wivrn.po, de/wivrn-dashboard.po) contain each missing msgid
import subprocess,json,base64
missing=[l.rstrip('\n') for l in open('/tmp/wivrn_missing.txt')]
# strip python-escaped \\n into actual marker check: po file stores as literal \n inside quotes
files=['locale/de/wivrn.po','locale/de/wivrn-dashboard.po']
content={}
for p in files:
    d=subprocess.run(['gh','api',f'repos/WiVRn/WiVRn/contents/{p}?ref=refs/pull/1136/head'],capture_output=True,text=True)
    j=json.loads(d.stdout)
    content[p]=base64.b64decode(j['content']).decode()
    print(p,j['size'],'bytes, sha',j['sha'][:10])
# check msgid presence
for s in missing:
    raw=s if s.startswith('"') or s.startswith("'") else None
    # normalize: inner text
    inner=s[1:-1] if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")) else s
    hits=[p for p in files if 'msgid "'+inner.replace('\\n','\\n')+'"' in content[p] or inner in content[p]]
    print('FILE' if hits else 'NONE', hits, repr(inner[:60]))
