import sqlite3, subprocess, json, time

db = sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
c = db.cursor()
rows = c.execute("SELECT id, repo, pr, pr_url, status FROM contributions WHERE status='OPEN'").fetchall()
print(f"OPEN rows to recheck: {len(rows)}")
print("="*70)

for rid, repo, pr, pr_url, status in rows:
    if not pr or not str(pr).lstrip('#').isdigit():
        print(f"[{rid}] {repo} pr={pr} (no numeric PR, skip)")
        continue
    pn = str(pr).lstrip('#')
    ep = f"repos/{repo}/pulls/{pn}"
    res = subprocess.run(['gh','api',ep,'--jq','.state,.merged_at,.merged'], capture_output=True, text=True, timeout=40)
    if res.returncode != 0:
        print(f"[{rid}] {repo}#{pn} API-ERR {res.stderr[:80]}")
        continue
    lines = res.stdout.strip().split('\n')
    state = lines[0] if lines else '?'
    merged_at = lines[1] if len(lines)>1 else ''
    merged = lines[2] if len(lines)>2 else ''
    new_status = 'MERGED' if (state=='closed' and merged=='true') else ('CLOSED' if state=='closed' else 'OPEN')
    flag = '  <-- CHANGE' if new_status != status else ''
    print(f"[{rid}] {repo}#{pn} state={state} merged={merged} -> {new_status}{flag}")
    time.sleep(1.0)