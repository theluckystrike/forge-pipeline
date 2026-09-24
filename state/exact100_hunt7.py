import json, subprocess, time, re
from datetime import datetime, timezone
from urllib.parse import quote

def gh(endpoint, retries=5):
    for a in range(retries):
        out = subprocess.run(["gh","api",endpoint], capture_output=True, text=True, timeout=60)
        if out.returncode == 0:
            try: return json.loads(out.stdout), None
            except Exception as e: return None, str(e)[:80]
        if "rate limit" in out.stderr.lower() or "403" in out.stderr:
            time.sleep(30*(a+1))
        else:
            return None, out.stderr[:200]
    return None, "rate-limit giveup"

def search(q, n=50, sort="updated", order="desc"):
    ep = "search/issues?" + "&".join(f"{k}={quote(str(v))}" for k,v in {"q":q,"per_page":n,"sort":sort,"order":order}.items())
    return gh(ep)

def utcnow():
    return datetime.now(timezone.utc)

CLAIM = re.compile(r"(picking this up|l?d like to work|i'll take|i will take|working on this|assign me|claiming|on it\b|taking this|i take this|starting on)", re.I)

def score(repo, num):
    r, err = gh(f"repos/{repo}")
    if err: return None, err
    i, err2 = gh(f"repos/{repo}/issues/{num}")
    if err2: return None, err2
    stars = r.get("stargazers_count",0)
    pushed = r.get("pushed_at","")
    days = (datetime.strptime(pushed,"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) - utcnow()).days if pushed else 999
    days = abs(days)
    lic = (r.get("license") or {}).get("spdx_id")
    labels = [l["name"].lower() for l in i.get("labels",[])]
    comments = i.get("comments",0)
    assignee = i.get("assignee")
    body = (i.get("body") or "")
    author = i.get("user",{}).get("login")
    state = i.get("state")
    if state!="open" or assignee or i.get("pull_request"): return None,"not-open"
    # contention scan on comments
    cs, cerr = gh(f"repos/{repo}/issues/{num}/comments")
    contested=False; recent_claim=None; oldest_activity=None
    if not cerr:
        now=utcnow()
        dates=[datetime.strptime(x['created_at'][:19]+"Z","%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) for x in cs]
        if dates: oldest_activity=min(dates)
        for x in cs:
            d=datetime.strptime(x['created_at'][:19]+"Z","%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            if CLAIM.search(x['body'] or "") and (now-d).days<=30:
                contested=True; recent_claim=x['user']['login']; break
    b = {}
    b["repo_health"] = 15 if stars>=1000 else (10 if stars>=300 else 5)
    b["issue_valid"] = 10 if comments==0 else (8 if comments<=2 else 0)
    b["issue_scope"] = 10 if "good first issue" in labels else (8 if "help wanted" in labels else 5)
    b["recency"] = 10 if days<=14 else (7 if days<=45 else 0)
    b["license_ok"] = 10 if lic in ("MIT","Apache-2.0","BSD-3-Clause","BSD-2-Clause","ISC","MPL-2.0") else 0
    b["assignable"] = 10 if not assignee else 0
    b["docs_clarity"] = 10 if len(body)>200 else (7 if len(body)>80 else 3)
    b["competence"] = 10
    b["risk"] = 10 if (any(k in labels for k in ("docs","documentation","doc")) or "test" in " ".join(labels)) else 7
    b["authenticity"] = 5 if author and author!="theluckystrike" else 0
    b["unassigned_now"] = 5
    total = min(sum(b.values()),100)
    return {"stars":stars,"days":days,"lic":lic,"comments":comments,"labels":labels,"score":total,
            "breakdown":b,"contested":contested,"recent_claim":recent_claim,"oldest_activity":oldest_activity}, None

QUERIES = [
 'label:"good first issue" label:"documentation" state:open comments:<=2 no:assignee',
 'label:"good first issue" label:"docs" state:open comments:<=2 no:assignee',
 'label:"good first issue" label:"doc" state:open comments:<=2 no:assignee',
 'label:"good first issue" label:"documentation" state:open no:assignee',
]
results={}
for i,q in enumerate(QUERIES):
    d,err = search(q)
    if err: print(f"### q{i} ERR {err}"); time.sleep(2); continue
    items=(d or {}).get("items",[])
    print(f"### q{i} {len(items)} hits")
    for it in items:
        repo=it.get("repository_url","").replace("https://api.github.com/repos/","")
        num=it["number"]
        res,err=score(repo,num)
        if res and res["score"]>=95:
            key=f"{repo}#{num}"
            if key not in results:
                results[key]=res
                results[key]["repo"]=repo; results[key]["num"]=num; results[key]["title"]=it["title"][:70]
                flags="CONTENDED!" if res["contested"] else "UNCONTESTED"
                print(f"   [{flags}] {res['score']} {repo}#{num} stars={res['stars']} days={res['days']} c={res['comments']} :: {res['title']}")
        time.sleep(0.2)
    time.sleep(2)

print("\n=== UNCONTESTED high-score candidates ===")
un=[]
for k,v in results.items():
    if not v["contested"]: un.append(v)
un.sort(key=lambda x:-x["score"])
for v in un[:20]:
    print(f"  [{v['score']}] {v['repo']}#{v['num']} stars={v['stars']} days={v['days']} lic={v['lic']} c={v['comments']} labs={v['labels']} :: {v['title']}")