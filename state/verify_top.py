"""L2 verify + exact-100 rescore of widened-discovery top candidates."""
import subprocess, json, time
from datetime import datetime

def gh(endpoint):
    out = subprocess.run(["gh","api",endpoint], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return None, out.stderr.strip()[:200]
    return json.loads(out.stdout), None

ACCT = "theluckystrike"
CAND = [
    ("GoogleCloudPlatform/kubectl-ai", 500),
    ("FusionAuth/fusionauth-site", 2000),
    ("Bike4Mind/bike4mind", 2000),
    ("aesara-devs/aesara", 500),
    ("gnn-tracking/gnn_tracking", 500),
    ("pulp/pulpcore", 2000),
    ("MarSeventh/CloudFlare-ImgBed", 500),
    ("Molara-Lab/Molara", 500),
    ("RealDevSquad/website-backend", 500),
]
PERM_LIC = ("MIT","Apache-2.0","BSD-3-Clause","BSD-2-Clause","ISC","MPL-2.0")

def score(repo, num, r, issue, labels):
    b={}
    b["repo_health"]= 15 if r["stargazers_count"]>=1000 else (10 if r["stargazers_count"]>=300 else 5)
    b["issue_valid"]= 10 if issue["comments"]==0 else (8 if issue["comments"]<=2 else 0)
    b["issue_scope"]= 10 if "good first issue" in labels else (8 if "help wanted" in labels else 5)
    rec = (datetime.utcnow()-datetime.strptime(r["pushed_at"],"%Y-%m-%dT%H:%M:%SZ")).days
    b["recency"]= 10 if rec<=14 else (7 if rec<=45 else 0)
    lic = (r.get("license") or {}).get("spdx_id")
    b["license_ok"]= 10 if lic in PERM_LIC else 0
    b["assignable"]= 10 if not issue.get("assignee") else 0
    body=issue.get("body") or ""
    b["docs_clarity"]= 10 if len(body)>200 else (7 if len(body)>80 else 3)
    b["competence"]= 10
    ll=[l.lower() for l in labels]
    b["risk"]= 10 if ("docs" in ll or "documentation" in ll or "test" in " ".join(ll)) else 7
    auth = (issue.get("user") or {}).get("login")
    b["authenticity"]= 5 if auth and auth.lower()!=ACCT else 0
    b["unassigned_now"]= 5
    total=sum(b.values())
    return total, b, rec, lic

for repo, num in CAND:
    r, e1 = gh(f"repos/{repo}")
    if e1:
        print(f"{repo}#{num}: repo ERR {e1}"); continue
    issue, e2 = gh(f"repos/{repo}/issues/{num}")
    if e2:
        print(f"{repo}#{num}: issue ERR {e2}"); continue
    if issue.get("pull_request"):
        print(f"{repo}#{num}: is PR not issue"); continue
    labels=[l["name"] for l in issue.get("labels",[])]
    if issue.get("assignee"):
        print(f"{repo}#{num}: ASSIGNED to {issue['assignee'].get('login')}"); time.sleep(0.3); continue
    t,b,rec,lic = score(repo,num,r,issue,labels)
    print(f"\n{repo}#{num} score={t} (pushed={rec}d, stars={r['stargazers_count']}, lic={lic}, comments={issue['comments']})")
    print(f"   title: {(issue.get('title') or '')[:70]}")
    print(f"   labels: {labels}")
    print(f"   breakdown: {b}")
    print(f"   body({len(issue.get('body') or '')}ch): {(issue.get('body') or '')[:160]!r}")
    time.sleep(0.3)
