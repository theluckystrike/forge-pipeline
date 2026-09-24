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

# covering PRs to check state
CHECKS=[
  ("apache/apisix",13396,"covering PR for #13395"),
  ("apache/apisix",13418,"covering PR for #10893"),
  ("apache/apisix",10966,"covering PR for #10893"),
  ("NVIDIA/NeMo-Retriever",2333,"covering PR for #16"),
  ("NVIDIA/NeMo-Retriever",2404,"covering PR for #16"),
  ("numba/numba",10788,"covering PR for #3639"),
  ("numba/numba",2724,"covering PR for #2598"),
  ("The-PR-Agent/pr-agent",0,"check PRs for #3536"),
]
for repo,num,note in CHECKS:
    if num==0:
        # search PRs referencing #3536
        prs=gh(f"repos/{repo}/pulls?state=all&per_page=100")
        if prs:
            for p in prs:
                if "3536" in (p.get("body") or ""):
                    print(f"  {repo} PR#{p['number']} [{p['state']}] {p['title'][:60]}")
        continue
    pr=gh(f"repos/{repo}/pulls/{num}")
    if pr:
        print(f"  {repo}#{num} [{pr.get('state')}] merged={pr.get('merged')} :: {pr.get('title','')[:60]}")
    else:
        print(f"  {repo}#{num} NOT FOUND")
    time.sleep(0.5)