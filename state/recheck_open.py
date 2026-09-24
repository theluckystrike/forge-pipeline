import sqlite3, json, subprocess, sys

DB = '/Users/mike/oss-pipeline/state/kpi.db'
con = sqlite3.connect(DB)
cur = con.cursor()

def gh(endpoint):
    out = subprocess.run(['gh','api',endpoint], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return None, out.stderr.strip()[:200]
    return json.loads(out.stdout), None

# All OPEN contributions with a pr_url
rows = cur.execute(
    "SELECT id, repo, issue, pr, status, pr_url FROM contributions WHERE status='OPEN' AND pr_url IS NOT NULL"
).fetchall()
print(f"OPEN rows with pr_url: {len(rows)}")
print("="*80)

for rid, repo, issue, pr, status, pr_url in rows:
    # extract PR number from url
    prnum = pr_url.rstrip('/').split('/')[-1]
    data, err = gh(f"repos/{repo}/pulls/{prnum}")
    if err:
        print(f"[{rid}] {repo}#{prnum}: API ERROR {err}")
        continue
    state = data.get('state')
    merged = data.get('merged')
    mergeable = data.get('mergeable_state')
    print(f"[{rid}] {repo}#{prnum} state={state} merged={merged} mergeable={mergeable}")
