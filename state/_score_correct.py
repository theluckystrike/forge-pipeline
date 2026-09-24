import subprocess, json, sys
from datetime import datetime
sys.path.insert(0, '/Users/mike/oss-pipeline')
from pipeline import score_candidate, ACCOUNT

def score_repo(repo, num):
    issue = json.loads(subprocess.run(['gh','api',f'repos/{repo}/issues/{num}','--jq','.'],capture_output=True,text=True,timeout=40).stdout)
    r = json.loads(subprocess.run(['gh','api',f'repos/{repo}','--jq','.'],capture_output=True,text=True,timeout=40).stdout)
    days = (datetime.utcnow() - datetime.strptime(r['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')).days
    c = {
        'stars': r['stargazers_count'],
        'comments': issue.get('comments',0),
        'labels': [l['name'] for l in issue.get('labels',[])],
        'pushed_days_ago': days,
        'license': (r.get('license') or {}).get('spdx_id'),
        'assignee': issue.get('assignee'),
        'issue_body': (issue.get('body') or '')[:2000],
        'issue_author': (issue.get('user') or {}).get('login'),
        'verified': True,
    }
    s, b = score_candidate(c)
    print(f"{repo}#{num} SCORE={s}")
    for k,v in b.items():
        print(f"    {k}={v}")
    return s, b

for repo, num in [('OWASP/cve-lite-cli',1000),('meilisearch/meilisearch-rust',800),('serde-rs/serde',1500)]:
    score_repo(repo, num)
    print()