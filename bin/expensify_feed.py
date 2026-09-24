#!/usr/bin/env python3
"""Expensify Help Wanted feed (WhiteHERO v3, lane L3).

Lists open Expensify/App issues labelled "Help Wanted", extracts the bounty from the
title ("[$250]") or a "$N" label, skips issues that are already taken, and inserts
the rest into kpi.db proposals(issue_url, bounty_usd, drafted_at NULL).

Taken means any of:
  - title carries "[HOLD" or "Due for payment"
  - the last 30 comments contain a C+ approval ("🎀👀🎀", spaced or not),
    "proposal accepted", or a Melvin Upwork offer for the Contributor role
  - a non-bot assignee is a contributor rather than staff: they posted a
    "Proposal" in the last 30 comments, or were named in a Contributor-role offer.
    Staff (BZ, C+, engineers) are auto-assigned on every issue, so a plain
    "has a non-bot assignee" rule would skip all 28 issues; see README.

Cost per run: 1 REST call (issue list, up to 100 per page) plus 1 GraphQL call per
10 issues. Posts nothing. Idempotent (INSERT OR IGNORE; bounty filled only if NULL).
Usage: expensify_feed.py [--dry-run] [--json]
"""
import json, os, re, sqlite3, subprocess, sys, time, datetime

PIPE = os.path.expanduser('~/oss-pipeline')
DB = os.path.join(PIPE, 'state', 'kpi.db')
SNAP = os.path.join(PIPE, 'state', 'expensify', 'feed-last.json')
REPO = 'Expensify/App'
BOTS = {'melvin-bot', 'MelvinBot', 'github-actions', 'OSBotify', 'imgbot', 'dependabot', 'codecov'}
CPLUS = re.compile(r'🎀\s*👀\s*🎀')
ACCEPT = re.compile(r'proposal\s+(?:has\s+been\s+|is\s+)?accepted', re.I)
OFFER = re.compile(r'@([\w-]+)[^\n]{0,40}\n?[^\n]{0,20}offer has been automatically sent to your Upwork account for the Contributor role', re.I)
PROPOSAL = re.compile(r'^\s*#{1,4}\s*Proposal\b', re.M | re.I)
FIXED = re.compile(r'(appears to be|has been|is already|already) fixed|no longer reproduc', re.I)
BOUNTY_TITLE = re.compile(r'\[\$\s?(\d[\d,]*)\]')
BOUNTY_LABEL = re.compile(r'^\$\s?(\d[\d,]*)$')


def gh(args, tries=(0, 20, 40, 80)):
    err = ''
    for back in tries:
        if back:
            time.sleep(back)
        r = subprocess.run(['gh'] + args, capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout
        err = r.stderr.strip()
        if 'rate limit' not in err.lower() and '403' not in err and '429' not in err and '502' not in err:
            break
    raise RuntimeError('gh failed: ' + err[:300])


def is_bot(login):
    return (not login) or login in BOTS or login.endswith('[bot]')


def list_help_wanted():
    out = gh(['api', '-X', 'GET', f'repos/{REPO}/issues', '-f', 'labels=Help Wanted',
              '-f', 'state=open', '-f', 'per_page=100', '--paginate'])
    items = []
    for chunk in out.replace('][', ']\n[').split('\n'):
        chunk = chunk.strip()
        if chunk:
            items += json.loads(chunk)
    return [i for i in items if 'pull_request' not in i]


FIELDS = '''number title createdAt url assignees(first:20){nodes{login}}
 comments(last:30){nodes{author{login} createdAt body}}'''


def fetch_details(numbers):
    det = {}
    for k in range(0, len(numbers), 10):
        chunk = numbers[k:k + 10]
        body = ' '.join(f'i{n}: issue(number:{n}){{{FIELDS}}}' for n in chunk)
        q = f'query{{repository(owner:"Expensify",name:"App"){{{body}}} rateLimit{{cost remaining}}}}'
        d = json.loads(gh(['api', 'graphql', '-f', 'query=' + q]))['data']
        for n in chunk:
            det[n] = d['repository'][f'i{n}']
    return det


def bounty_of(issue):
    m = BOUNTY_TITLE.search(issue['title'])
    if m:
        return float(m.group(1).replace(',', ''))
    for lab in issue.get('labels', []):
        m = BOUNTY_LABEL.match(lab['name'].strip())
        if m:
            return float(m.group(1).replace(',', ''))
    return None


def taken_reason(issue, det):
    t = issue['title']
    if '[HOLD' in t.upper():
        return 'hold'
    if 'due for payment' in t.lower():
        return 'due-for-payment'
    comments = det['comments']['nodes'] if det else []
    proposers, offered = set(), set()
    for c in comments:
        b = c['body'] or ''
        who = (c['author'] or {}).get('login', '')
        if CPLUS.search(b):
            return 'c+-approved'
        if ACCEPT.search(b):
            return 'proposal-accepted'
        for m in OFFER.finditer(b):
            offered.add(m.group(1))
        if PROPOSAL.search(b) and not is_bot(who):
            proposers.add(who)
    if offered:
        return 'contributor-offer'
    human = [c for c in comments if not is_bot((c['author'] or {}).get('login', ''))][-3:]
    if any(FIXED.search(c['body'] or '') for c in human):
        return 'reported-fixed'
    for a in (det['assignees']['nodes'] if det else issue['assignees']):
        login = a['login']
        if not is_bot(login) and login in proposers:
            return 'contributor-assigned'
    return None


def main():
    dry = '--dry-run' in sys.argv
    issues = list_help_wanted()
    det = fetch_details([i['number'] for i in issues]) if issues else {}
    rows, skipped = [], {}
    for i in issues:
        reason = taken_reason(i, det.get(i['number']))
        rec = {'number': i['number'], 'url': i['html_url'], 'title': i['title'],
               'bounty_usd': bounty_of(i), 'created_at': i['created_at'],
               'labels': [l['name'] for l in i['labels']],
               'assignees': [a['login'] for a in i['assignees']], 'taken': reason}
        rows.append(rec)
        if reason:
            skipped[reason] = skipped.get(reason, 0) + 1
    eligible = [r for r in rows if not r['taken']]
    new = upd = 0
    if not dry:
        con = sqlite3.connect(DB, timeout=30)
        with con:
            for r in eligible:
                cur = con.execute('INSERT OR IGNORE INTO proposals(issue_url, bounty_usd, drafted_at) VALUES (?,?,NULL)',
                                  (r['url'], r['bounty_usd']))
                new += cur.rowcount
                if r['bounty_usd'] is not None:
                    upd += con.execute('UPDATE proposals SET bounty_usd=? WHERE issue_url=? AND bounty_usd IS NULL',
                                       (r['bounty_usd'], r['url'])).rowcount
        con.close()
        os.makedirs(os.path.dirname(SNAP), exist_ok=True)
        json.dump({'at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
                   'rows': rows}, open(SNAP, 'w'), indent=1)
    if '--json' in sys.argv:
        print(json.dumps(rows, indent=1))
    sk = ','.join(f'{k}={v}' for k, v in sorted(skipped.items())) or 'none'
    print(f'expensify_feed: open_help_wanted={len(rows)} eligible={len(eligible)} new={new} '
          f'bounty_filled={upd} taken={len(rows) - len(eligible)} ({sk}){" DRY-RUN" if dry else ""}')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'expensify_feed: ERROR {e}', file=sys.stderr)
        sys.exit(1)
