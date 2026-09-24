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

repo="reservoirpy"
print("=== repo tree (docs) ===")
tree=gh(f"repos/{repo}/git/trees/main?recursive=1")
if tree:
    paths=[t["path"] for t in tree.get("tree",[]) if "doc" in t["path"].lower() or "tutorial" in t["path"].lower() or "readme" in t["path"].lower()]
    for p in paths[:40]: print("  ", p)
else:
    print("  tree failed, trying default branch")
    r=gh(f"repos/{repo}")
    print("  default_branch:", r.get("default_branch") if r else "?")
print("\n=== issue #218 full body ===")
issue=gh(f"repos/{repo}/issues/218")
if issue: print(" ", issue.get("body"))