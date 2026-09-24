import subprocess, json, time, sys, re
sys.path.insert(0, '/Users/mike/oss-pipeline')
from pipeline import search, score_candidate, ACCOUNT

# Docs-only widened axis: high-star, 0-comment OR 1-2 claim-chatter, docs label
docs_queries = [
    'label:"documentation" state:open stars:>1000 pushed:>2026-09-05 no:assignee comments:0',
    'label:"good first issue" state:open stars:>800 pushed:>2026-09-01 no:assignee comments:0',
    'label:"docs" state:open stars:>1500 pushed:>2026-09-01 no:assignee comments:0',
    'label:"documentation" state:open stars:>2000 pushed:>2026-09-01 no:assignee comments:1',
    'label:"good first issue" state:open stars:>1000 pushed:>2026-09-01 no:assignee comments:1',
]
seen = {}
for q in docs_queries:
    try:
        r = search(q, n=15)
        for item in r.get('items', []):
            repo = item['repository_url'].replace('https://api.github.com/repos/','')
            num = item['number']
            key = f"{repo}#{num}"
            if key in seen: continue
            seen[key] = {
                'repo': repo, 'num': num, 'title': item['title'],
                'labels': [l['name'] for l in item.get('labels',[])],
                'comments': item.get('comments',0), 'stars': item.get('stars',0),
            }
    except Exception as e:
        print("ERR", q, str(e)[:80])
    time.sleep(3)
print(f"Docs-axis raw candidates: {len(seen)}")

# Verify each: health + score
results = []
for key, c in seen.items():
    repo, num = c['repo'], c['num']
    try:
        r = subprocess.run(['gh','api',f'repos/{repo}','--jq','.'], capture_output=True, text=True, timeout=40)
        rj = json.loads(r.stdout)
        if rj.get('archived') or rj.get('disabled'): continue
        stars = rj.get('stargazers_count',0)
        if stars < 300: continue
        lic = (rj.get('license') or {}).get('spdx_id')
        if lic not in ('MIT','Apache-2.0','BSD-3-Clause','BSD-2-Clause','ISC','MPL-2.0'): continue
        pushed = rj.get('pushed_at','')
        issue = subprocess.run(['gh','api',f'repos/{repo}/issues/{num}','--jq','.'], capture_output=True, text=True, timeout=40)
        ij = json.loads(issue.stdout)
        if ij.get('state') != 'open' or ij.get('assignee') or ij.get('pull_request'): continue
        if (ij.get('comments') or 0) > 2: continue
        body = ij.get('body') or ''
        author = (ij.get('user') or {}).get('login')
        # recheck comments for claim-chatter
        if (ij.get('comments') or 0) > 0:
            cr = subprocess.run(['gh','api',f'repos/{repo}/issues/{num}/comments','--jq','.'], capture_output=True, text=True, timeout=40)
            cms = json.loads(cr.stdout)
            contested = False
            for cm in cms:
                b = cm['body'].lower()
                if re.search(r"\bi.?d like to work\b|\bi.?ll take\b|\bi.?ll work on\b|\bi.?m working on\b|hold for you|offering you|opened a pr|submitted", b):
                    contested = True; break
            if contested: continue
        cc = {
            'repo':repo,'number':num,'title':ij.get('title',''),'labels':[l['name'] for l in ij.get('labels',[])],
            'comments':0,'stars':stars,'license':lic,'pushed_days_ago':0,'issue_body':body,
            'issue_author':author,'verified':True,'assignee':None,
        }
        s, b = score_candidate(cc)
        results.append((s, repo, num, ij.get('title','')[:60], b))
    except Exception as e:
        pass
    time.sleep(1.5)

results.sort(key=lambda x:-x[0])
print(f"\nPassed filters: {len(results)}")
for s, repo, num, title, b in results:
    low = {k:v for k,v in b.items() if v < (15 if k=='repo_health' else 10)}
    print(f"SCORE={s} {repo}#{num} | {title}")
    if low: print(f"    low: {low}")