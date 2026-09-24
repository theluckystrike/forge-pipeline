import subprocess, json, time
from datetime import datetime
def gh(e):
    o=subprocess.run(["gh","api",e],capture_output=True,text=True,timeout=60)
    return json.loads(o.stdout) if o.returncode==0 else None
def score(repo,num):
    r=gh(f"repos/{repo}"); iss=gh(f"repos/{repo}/issues/{num}")
    if not r or not iss: print(f"{repo}#{num} fetch fail"); return
    labels=[l["name"] for l in iss.get("labels",[])]; ll=[l.lower() for l in labels]
    rec=(datetime.utcnow()-datetime.strptime(r["pushed_at"],"%Y-%m-%dT%H:%M:%SZ")).days
    lic=(r.get("license") or {}).get("spdx_id")
    b={}
    b["repo_health"]=15 if r["stargazers_count"]>=1000 else (10 if r["stargazers_count"]>=300 else 5)
    b["issue_valid"]=10 if iss["comments"]==0 else (8 if iss["comments"]<=2 else 0)
    b["issue_scope"]=10 if "good first issue" in ll else (8 if "help wanted" in ll else 5)
    b["recency"]=10 if rec<=14 else (7 if rec<=45 else 0)
    b["license_ok"]=10 if lic in ("MIT","Apache-2.0","BSD-3-Clause","BSD-2-Clause","ISC","MPL-2.0") else 0
    b["assignable"]=10 if not iss.get("assignee") else 0
    body=iss.get("body") or ""
    b["docs_clarity"]=10 if len(body)>200 else (7 if len(body)>80 else 3)
    b["competence"]=10
    b["risk"]=10 if (any(k in ll for k in ("docs","documentation","doc")) or "test" in " ".join(ll)) else 7
    au=(iss.get("user") or {}).get("login")
    b["authenticity"]=5 if au and au!="theluckystrike" else 0
    b["unassigned_now"]=5
    t=min(sum(b.values()),100)
    print(f"{repo}#{num} score={t} stars={r['stargazers_count']} pushed={rec}d lic={lic} c={iss['comments']}")
    print(f"   labs={labels}")
    print(f"   title: {(iss.get('title') or '')[:70]}")
    print(f"   body({len(body)}ch): {body[:120]!r}")
for repo,num in [("shep-pm/shep",300),("munirov/cremniy",300),("C-Accel-Project-Old-Version/old-sdk",300)]:
    score(repo,num); time.sleep(0.4)
