import subprocess, json, sys
sys.path.insert(0, '/Users/mike/oss-pipeline')
from pipeline import score_candidate, gh

repo='serde-rs/serde'; num=1500
issue = json.loads(subprocess.run(['gh','api',f'repos/{repo}/issues/{num}','--jq','.'],capture_output=True,text=True,timeout=40).stdout)
repo_info = json.loads(subprocess.run(['gh','api',f'repos/{repo}','--jq','.'],capture_output=True,text=True,timeout=40).stdout)
c = {
    'repo': repo, 'number': num,
    'title': issue['title'], 'body': issue.get('body') or '',
    'labels': [l['name'] for l in issue.get('labels',[])],
    'comments': issue.get('comments',0),
    'assignee': issue.get('assignee'),
    'state': issue.get('state'),
    'created_at': issue.get('created_at'),
    'author': (issue.get('user') or {}).get('login'),
    'repo_stars': repo_info.get('stargazers_count'),
    'repo_pushed': repo_info.get('pushed_at'),
    'repo_license': (repo_info.get('license') or {}).get('spdx_id'),
    'repo_archived': repo_info.get('archived'),
}
s = score_candidate(c)
print("FULL SCORE:", s)
print("COMPONENTS:", json.dumps(s.get('components',{}), indent=1) if isinstance(s,dict) else s)