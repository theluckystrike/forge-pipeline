#!/usr/bin/env python3
"""Check every '### E<k> <path> L<a>-L<b>' block in proposals/*.evidence.md against the pinned source mirror.
Also checks that every pinned-SHA permalink in the proposal points at an existing file and in-range lines.
Exit 1 on any mismatch. Posts nothing, no network."""
import glob, os, re, sys
PIPE = os.path.expanduser('~/oss-pipeline')
SHA = 'c134a8df49ca39dce693b81084cf0e58354c0821'
M = os.path.join(PIPE, 'state/expensify/src-mirror', f'App-{SHA}')
HDR = re.compile(r'^###\s+E\d+\s+(\S+)\s+L(\d+)-L?(\d+)\s*$', re.M)
LINK = re.compile(r'github\.com/Expensify/App/blob/' + SHA + r'/([^\s#)\]]+)#L(\d+)(?:-L(\d+))?')
bad = 0
files = sys.argv[1:] or sorted(glob.glob(os.path.join(PIPE, 'proposals', '*.evidence.md')))
for ev in files:
    txt = open(ev).read()
    n_ok = n = 0
    for m in HDR.finditer(txt):
        n += 1
        path, a, b = m.group(1), int(m.group(2)), int(m.group(3))
        rest = txt[m.end():]
        fm = re.search(r'```[^\n]*\n(.*?)\n```', rest, re.S)
        src = os.path.join(M, path)
        if not fm or not os.path.exists(src):
            print(f'FAIL {os.path.basename(ev)} {path} L{a}-L{b}: {"no code block" if not fm else "file missing"}'); bad += 1; continue
        lines = open(src, encoding='utf-8', errors='replace').read().split('\n')
        want = '\n'.join(lines[a - 1:b]).rstrip()
        got = fm.group(1).rstrip()
        if want != got:
            print(f'FAIL {os.path.basename(ev)} {path} L{a}-L{b}: excerpt differs from mirror'); bad += 1
        else:
            n_ok += 1
    prop = ev.replace('.evidence.md', '.md')
    ln = lb = 0
    if os.path.exists(prop):
        for m in LINK.finditer(open(prop).read()):
            ln += 1
            src = os.path.join(M, m.group(1))
            hi = int(m.group(3) or m.group(2))
            if not os.path.exists(src) or hi > len(open(src, encoding='utf-8', errors='replace').read().split('\n')):
                print(f'FAIL {os.path.basename(prop)} link {m.group(1)}#L{m.group(2)}: missing file or line out of range'); bad += 1; lb += 1
    print(f'{os.path.basename(ev)}: {n_ok}/{n} excerpts match, {ln - lb}/{ln} permalinks resolve')
    if n == 0:
        print(f'FAIL {os.path.basename(ev)}: no E blocks'); bad += 1
sys.exit(1 if bad else 0)
