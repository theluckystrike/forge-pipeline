import urllib.request,json,time
codes=[12020,12031,12032,12049,12050,12064,12065,12073,12077,12078,12090,12091,12092,12093,12101,60361,60371,60372,60379,60384,6132]
out={}
for code in codes:
    for attempt in range(4):
        try:
            with urllib.request.urlopen(f'https://de.arkhamdb.com/api/public/card/{code}',timeout=30) as r:
                c=json.load(r)
            out[str(code)]={'en_name':c['real_name'],'de_name':c['name'],'de_text':c['text'],'en_text':c['real_text']}
            break
        except Exception as e:
            print(code,'retry',e); time.sleep(5*(attempt+1))
    else:
        raise SystemExit(f'FAIL {code}')
json.dump(out,open('/Users/mike/oss-pipeline/s48_de.json','w'),ensure_ascii=False,indent=1)
print('saved',len(out),'entries; 6132 de_text:',out.get('6132',{}).get('de_text','')[:80])
