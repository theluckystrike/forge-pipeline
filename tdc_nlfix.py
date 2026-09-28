import json
ns={}
exec(open('/tmp/tdc_fixes_raw.py').read().replace('\\n','\\\\n'),ns) if False else None
# Build fixes JSON from the raw fixes file by exec'ing it with a fallback for broken strings:
# Since tdc_fix2.py strings contain raw newlines (invalid), re-extract from chunk files instead.
import re

# Rebuild all fixes from scratch: re-parse each cN file, detect broken multi-line string entries, and re-emit with json.dumps.
def parse_and_fix(p):
    src=open(p).read()
    # Strategy: convert every "key": "....", pair allowing raw newlines by regex on the value up to the trailing '",' at line end
    pat=re.compile(r'("[0-9a-zb]+\|[a-z]+": ")(.*?)(",?)\n(?="|\}|$)', re.S)
    def repl(m):
        key=m.group(1)
        val=m.group(2)
        # if val contains raw newline it was a literal; escape it
        if '\n' in val:
            val=val.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')
        return key+val+m.group(3)+'\n'
    new=pat.sub(repl,src)
    open(p,'w').write(new)
    return new

for n in range(6):
    p=f'/Users/mike/oss-pipeline/tdc_de_c{n}.py'
    parse_and_fix(p)
    try:
        ns={}
        exec(open(p).read(),ns)
        print(n,'OK',len(ns['T']))
    except SyntaxError as e:
        print(n,'ERR',e.lineno)
