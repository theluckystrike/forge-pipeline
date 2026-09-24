import subprocess, json, time, sys
sys.path.insert(0, '/Users/mike/oss-pipeline')
from pipeline import gh, score_candidate, ACCOUNT

cands = [
    ('lacs-project/sysknife', 464),
    ('lacs-project/sysknife', 451),
    ('webamigos/RagenAI', 1100),
    ('webamigos/RagenAI', 1138),
    ('webamigos/RagenAI', 1139),
    ('lightly-ai/lightly-train', 980),
    ('apache/mahout', 1468),
    ('apache/mahout', 1469),
    ('apache/mahout', 1471),
    ('videojs/v10', 2885),
    ('videojs/v10', 2722),
    ('LunchBox951/pokeemerald-rs', 655),
    ('getsotto/sotto-action', 47),
    ('sima-neat/core', 911),
    ('georgestephanis/community-login-idp', 8),
    ('lingdojo/kana-dojo', 30676),
    ('revsmoke/promptrejectormcp', 8),
]

for repo, num in cands:
    try:
        r = gh(f"repos/{repo}")
        if r.get('archived') or r.get('disabled'):
            print(f"{repo}#{num} ARCHIVED/DISABLED"); continue
        stars = r.get('stargazers_count', 0)
        pushed = r.get('pushed_at','')
        lic = (r.get('license') or {}).get('spdx_id')
        issue = gh(f"repos/{repo}/issues/{num}")
        if issue.get('state') != 'open' or issue.get('assignee') or issue.get('pull_request'):
            print(f"{repo}#{num} NOT-OPEN/ASSIGNED/PR"); continue
        comments = issue.get('comments', 0)
        labels = [l['name'] for l in issue.get('labels', [])]
        author = issue.get('user', {}).get('login')
        bodylen = len(issue.get('body') or '')
        c = {
            'repo': repo, 'number': num, 'title': issue.get('title',''),
            'labels': labels, 'comments': comments, 'stars': stars,
            'license': lic, 'pushed_days_ago': 0, 'issue_body': issue.get('body') or '',
            'issue_author': author, 'verified': True, 'assignee': None,
        }
        s, b = score_candidate(c)
        print(f"{repo}#{num} stars={stars} lic={lic} c={comments} lbl={','.join(labels[:4])} author={author} SCORE={s}")
        print(f"    bodylen={bodylen} | {issue.get('title','')[:70]}")
    except Exception as e:
        print(f"{repo}#{num} ERR {str(e)[:120]}")
    time.sleep(1.5)