#!/usr/bin/env python3
"""Render ~/oss-pipeline/site/l10n.html from l10n.template.html using LIVE gh state.

- PR states come from `gh pr view` at build time; nothing is labelled merged unless gh says MERGED.
- Key counts come from state/pitch-evidence/keycount.txt (raw base vs head comparison, keycount.py).
- Payment buttons appear only for LIVE Stripe links in state/stripe.json["live"]; test links are never used.
usage: python3 build_l10n.py [--out PATH]
"""
import json, subprocess, sys, os, re, datetime, html
PIPE = os.environ.get('PIPE_L10N', os.path.expanduser('~/oss-pipeline'))
MEDUSA = [16932, 16933, 16934, 16936, 16939, 16940, 16942, 16944, 16946, 16948]
OTHER = [('toss/react-simplikit', 519), ('hoppscotch/hoppscotch', 6669)]

def pr(repo, n):
    j = json.loads(subprocess.check_output(['gh', 'pr', 'view', str(n), '-R', repo, '--json',
        'number,title,state,mergedAt,reviewDecision,url']))
    return j

def tag(j):
    if j['state'] == 'MERGED':
        return '<span class="tag merged">merged %s</span>' % j['mergedAt'][:10]
    if j['state'] == 'OPEN':
        return '<span class="tag">open, awaiting maintainer review</span>'
    return '<span class="tag">%s</span>' % j['state'].lower()

def row(repo, j, label):
    return ('      <div class="pr"><span><a href="%s">%s#%d</a> %s</span>%s</div>'
            % (j['url'], (repo + ' ') if repo else '', j['number'], html.escape(label), tag(j)))

def clean_title(t):
    t = t.replace('—', ',').replace(' -- ', ', ')
    t = re.sub(r'^i18n:?\s*', '', t)
    return t

def main():
    out = os.path.join(PIPE, 'site', 'l10n.html')
    if '--out' in sys.argv: out = sys.argv[sys.argv.index('--out') + 1]
    tpl = open(os.path.join(PIPE, 'site', 'l10n.template.html')).read()
    med = [pr('medusajs/medusa', n) for n in MEDUSA]
    oth = [(r, pr(r, n)) for r, n in OTHER]
    kc = open(os.path.join(PIPE, 'state/pitch-evidence/keycount.txt')).read()
    keys = int(re.search(r'TOTAL added (\d+)', kc).group(1))
    n_open = sum(1 for j in med if j['state'] == 'OPEN')
    n_merged = sum(1 for j in med if j['state'] == 'MERGED')
    locales = 14  # 9 full dashboard locales + 5 locales in #16933 (fi hr pl sv tr), from parity.txt
    if n_merged:
        sub = 'Pull requests to Medusa: %d merged, %d open and awaiting maintainer review.' % (n_merged, n_open)
    else:
        sub = 'Pull requests to Medusa, open, CI-validated, and awaiting maintainer review.'
    stats = [(str(n_open), 'PRs open at Medusa')]
    if n_merged: stats.append((str(n_merged), 'PRs merged at Medusa'))
    stats += [(str(locales), 'locale files'), ('{:,}'.format(keys), 'keys added'), ('0', 'missing keys at PR head')]
    stats_html = '\n'.join('      <div class="stat"><div class="num">%s</div><div class="label">%s</div></div>' % s for s in stats)
    med_html = '\n'.join(row('', j, clean_title(j['title'])) for j in med)
    lab = {519: 'Chinese (zh-Hans) docs for all 42 hooks', 6669: 'French locale, 466 missing keys to full en.json parity'}
    oth_html = '\n'.join(row(r, j, lab.get(j['number'], clean_title(j['title']))) for r, j in oth)
    try: live = (json.load(open(os.path.join(PIPE, 'state/stripe.json'))) or {}).get('live') or {}
    except Exception: live = {}
    def cta(key, label, mail_subj, mail_label):
        mail = 'mailto:mike@zovo.one?subject=' + mail_subj
        u = (live.get(key) or {}).get('url', '')
        if u.startswith('https://buy.stripe.com/') and '/test_' not in u:
            return ('        <a class="cta" href="%s">%s</a>\n        <p class="alt">or <a href="%s">%s</a></p>' % (u, label, mail, mail_label.lower()))
        return '        <a class="cta" href="%s">%s</a>' % (mail, mail_label)
    s = (tpl.replace('{{PROOF_SUB}}', sub).replace('{{STATS}}', stats_html)
            .replace('{{MEDUSA_LIST}}', med_html).replace('{{OTHER_LIST}}', oth_html)
            .replace('{{ASOF}}', datetime.date.today().isoformat())
            .replace('{{CTA_LOCALE}}', cta('locale', 'Pay $500 per locale', 'Locale%20completion', 'Email for a quote'))
            .replace('{{CTA_RETAINER}}', cta('retainer', 'Start the retainer', 'Retainer', 'Email about a retainer')))
    assert '{{' not in s, 'unfilled placeholder'
    open(out, 'w').write(s)
    print('wrote', out, 'open', n_open, 'merged', n_merged, 'keys', keys, 'live_links', sorted(live))
main()
