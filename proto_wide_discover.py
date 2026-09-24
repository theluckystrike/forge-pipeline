#!/usr/bin/env python3
"""Prototype widened discovery for W30 FORGE sprint.

Axis A: "claim-chatter" acceptance - open, UNASSIGNED issues with 1-2 comments,
where the comment is usually someone asking to take it, BUT must pass a linked-PR
cross-check (a comment pointing at a merged/closed PR = already-resolved false positive).
Axis B: docs-only axis - surface pure-docs candidates that can reach exactly 100.

This prototype encodes the W30 lesson: cashubtc/nutshell#500 was scored 100 but its
single comment pointed at PR#507 which was MERGED, so the issue was already resolved.
"""
import subprocess, json, re, time

GOOD_FIRST_QUERIES_A = [
    'is:issue is:open no:assignee label:"good first issue" label:documentation comments:1..2 archived:false',
    'is:issue is:open no:assignee label:"help wanted" label:documentation comments:1..2 archived:false',
    'is:issue is:open no:assignee label:docs comments:1..2 archived:false',
    'is:issue is:open no:assignee label:"good first issue" label:documentation comments:0 archived:false',
]

CLAIM_PTR = re.compile(r'\b(?:#|pull/?\s?|pull/?request/?\s?)(\d{2,6})\b', re.I)

def gh_endpoint(ep):
    res = subprocess.run(['gh','api',ep,'--jq','.'], capture_output=True, text=True, timeout=40)
    if res.returncode != 0:
        return {"error": res.stderr[:200]}
    try:
        return json.loads(res.stdout)
    except Exception:
        return {"error": "parse"}

def gh_search(q, n=15):
    from urllib.parse import quote
    ep = "search/issues?" + "&".join([f"q={quote(q)}", f"per_page={n}", "sort=updated", "order=desc"])
    res = subprocess.run(['gh','api',ep,'--jq','.'], capture_output=True, text=True, timeout=40)
    if res.returncode != 0:
        return {"error": res.stderr[:200]}
    try:
        return json.loads(res.stdout)
    except Exception:
        return {"error": "parse"}

def is_already_resolved(repo, issue_num, comments):
    """If any comment links to a PR that is MERGED/CLOSED, the issue is resolved -> exclude."""
    pr_nums = set()
    for c in comments:
        body = c.get('body') or ''
        for m in CLAIM_PTR.finditer(body):
            n = int(m.group(1))
            if 100 <= n <= 99999:
                pr_nums.add(n)
    for n in sorted(pr_nums):
        pr = gh_endpoint(f"repos/{repo}/pulls/{n}")
        if isinstance(pr, dict) and pr.get('state'):
            state = pr['state']
            # merged is 'closed' + merged_at set
            merged = bool(pr.get('merged_at'))
            if state == 'closed' or merged or state == 'merged':
                return True, state, n
        time.sleep(1.2)
    return False, None, None

def run():
    cands = []
    for q in GOOD_FIRST_QUERIES_A:
        d = gh_search(q)
        if 'error' in d:
            print(f"[rate/backoff {q[:45]}] {d['error'][:50]}")
            time.sleep(45); continue
        for it in d.get('items', []):
            repo_url = it.get('repository_url') or ''
            it['repo'] = repo_url.replace('https://api.github.com/repos/','')
            it['query'] = q
            if it['repo']:
                cands.append(it)
        time.sleep(8)  # secondary-rate-limit spacing
    # de-dup
    seen = {}
    for c in cands:
        k = (c['repo'], c['number'])
        if k not in seen:
            seen[k] = c
    results = list(seen.values())
    print(f"WIDENED raw candidates: {len(results)}")

    exclusions = []
    clean = []
    for c in results:
        resolved = False
        if c.get('comments', 0) >= 1:
            try:
                comments = gh_endpoint(f"repos/{c['repo']}/issues/{c['number']}/comments")
                if isinstance(comments, list):
                    resolved, state, prn = is_already_resolved(c['repo'], c['number'], comments)
                    if resolved:
                        exclusions.append((c['repo'], c['number'], f"claim->PR#{prn} {state}"))
            except Exception as e:
                print("  err", e)
            time.sleep(1.5)
        if not resolved:
            clean.append(c)

    print(f"After claim->merged/closed-PR exclusion: {len(clean)}")
    print("EXCLUDED (already-resolved):")
    for e in exclusions:
        print("  ", e)
    return clean

if __name__ == "__main__":
    clean = run()
    print("\nCLEAN WIDENED CANDIDATES:")
    if not clean:
        print("  (none)")
    for c in clean:
        lbls = [l.get('name') or str(l) for l in c['labels']] if isinstance(c['labels'],(list,)) else []
        print(f"  {c['repo']}#{c['number']} | {c.get('comments')}c | {c['title'][:58]} | {','.join(lbls)}")