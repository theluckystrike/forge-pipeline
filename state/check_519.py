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

repo="toss/react-simplikit"
print("=== PR #519 ===")
pr=gh(f"repos/{repo}/pulls/519")
if pr:
    print("  title:", pr.get("title"))
    print("  state:", pr.get("state"), "| merged:", pr.get("merged"))
    print("  user:", pr.get("user",{}).get("login"))
    print("  body:", (pr.get("body") or "")[:300])
    print("  head:", pr.get("head",{}).get("ref"))
    print("  files/commits:", pr.get("changed_files"), "/", pr.get("commits"))
print("\n=== issue #500 event of PR 519 ===")
# does #519 close #500?
print("\n=== check if #519 is theLuckystrike's ===")