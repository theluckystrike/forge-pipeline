import subprocess, json, time, re, sys
sys.path.insert(0, '/Users/mike/oss-pipeline')
from pipeline import gh, score_candidate

CLAIM_PATTERNS = [
    r'\bi.?ll take\b', r'\bi.?ll work on\b', r'\bi want to work\b', r'\bi.?d like to work\b',
    r'\bclaim\b', r'\bassigned\b', r'\bworking on\b', r'\bopen(ing|ed)? a pr\b',
    r'\bpr (is|opened|submitted)\b', r'\bfix(ing|ed)? this\b', r'\bhandle this\b',
    r'\bmy pr\b', r'\bregression test\b', r'\bsubmitted\b',
]
RESOLVED_PATTERNS = [r'#\d+', r'pull request', r'merged', r'closed', r'resolved', r'fixed in', r'pr #']
MAINTAINER_HOLD = [r'hold for you', r'offering you this', r'reserved', r'i said i would']
BOT_TRIAGE = ['github-actions[bot]', 'dependabot', 'codex', 'sweep', 'renovate']

CLAIM_RE = re.compile('|'.join(CLAIM_PATTERNS), re.I)
RESOLVED_RE = re.compile('|'.join(RESOLVED_PATTERNS), re.I)
HOLD_RE = re.compile('|'.join(MAINTAINER_HOLD), re.I)
# first-person commitment to actually do the work = a real claim, not chatter
FIRSTPERSON_RE = re.compile(r"\bi.?d like to work\b|\bi.?ll take\b|\bi.?ll work on\b|\bi.?m working on\b|\bi will (fix|handle|implement|add)\b|\bi.?ll (fix|handle|implement|add|trace|inspect)\b|\bi.?ll start\b|\btaking this\b", re.I)

def classify_comment(author, body):
    body_l = body.lower()
    if author in BOT_TRIAGE or '[bot]' in author:
        return 'bot_triage'
    if HOLD_RE.search(body_l):
        return 'maintainer_hold'   # reserved for specific person -> contested
    if FIRSTPERSON_RE.search(body_l):
        return 'genuine_claim'     # "I'd like to work on this" = real claim -> contested
    if CLAIM_RE.search(body_l) and RESOLVED_RE.search(body_l):
        return 'genuine_claim'     # someone working on it / linked PR
    if CLAIM_RE.search(body_l):
        return 'claim_chatter'     # vague "can I take this?" with no commitment
    if RESOLVED_RE.search(body_l):
        return 'resolution_hint'   # references a PR/issue - check linkage
    return 'harmless'              # maintainer confirming open, etc

def check_candidate(repo, num, labels, stars, lic, author):
    try:
        res = subprocess.run(['gh','api',f'repos/{repo}/issues/{num}/comments','--jq','.'], capture_output=True, text=True, timeout=40)
        comments = json.loads(res.stdout)
    except Exception as e:
        return None
    if not comments:
        return None  # already handled by standard discovery (0 comments)
    # classify each comment
    classes = [classify_comment(cm['user']['login'], cm['body']) for cm in comments]
    # uncontested if all comments are claim_chatter, harmless, or bot_triage (no genuine claim, no maintainer hold, no resolution)
    contested = any(k in classes for k in ('genuine_claim','maintainer_hold','resolution_hint'))
    if contested:
        return {'repo':repo,'num':num,'status':'CONTESTED','classes':classes}
    # treat as uncontested: re-score with comments=0 (claim-chatter doesn't contest)
    c = {
        'repo': repo, 'number': num, 'title': '', 'labels': labels,
        'comments': 0, 'stars': stars, 'license': lic, 'pushed_days_ago': 0,
        'issue_body': '', 'issue_author': author, 'verified': True, 'assignee': None,
    }
    s, b = score_candidate(c)
    return {'repo':repo,'num':num,'status':'UNCONTESTED','score':s,'classes':classes,'breakdown':b}

# candidates surfaced by widened discovery with 1-2 comments
cands = [
    ('apache/mahout', 1468, ['bug','docs','good-first-issue'], 2308, 'Apache-2.0', 'viiccwen'),
    ('apache/mahout', 1469, ['bug','docs','good-first-issue'], 2308, 'Apache-2.0', 'viiccwen'),
    ('apache/mahout', 1471, ['bug','docs','question','good-first-issue'], 2308, 'Apache-2.0', 'viiccwen'),
    ('lacs-project/sysknife', 464, ['documentation','good first issue','help wanted','easy'], 12, 'MIT', 'vladimirrott'),
    ('lacs-project/sysknife', 451, ['documentation','good first issue','help wanted','easy'], 12, 'MIT', 'vladimirrott'),
    ('webamigos/RagenAI', 1100, ['documentation','help wanted','good first issue'], 2, 'Apache-2.0', 'patrykomiotek'),
    ('sima-neat/core', 911, ['documentation','help wanted'], 6, 'Apache-2.0', 'dotimothy'),
    ('lingdojo/kana-dojo', 30676, ['documentation','help wanted','good first issue','hacktoberfest'], 3438, 'AGPL-3.0', 'tentoumushii'),
    ('lightly-ai/lightly-train', 980, ['bug','documentation','good first issue','help wanted'], 1681, 'AGPL-3.0', 'liopeer'),
    ('getsotto/sotto-action', 47, ['documentation','good first issue','help wanted'], 1, 'Apache-2.0', 'Maxerns'),
    ('videojs/v10', 2885, ['needs discussion','docs','site','pkg:html'], 947, 'NOASSERTION', 'luwes'),
    ('revsmoke/promptrejectormcp', 8, ['documentation','help wanted','good first issue'], 2, 'ISC', 'revsmoke'),
]
for repo,num,labels,stars,lic,author in cands:
    r = check_candidate(repo,num,labels,stars,lic,author)
    if r:
        if r['status']=='UNCONTESTED':
            print(f"UNCONTESTED {repo}#{num} SCORE={r['score']} classes={r['classes']}")
            for k,v in r['breakdown'].items():
                if v < 10 and v > 0: print(f"    {k}={v}")
        else:
            print(f"CONTESTED   {repo}#{num} classes={r['classes']}")
    time.sleep(2)