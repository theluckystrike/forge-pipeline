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

# Check apache/apisix#13395: is Gagan-TW's claim stale? any PR from them?
print("=== apache/apisix#13395 full comments ===")
cs=gh("repos/apache/apisix/issues/13395/comments?per_page=20")
for c in cs or []:
    print(f"  {c['user']['login']} [{c['created_at'][:10]}]: {c['body'][:200].replace(chr(10),' ')}")

print("\n=== PRs by Gagan-TW in apisix ===")
prs=gh("search/issues?q=repo:apache/apisix+author:Gagan-TW+type:pr&per_page=10")
if prs:
    for i in prs.get("items",[]):
        print(f"  PR#{i['number']} [{i['state']}] {i['title'][:60]}")

print("\n=== PRs referencing #13395 (all) ===")
tl=gh("repos/apache/apisix/issues/13395/timeline?per_page=50")
if tl:
    for e in tl:
        if e.get("event")=="cross-referenced":
            u=e.get("source",{}).get("issue",{}).get("html_url","")
            print("  ",u)