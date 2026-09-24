import json, subprocess, time

def gh_post(endpoint, payload, retries=5):
    for a in range(retries):
        out=subprocess.run(["gh","api","--method","POST",endpoint,"--input","-"],
                           input=json.dumps(payload),capture_output=True,text=True,timeout=60)
        if out.returncode==0:
            try: return json.loads(out.stdout)
            except: return None
        if "403" in out.stderr or "rate limit" in out.stderr.lower():
            time.sleep(12*(a+1))
        else:
            print("ERR", out.stderr[:200]); return None
    return None

repo,num="stellar/stellar-docs",2865
body=("Removed the unsupported rationale in the latest commit. The text now says the "
      "pool share trustline adds 2 and requires two base reserves, without claiming "
      "it holds the two reserve assets.")
payload={"body":body,"in_reply_to":4059009389}
r=gh_post(f"repos/{repo}/pulls/{num}/comments",payload)
if r:
    print("POSTED reply id", r.get("id"), "to", r.get("in_reply_to_id"))
    print("URL", r.get("html_url"))
else:
    print("FAILED to post reply")