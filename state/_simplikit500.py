import subprocess, json, time
repo='toss/react-simplikit'; num=500
res = subprocess.run(['gh','api',f'repos/{repo}/issues/{num}','--jq','.'], capture_output=True, text=True, timeout=40)
issue = json.loads(res.stdout)
print("TITLE:", issue['title'])
print("STATE:", issue['state'], "ASSIGNEE:", issue.get('assignee'))
print("COMMENTS:", issue.get('comments'))
print("LABELS:", [l['name'] for l in issue.get('labels',[])])
print("AUTHOR:", issue.get('user',{}).get('login'))
print("CREATED:", issue.get('created_at'))
print("BODY:", (issue.get('body') or '')[:1500])
print("\n--- COMMENTS ---")
res2 = subprocess.run(['gh','api',f'repos/{repo}/issues/{num}/comments','--jq','.'], capture_output=True, text=True, timeout=40)
for cm in json.loads(res2.stdout):
    print(f"[{cm['user']['login']}] {cm['body'][:300].replace(chr(10),' ')}")
print("\n--- REPO ---")
res3 = subprocess.run(['gh','api',f'repos/{repo}','--jq','.'], capture_output=True, text=True, timeout=40)
r = json.loads(res3.stdout)
print("stars:", r['stargazers_count'], "pushed:", r['pushed_at'], "license:", (r.get('license') or {}).get('spdx_id'), "archived:", r.get('archived'))