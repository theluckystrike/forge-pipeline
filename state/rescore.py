import json, subprocess, time

def gh(endpoint,retries=5):
    for a in range(retries):
        out=subprocess.run(["gh","api",endpoint,"-H","Accept: application/vnd.github+json"],capture_output=True,text=True,timeout=60)
        if out.returncode==0 and out.stdout.strip():
            try: return json.loads(out.stdout)
            except: return None
        if "403" in out.stderr or "rate limit" in out.stderr.lower() or "secondary" in out.stderr.lower():
            time.sleep(10*(a+1))
        elif out.returncode!=0:
            time.sleep(3)
    return None

def score(repo,num):
    issue=gh(f"repos/{repo}/issues/{num}")
    r=gh(f"repos/{repo}")
    if not issue or not r: return None
    stars=r.get("stargazers_count",0)
    pushed=r.get("pushed_at","")
    lic=(r.get("license") or {}).get("spdx_id","")
    labels=[l["name"].lower() for l in issue.get("labels",[])]
    comments=issue.get("comments",0)
    body=issue.get("body") or ""
    assignees=issue.get("assignees",[])
    # rubric
    repo_health=15 if stars>=300 else (10 if stars>=100 else 5)
    issue_valid=10 if comments==0 else (8 if comments<=2 else 5)
    issue_scope=10 if any("good first" in l for l in labels) else 5
    # recency
    from datetime import datetime
    try:
        pd=datetime.fromisoformat(pushed.replace("Z","+00:00"))
        days=(datetime.now().astimezone()-pd).days
    except: days=999
    recency=10 if days<=14 else (7 if days<=45 else (3 if days<=90 else 0))
    license_ok=10 if lic in ("MIT","Apache-2.0","BSD-3-Clause","BSD-2-Clause","MPL-2.0","ISC") else 5
    assignable=10 if not assignees else 0
    docs_clarity=10 if len(body)>200 else 5
    competence=10
    risk=10 if any("doc" in l or "test" in l for l in labels) else 7
    authenticity=5
    unassigned_now=5 if not assignees else 0
    total=repo_health+issue_valid+issue_scope+recency+license_ok+assignable+docs_clarity+competence+risk+authenticity+unassigned_now
    return dict(repo=repo,num=num,stars=stars,days=days,comments=comments,labels=labels,lic=lic,total=min(total,100),
                rh=repo_health,iv=issue_valid,isc=issue_scope,rec=recency,lo=license_ok,asg=assignable,dc=docs_clarity,risk=risk)

cands=[("reservoirpy/reservoirpy",218),("libredb/libredb-studio",869),("toss/react-simplikit",500),
       ("cashubtc/nutshell",500),("marqo-ai/marqo",500),("shep-pm/shep",300)]
for repo,num in cands:
    s=score(repo,num)
    if s: print(f"{s['repo']}#{s['num']} total={s['total']} stars={s['stars']} days={s['days']} c={s['comments']} labels={s['labels']} lic={s['lic']} [rh={s['rh']} iv={s['iv']} isc={s['isc']} rec={s['rec']} lo={s['lo']} asg={s['asg']} dc={s['dc']} risk={s['risk']}]")
    else: print(f"{repo}#{num} ERROR")