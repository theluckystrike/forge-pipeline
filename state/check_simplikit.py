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

repo,num="toss/react-simplikit",500
print(f"===== {repo}#{num} =====")
issue=gh(f"repos/{repo}/issues/{num}")
if not issue:
    print("  NO ISSUE"); raise SystemExit
print("  title:", issue.get("title"))
print("  state:", issue.get("state"), "| assignees:", [a["login"] for a in issue.get("assignees",[])] or "none")
print("  labels:", [l["name"] for l in issue.get("labels",[])])
print("  comments:", issue.get("comments"), "| created:", issue.get("created_at"))
b=issue.get("body") or ""
print("  body_len:", len(b))
print("  body:", b[:300].replace(chr(10)," / "))
# repo info
r=gh(f"repos/{repo}")
if r:
    print("  repo stars:", r.get("stargazers_count"), "| pushed:", r.get("pushed_at"), "| license:", (r.get("license") or {}).get("spdx_id"))
# timeline for contention
tl=gh(f"repos/{repo}/issues/{num}/timeline?per_page=30")
if tl:
    for e in tl:
        if e.get("event") in ("cross-referenced","connected","referenced"):
            print("  REF:", e.get("event"), e.get("source",{}).get("issue",{}).get("html_url"))
# comments
cs=gh(f"repos/{repo}/issues/{num}/comments?per_page=10")
if cs:
    for c in cs:
        print(f"  CMT {c['user']['login']} [{c['created_at'][:10]}]: {c['body'][:120].replace(chr(10),' ')}")