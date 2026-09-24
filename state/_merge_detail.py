import sqlite3, subprocess, json, time

db = sqlite3.connect('/Users/mike/oss-pipeline/state/kpi.db')
c = db.cursor()
for rid, repo, pr in [(12,'adlerqa/wardeniq',32),(42,'chrisalunlloyd2-sudo/mindpalace',81)]:
    res = subprocess.run(['gh','api',f'repos/{repo}/pulls/{pr}','--jq','.merged_at,.merge_commit_sha,.merged_by.login'], capture_output=True, text=True, timeout=40)
    print(f"[{rid}] {repo}#{pr}:")
    print("   ", res.stdout.strip().replace('\n',' | '))
    time.sleep(1.0)