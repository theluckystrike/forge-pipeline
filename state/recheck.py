import sqlite3, subprocess, json, time

con = sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
cur = con.cursor()
rows = cur.execute("SELECT id, repo, issue, pr, status, pr_url FROM contributions WHERE status='OPEN'").fetchall()

def gh_api(endpoint):
    out = subprocess.run(["gh","api",endpoint], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return None, out.stderr.strip()[:200]
    return json.loads(out.stdout), None

print("=== MERGE-STATE RECHECK of OPEN contributions ===")
changes = []
for rid, repo, issue, pr, status, pr_url in rows:
    if not pr:
        continue
    # PR number may be like '#68' string
    prnum = str(pr).lstrip('#')
    prurl = pr_url
    # derive repo from pr_url fallback
    data, err = gh_api(f"repos/{repo}/pulls/{prnum}")
    time.sleep(0.4)
    if err:
        print(f"row {rid} {repo}#{prnum}: ERR {err}")
        continue
    state = data.get("state")
    merged = data.get("merged")
    print(f"row {rid} {repo}#{prnum}: state={state} merged={merged}")
    if state == "closed" and merged:
        changes.append((rid, repo, prnum, "MERGED"))
    elif state == "closed":
        changes.append((rid, repo, prnum, "CLOSED"))
    elif state == "open":
        # check draft/review state briefly
        pass

print()
print("=== CHANGES ===")
for c in changes:
    print(c)
    cur.execute("UPDATE contributions SET status=? WHERE id=?", (c[3], c[0]))
con.commit()
print("DB updated. Total flips:", len(changes))
con.close()
