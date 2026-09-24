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

for repo,num in [("libredb/libredb-studio",869),("cashubtc/nutshell",500)]:
    print(f"===== {repo}#{num} =====")
    issue=gh(f"repos/{repo}/issues/{num}")
    if not issue: print("  NO ISSUE"); continue
    print("  title:", issue.get("title"))
    print("  state:", issue.get("state"), "| assignees:", [a["login"] for a in issue.get("assignees",[])] or "none")
    print("  created:", issue.get("created_at"))
    print("  body:", (issue.get("body") or "")[:400].replace(chr(10)," / "))
    tl=gh(f"repos/{repo}/issues/{num}/timeline?per_page=30")
    if tl:
        for e in tl:
            if e.get("event") in ("cross-referenced","connected","referenced"):
                print("  REF:", e.get("event"), e.get("source",{}).get("issue",{}).get("html_url"))
    cs=gh(f"repos/{repo}/issues/{num}/comments?per_page=10")
    if cs:
        for c in cs:
            print(f"  CMT {c['user']['login']} [{c['created_at'][:10]}]: {c['body'][:150].replace(chr(10),' ')}")
    print()