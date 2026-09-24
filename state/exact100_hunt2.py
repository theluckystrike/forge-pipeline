import json, subprocess, time
from datetime import datetime
from urllib.parse import quote

def gh(endpoint):
    out = subprocess.run(["gh","api",endpoint], capture_output=True, text=True, timeout=60)
    if out.returncode != 0: return None, out.stderr.strip()[:200]
    return json.loads(out.stdout), None

def search(q, n=20):
    ep = "search/issues?" + "&".join(f"{k}={quote(str(v))}" for k,v in {"q":q,"per_page":n,"sort":"updated","order":"desc"}.items())
    for a in range(5):
        try:
            return gh(ep)
        except Exception as e:
            if "rate limit" in str(e).lower() and a<4:
                time.sleep(25*(a+1))
            else: raise

# Exact-100 profile: high stars, fresh, 0 comments, docs+good-first-issue, permissive
QUERIES = {
 "x1": 'label:"good first issue" label:"documentation" state:open comments:0 stars:>1000 pushed:>2026-09-10 no:assignee',
 "x2": 'label:"good first issue" label:"documentation" state:open comments:0 stars:>2000 pushed:>2026-09-05 no:assignee',
 "x3": 'label:"good first issue" label:"docs" state:open comments:0 stars:>1000 pushed:>2026-09-10 no:assignee',
 "x4": 'label:"good first issue" label:"documentation" state:open comments:0 stars:>5000 pushed:>2026-09-01 no:assignee',
 "x5": 'label:"good first issue" label:"test" state:open comments:0 stars:>1000 pushed:>2026-09-10 no:assignee',
}
seen=set()
for name,q in QUERIES.items():
    try:
        d,_=search(q)
        print(f"\n### {name}")
        for it in (d or {}).get("items",[]):
            repo=it.get("repository_url","").replace("https://api.github.com/repos/","")
            key=(repo,it["number"])
            if key in seen: continue
            seen.add(key)
            print(f"   {repo}#{it['number']} c={it.get('comments')} labs={[l['name'] for l in it.get('labels',[])]} :: {it['title'][:75]}")
    except Exception as e:
        print(f"{name} ERR {str(e)[:120]}")
    time.sleep(0.5)
