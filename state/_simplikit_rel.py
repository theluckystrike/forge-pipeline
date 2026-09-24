import subprocess, json, sys
from datetime import datetime
sys.path.insert(0, '/Users/mike/oss-pipeline')
from pipeline import score_candidate

# Check what PR #519 is and its relation to issue #500
for num in [500, 519]:
    try:
        issue = json.loads(subprocess.run(['gh','api',f'repos/toss/react-simplikit/issues/{num}','--jq','.'],capture_output=True,text=True,timeout=40).stdout)
        print(f"issue #{num}: title='{issue.get('title')}' state={issue.get('state')} comments={issue.get('comments')} is_pr={bool(issue.get('pull_request'))}")
        print(f"  labels={[l['name'] for l in issue.get('labels',[])]} assignee={issue.get('assignee')}")
    except Exception as e:
        print(f"#{num} error: {e}")

# Check PRs referencing issue 500
print("\n=== PRs referencing issue 500 ===")
prs = json.loads(subprocess.run(['gh','api','search/issues','-f','q=repo:toss/react-simplikit is:pr 500','--jq','.items'],capture_output=True,text=True,timeout=40).stdout)
for p in prs:
    print(f"  PR #{p['number']} state={p['state']} title='{p['title']}'")
    # check body for "500"
    if '500' in (p.get('body') or ''):
        print(f"    body mentions 500: {p['body'][:200]}")
        # get timeline for cross-reference
        tl = json.loads(subprocess.run(['gh','api',f'repos/toss/react-simplikit/issues/{p["number"]}/timeline','--jq','.[]?'],capture_output=True,text=True,timeout=40).stdout)
        for e in tl:
            if e.get('event') in ('cross-referenced','referenced'):
                src = e.get('source',{}).get('issue',{})
                print(f"    {e.get('event')}: {src.get('number')} {src.get('title','')[:60]}")