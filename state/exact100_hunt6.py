import json, subprocess, time
from datetime import datetime
from urllib.parse import quote

def gh(endpoint, retries=5):
    for a in range(retries):
        out = subprocess.run(["gh","api",endpoint], capture_output=True, text=True, timeout=60)
        if out.returncode == 0:
            try: return json.loads(out.stdout), None
            except Exception as e: return None, str(e)[:80]
        if "rate limit" in out.stderr.lower() or "403" in out.stderr:
            time.sleep(25*(a+1))
        else:
            return None, out.stderr[:200]
    return None, "rate-limit giveup"

def search(q, n=40):
    ep = "search/issues?" + "&".join(f"{k}={quote(str(v))}" for k,v in {"q":q,"per_page":n,"sort":"updated","order":"desc"}.items())
    return gh(ep)

def score(repo, num, title):
    r, err = gh(f"repos/{repo}")
    if err: return None
    i, err2 = gh(f"repos/{repo}/issues/{num}")
    if err2: return None
    stars = r.get("stargazers_count",0)
    pushed = r.get("pushed_at","")
    days = (datetime.utcnow() - datetime.strptime(pushed,"%Y-%m-%dT%H:%M:%SZ")).days if pushed else 999
    lic = (r.get("license") or {}).get("spdx_id")
    labels = [l["name"].lower() for l in i.get("labels",[])]
    comments = i.get("comments",0)
    assignee = i.get("assignee")
    body = (i.get("body") or "")
    author = i.get("user",{}).get("login")
    state = i.get("state")
    b = {}
    b["repo_health"] = 15 if stars>=1000 else (10 if stars>=300 else 5)
    b["issue_valid"] = 10 if comments==0 else (8 if comments<=2 else 0)
    b["issue_scope"] = 10 if "good first issue" in labels else (8 if "help wanted" in labels else 5)
    b["recency"] = 10 if days<=14 else (7 if days<=45 else 0)
    b["license_ok"] = 10 if lic in ("MIT","Apache-2.0","BSD-3-Clause","BSD-2-Clause","ISC","MPL-2.0") else 0
    b["assignable"] = 10 if not assignee else 0
    b["docs_clarity"] = 10 if len(body)>200 else (7 if len(body)>80 else 3)
    b["competence"] = 10
    b["risk"] = 10 if any(k in labels for k in ("docs","documentation","doc")) or "test" in " ".join(labels) else 7
    b["authenticity"] = 5 if author and author!="theluckystrike" else 0
    b["unassigned_now"] = 5 if state=="open" and not assignee and comments<=3 else 0
    total = min(sum(b.values()),100)
    return {"stars":stars,"days":days,"lic":lic,"comments":comments,"labels":labels,"score":total,"breakdown":b}

# Broad hunt for good-first-issue docs tasks, verify stars via repo API
QUERIES = {
 "b1": 'label:"good first issue" label:"documentation" state:open comments:0..2 no:assignee',
 "b2": 'label:"good first issue" label:"docs" state:open comments:0..2 no:assignee',
}
results=[]
seen=set()
for name,q in QUERIES.items():
    print(f"\n### {name}")
    d,err = search(q)
    if err: print(f"   search ERR {err}"); time.sleep(2); continue
    items = (d or {}).get("items",[])
    print(f"   {len(items)} raw hits")
    for it in items:
        repo=it.get("repository_url","").replace("https://api.github.com/repos/","")
        key=(repo,it["number"])
        if key in seen: continue
        seen.add(key)
        s = score(repo, it["number"], it["title"])
        if s and s["score"] >= 90:
            results.append((repo,it["number"],it["title"],s))
            print(f"   SCORE={s['score']} {repo}#{it['number']} stars={s['stars']} days={s['days']} c={s['comments']} :: {it['title'][:60]}")
        time.sleep(0.3)
    time.sleep(2)

print("\n\n=== TOP RESULTS (>=90) ===")
results.sort(key=lambda x:-x[3]["score"])
for repo,num,title,s in results[:15]:
    print(f"  {s['score']} {repo}#{num} stars={s['stars']} days={s['days']} lic={s['lic']} c={s['comments']} labs={s['labels']} :: {title[:55]}")