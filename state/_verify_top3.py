import subprocess, json, time
for repo, num in [('OWASP/cve-lite-cli',1000),('meilisearch/meilisearch-rust',800),('serde-rs/serde',1500)]:
    print(f"\n===== {repo}#{num} =====")
    issue = json.loads(subprocess.run(['gh','api',f'repos/{repo}/issues/{num}','--jq','.'],capture_output=True,text=True,timeout=40).stdout)
    print("TITLE:", issue.get('title'))
    print("STATE:", issue.get('state'), "| ASSIGNEE:", issue.get('assignee'))
    print("COMMENTS:", issue.get('comments'))
    print("LABELS:", [l['name'] for l in issue.get('labels',[])])
    print("AUTHOR:", (issue.get('user') or {}).get('login'))
    print("CREATED:", issue.get('created_at'))
    print("BODY (first 700):")
    print((issue.get('body') or '')[:700])
    if issue.get('comments',0) > 0:
        cms = json.loads(subprocess.run(['gh','api',f'repos/{repo}/issues/{num}/comments','--jq','.'],capture_output=True,text=True,timeout=40).stdout)
        print("COMMENT AUTHORS/BODIES:")
        for cm in cms:
            print(f"  [{cm['user']['login']}] {cm['body'][:200]}")
    time.sleep(2)