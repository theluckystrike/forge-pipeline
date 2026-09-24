import sqlite3, json, subprocess, time

db=sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
db.row_factory=sqlite3.Row
rows=[dict(r) for r in db.execute("SELECT id,repo,issue,pr,status,pr_url FROM contributions WHERE status='OPEN' ORDER BY id")]

def gh(endpoint, retries=6):
    for a in range(retries):
        out=subprocess.run(["gh","api",endpoint,"-H","Accept: application/vnd.github+json"],capture_output=True,text=True,timeout=60)
        if out.returncode==0:
            try: return json.loads(out.stdout)
            except: return None
        if "403" in out.stderr or "rate limit" in out.stderr.lower():
            time.sleep(15*(a+1))
        else:
            return None
    return None

print("checking", len(rows), "OPEN PRs")
changed=[]
for r in rows:
    repo,pr = r['repo'], r['pr']
    if not pr:
        print(f"  [SKIP] {r['id']} {repo}#{r['issue']} no-pr")
        continue
    pr_num=str(pr).lstrip('#')
    d=gh(f"repos/{repo}/pulls/{pr_num}")
    if d:
        merged=d.get("merged")
        state=d.get("state")
        head=d.get("head",{}).get("ref","")
        url=d.get("html_url")
        if merged: newst="MERGED"
        elif state=="closed": newst="CLOSED"
        else: newst="OPEN"
        print(f"  [{newst}] {r['id']} {repo}#{pr} head={head}")
        if newst!="OPEN":
            changed.append({**r,"newstatus":newst,"pr_url":url})
    else:
        print(f"  [ERR] {r['id']} {repo}#{pr}")

print("\n=== CHANGED ===")
for c in changed:
    print(f"  {c['repo']}#{c['pr']} -> {c['newstatus']}")
print("total changed:", len(changed))
with open('/Users/mike/oss-pipeline/state/changed_prs.json','w') as f:
    json.dump(changed,f,indent=2)
print("written changed_prs.json len", len(changed))