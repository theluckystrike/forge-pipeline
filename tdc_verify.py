import subprocess,hashlib,json

FK='theluckystrike/arkhamdb-json-data'
BR='de/tdcc'
PATH='translations/de/pack/tdc/tdcc.json'

# read back raw and byte-compare
r=subprocess.run(['curl','-sL','--max-time','120',f'https://raw.githubusercontent.com/{FK}/{BR}/{PATH}'],capture_output=True)
rb=r.stdout
local=open('/tmp/tdcc_de_out.json','rb').read()
print('RB_IDENTICAL',rb==local,'rb_bytes',len(rb),'local_bytes',len(local))
j=json.loads(rb)
print('parsed ok, cards',len(j))
changed=sum(1 for c in j if c.get('text') and c['code'] in ('11503','11702'))
print('spot check present',changed)
