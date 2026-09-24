import subprocess, json, time
cands = [
    ('apache/mahout', 1468),
    ('apache/mahout', 1469),
    ('apache/mahout', 1471),
    ('lacs-project/sysknife', 464),
    ('lacs-project/sysknife', 451),
    ('webamigos/RagenAI', 1100),
    ('sima-neat/core', 911),
    ('lingdojo/kana-dojo', 30676),
    ('lightly-ai/lightly-train', 980),
    ('getsotto/sotto-action', 47),
]
for repo, num in cands:
    try:
        res = subprocess.run(['gh','api',f'repos/{repo}/issues/{num}/comments','--jq','.'], capture_output=True, text=True, timeout=40)
        comments = json.loads(res.stdout)
        print(f"=== {repo}#{num} ({len(comments)} comments) ===")
        for cm in comments:
            print(f"  [{cm['user']['login']}] {cm['body'][:200].replace(chr(10),' ')}")
    except Exception as e:
        print(f"{repo}#{num} ERR {str(e)[:80]}")
    time.sleep(2)