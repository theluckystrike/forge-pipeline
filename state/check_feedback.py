import json, subprocess, time

TRACKED=[("Comfy-Org/ComfyUI_frontend",18234),("stellar/stellar-docs",2865),
         ("cloudnative-pg/plugin-barman-cloud",1108),("Qiskit/documentation",5676),
         ("calyxir/calyx",2724),("domWalters/mkdocs-to-pdf",115)]

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

def recent(login):
    return login not in ("theluckystrike",)

for repo,num in TRACKED:
    print(f"\n=== {repo}#{num} ===")
    # review comments
    revs=gh(f"repos/{repo}/pulls/{num}/comments")
    if revs:
        # show the most recent non-self review comment
        comments=sorted(revs,key=lambda x:x.get("created_at",""),reverse=True)
        for c in comments[:4]:
            if recent(c.get("user",{}).get("login")):
                print(f"  REVIEW {c['user']['login']} [{c['created_at']}] :: {(c.get('body') or '')[:180]}")
    # issue comments
    ics=gh(f"repos/{repo}/issues/{num}/comments")
    if ics:
        comments=sorted(ics,key=lambda x:x.get("created_at",""),reverse=True)
        for c in comments[:4]:
            if recent(c.get("user",{}).get("login")):
                print(f"  ISSCM {c['user']['login']} [{c['created_at']}] :: {(c.get('body') or '')[:180]}")
    # reviews (approvals)
    reviews=gh(f"repos/{repo}/pulls/{num}/reviews")
    if reviews:
        for r in reviews[-3:]:
            if r.get("state") in ("CHANGES_REQUESTED","APPROVED") and recent(r.get("user",{}).get("login")):
                print(f"  REVIEWSTATE {r['user']['login']} [{r['state']}] [{r.get('submitted_at')}]")
    time.sleep(1)