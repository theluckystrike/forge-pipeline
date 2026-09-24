import json, subprocess, time
from urllib.parse import quote

def gh(endpoint, retries=6):
    for a in range(retries):
        out = subprocess.run(["gh","api",endpoint,"-H","Accept: application/vnd.github+json"], capture_output=True, text=True, timeout=60)
        if out.returncode == 0:
            try:
                return json.loads(out.stdout), None
            except Exception as e:
                return None, f"parse {str(e)[:80]}"
        err = out.stderr
        if "secondary rate limit" in err.lower() or "403" in err:
            wait = 30*(a+1)
            print(f"    [backoff {wait}s] {err[:60]}")
            time.sleep(wait)
        else:
            return None, err[:200]
    return None, "gave up on rate limit"

def search(q, n=25):
    ep = "search/issues?" + "&".join(f"{k}={quote(str(v))}" for k,v in {"q":q,"per_page":n,"sort":"updated","order":"desc"}.items())
    return gh(ep)

QUERIES = {
 "a1": 'label:"good first issue" label:"documentation" state:open comments:0..2 stars:>1000 pushed:>2026-08-20 no:assignee',
 "a2": 'label:"good first issue" label:"docs" state:open comments:0..2 stars:>1000 pushed:>2026-08-20 no:assignee',
 "a3": 'label:"good first issue" label:"documentation" state:open comments:0..2 stars:>3000 pushed:>2026-07-01 no:assignee',
}
seen=set()
for name,q in QUERIES.items():
    print(f"\n### {name}  [{q}]")
    d,err = search(q)
    if err: print(f"   ERR {err}"); time.sleep(2); continue
    for it in (d or {}).get("items",[]):
        repo=it.get("repository_url","").replace("https://api.github.com/repos/","")
        key=(repo,it["number"])
        if key in seen: continue
        seen.add(key)
        print(f"   {repo}#{it['number']} c={it.get('comments')} labs={[l['name'] for l in it.get('labels',[])]} :: {it['title'][:75]}")
    time.sleep(1)
