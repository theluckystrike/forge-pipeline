import json, subprocess, time

def gh(endpoint,retries=5):
    for a in range(retries):
        out=subprocess.run(["gh","api",endpoint,"-H","Accept: application/vnd.github+json"],capture_output=True,text=True,timeout=60)
        if out.returncode==0:
            try: return json.loads(out.stdout)
            except: return None
        if "403" in out.stderr or "rate limit" in out.stderr.lower():
            time.sleep(12*(a+1))
        else: return None
    return None

repo,num="stellar/stellar-docs",2865
print("=== PR review comments (full) ===")
revs=gh(f"repos/{repo}/pulls/{num}/comments")
if revs:
    for c in sorted(revs,key=lambda x:x.get("created_at","")):
        print(f"\n--- {c['user']['login']} [{c['created_at']}] path={c.get('path')} line={c.get('line')} ---")
        print((c.get('body') or '')[:600])
print("\n=== PR reviews (non-techstate) ===")
reviews=gh(f"repos/{repo}/pulls/{num}/reviews")
if reviews:
    for r in reviews:
        if r.get("user",{}).get("login")!="theluckystrike":
            print(f"  {r['user']['login']} state={r['state']} [{r.get('submitted_at','')}] :: {(r.get('body') or '')[:120]}")
# latest state of PR files - show a relevant snippet of which file/line
print("\n=== PR files ===")
files=gh(f"repos/{repo}/pulls/{num}/files")
if files:
    for f in files[:10]:
        print(f"  {f['filename']} +{f['additions']} -{f['deletions']}")