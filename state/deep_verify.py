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

CANDIDATES=[
  ("apache/apisix",13395),
  ("NVIDIA/NeMo-Retriever",16),
  ("numba/numba",2598),
]
for repo,num in CANDIDATES:
    print(f"\n===== {repo}#{num} =====")
    issue=gh(f"repos/{repo}/issues/{num}")
    if not issue:
        print("  NO ISSUE (PR?)"); continue
    print("  title:", issue.get("title"))
    print("  state:", issue.get("state"), "| assignees:", [a["login"] for a in issue.get("assignees",[])] or "none")
    print("  labels:", [l["name"] for l in issue.get("labels",[])])
    print("  comments:", issue.get("comments"))
    print("  created:", issue.get("created_at"))
    # body length + first 200 chars
    b=issue.get("body") or ""
    print("  body_len:", len(b), "::", b[:200].replace(chr(10)," / "))
    # check PRs referencing this issue (contention)
    prs=gh(f"repos/{repo}/issues/{num}/timeline?per_page=30")
    if prs:
        refs=[e for e in prs if e.get("event") in ("cross-referenced","connected","referenced")]
        for e in refs:
            src=e.get("source",{}).get("issue",{}).get("html_url")
            print("  REF:", e.get("event"), src)
    # last few comments
    cs=gh(f"repos/{repo}/issues/{num}/comments?per_page=10")
    if cs:
        for c in cs[-3:]:
            print(f"  CMT {c['user']['login']} [{c['created_at'][:10]}]: {c['body'][:130].replace(chr(10),' ')}")
    time.sleep(1)