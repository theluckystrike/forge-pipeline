import subprocess, json, time, sys
sys.path.insert(0, '/Users/mike/oss-pipeline')
from pipeline import score_candidate
repo='toss/react-simplikit'; num=500
c = {
    'repo': repo, 'number': num, 'title': '[zh-Hans] Translate API docs: hooks (42)',
    'labels': ['documentation'], 'comments': 0, 'stars': 356,
    'license': 'MIT', 'pushed_days_ago': 0, 'issue_body': 'translate hooks docs',
    'issue_author': 'hyesungoh', 'verified': True, 'assignee': None,
}
s, b = score_candidate(c)
print("SCORE:", s)
for k,v in b.items():
    print(f"  {k}: {v}")
# check for PRs referencing this issue
res = subprocess.run(['gh','api','-X','GET',f'repos/{repo}/issues/{num}/timeline','--jq','.'], capture_output=True, text=True, timeout=40)
tl = json.loads(res.stdout)
print("\nTIMELINE events:", len(tl))
for ev in tl:
    if ev.get('event') in ('cross-referenced','connected','referenced'):
        src = ev.get('source',{})
        print("  ", ev.get('event'), src.get('issue',{}).get('number'), src.get('issue',{}).get('pull_request') is not None)