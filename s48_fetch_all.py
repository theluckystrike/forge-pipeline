# Fetch de text for all 36 missing card codes from de.arkhamdb (per-card API, retries).
# Store both de translation AND current en real_text so we can diff against repo EN and adapt.
import urllib.request,json,time
codes=['12020','12024','12025','12031','12032','12034','12038','12039','12042','12044','12049','12050','12056','12064','12065','12069','12073','12077','12078','12089','12090','12091','12092','12093','12094','12095','12096','12097','12100','12101','60361','60371','60372','60379','60381','60384']
out={}
fail=[]
for code in codes:
    ok=False
    for attempt in range(4):
        try:
            with urllib.request.urlopen(f'https://de.arkhamdb.com/api/public/card/{code}',timeout=30) as r:
                c=json.load(r)
            out[code]={'de_name':c['name'],'de_text':c['text'],'de_traits':c.get('traits',''),'de_flavor':c.get('flavor',''),
                       'en_name':c.get('real_name'),'en_text':c.get('real_text'),'en_traits':c.get('real_traits',''),
                       'type_code':c.get('type_code'),'slot':c.get('slot'),'cost':c.get('cost'),'xp':c.get('xp')}
            ok=True; break
        except Exception as e:
            print(code,'retry',attempt,e); time.sleep(3*(attempt+1))
    if not ok: fail.append(code)
json.dump(out,open('/Users/mike/oss-pipeline/s48_de_full.json','w'),ensure_ascii=False,indent=1)
print('fetched',len(out),'failed',fail)
