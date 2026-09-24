import json, subprocess, time
from datetime import datetime

def gh(endpoint):
    out = subprocess.run(["gh","api",endpoint], capture_output=True, text=True, timeout=60)
    if out.returncode != 0: return None, out.stderr.strip()[:200]
    return json.loads(out.stdout), None

# Candidates to verify against the exact-100 rubric
CANDS = [
    ("pangeo-data/pangeo-docker-images", 500),
    ("GoogleCloudPlatform/kubectl-ai", 500),
    ("biocore/empress", 500),
    ("Molara-Lab/Molara", 500),
    ("RealDevSquad/website-backend", 500),
    ("shep-pm/shep", 300),
    ("C-Accel-Project-Old-Version/old-sdk", 300),
]

def score(repo, num):
    r, err = gh(f"repos/{repo}")
    if err: print(f"{repo}#{num} repo ERR {err}"); return
    i, err2 = gh(f"repos/{repo}/issues/{num}")
    if err2: print(f"{repo}#{num} issue ERR {err2}"); return
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
    print(f"\n{repo}#{num} :: {i.get('title','')[:60]}")
    print(f"  stars={stars} pushed_days={days} lic={lic} comments={comments} state={state} author={author}")
    print(f"  labels={labels}")
    print(f"  SCORE={total}  breakdown={b}")

for repo,num in CANDS:
    try:
        score(repo,num)
    except Exception as e:
        print(f"{repo}#{num} ERR {str(e)[:150]}")
    time.sleep(0.5)
