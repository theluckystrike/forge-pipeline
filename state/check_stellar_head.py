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
pr=gh(f"repos/{repo}/pulls/{num}")
head=pr["head"]["ref"]; sha=pr["head"]["sha"]
print(f"head={head} sha={sha}")
for path in ["docs/data/analytics/hubble/data-catalog/data-dictionary/bronze/accounts.mdx",
             "docs/data/analytics/hubble/data-catalog/data-dictionary/silver/accounts-snapshot.mdx"]:
    print(f"\n=== {path} ===")
    content=gh(f"repos/{repo}/contents/{path}?ref={head}")
    if content and "content" in content:
        import base64
        txt=base64.b64decode(content["content"]).decode()
        # print lines mentioning num_subentries / pool share / two sides
        for i,line in enumerate(txt.split("\n"),1):
            low=line.lower()
            if "num_subentries" in low or "pool share" in low or "pool-share" in low or "two sides" in low or "two reserve" in low or "holds" in low:
                print(f"  {i}: {line[:160]}")
    else:
        print("  (no content)", content if content else "None")