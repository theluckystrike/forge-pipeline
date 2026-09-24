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
revs=gh(f"repos/{repo}/pulls/{num}/comments")
if revs:
    for c in revs:
        if c["user"]["login"]=="Copilot" and "causal explanation is inaccurate" in (c.get("body") or ""):
            print(f"id={c['id']} path={c['path']} created={c['created_at']} in_reply_to={c.get('in_reply_to_id')}")