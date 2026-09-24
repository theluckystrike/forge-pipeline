"""Exact-100 hunt: gfi + docs/test + 0 comments + fresh + high stars.
With the score clamp fixed, a candidate fully satisfying the rubric now lands at 100.
"""
import subprocess, json, time
from datetime import datetime

def gh(endpoint):
    out = subprocess.run(["gh","api",endpoint], capture_output=True, text=True, timeout=60)
    if out.returncode != 0: return None, out.stderr.strip()[:200]
    return json.loads(out.stdout), None

def search(q, n=15):
    from urllib.parse import quote
    ep = "search/issues?" + "&".join(f"{k}={quote(str(v))}" for k,v in {"q":q,"per_page":n,"sort":"updated","order":"desc"}.items())
    for a in range(4):
        try:
            return gh(ep)
        except Exception as e:
            if "rate limit" in str(e).lower() and a<3:
                time.sleep(20*(a+1)); 
            else: raise

QUERIES = {
 "q1_gfi_docs": 'label:"good first issue" label:"documentation" state:open comments:0 stars:>1000 pushed:>2026-09-08 no:assignee',
 "q2_gfi_docs2": 'label:"good first issue" label:"documentation" state:open comments:0 stars:>300 pushed:>2026-09-12 no:assignee',
 "q3_gfi_test": 'label:"good first issue" label:"test" state:open comments:0 stars:>1000 pushed:>2026-09-08 no:assignee',
 "q4_helpwanted_docs": 'label:"help wanted" label:"documentation" state:open comments:0 stars:>1000 pushed:>2026-09-10 no:assignee',
}
seen=set()
found={}
for name,q in QUERIES.items():
    try:
        d,_=search(q)
        print(f"\n### {name}")
        for it in (d or {}).get("items",[]):
            repo=it.get("repository_url","").replace("https://api.github.com/repos/","")
            key=(repo,it["number"])
            if key in seen: 
                print(f"   dup {repo}#{it['number']}")
                continue
            seen.add(key)
            found[key]={"repo":repo,"num":it["number"],"comments":it.get("comments",0),
                        "labels":[l["name"] for l in it.get("labels",[])],"title":it["title"][:85]}
            print(f"   {repo}#{it['number']} c={it.get('comments')} labs={found[key]['labels']} :: {found[key]['title']}")
    except Exception as e:
        print(f"{name} ERR {str(e)[:120]}")
    time.sleep(0.5)

json.dump({f"{k[0]}#{k[1]}":v for k,v in found.items()}, open("/Users/mike/oss-pipeline/state/exact100_hunt.json","w"), indent=2)
print("\nsaved exact100_hunt.json")
