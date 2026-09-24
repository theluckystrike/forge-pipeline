#!/usr/bin/env python3
"""check_evidence.py: every integer and percentage in an audit report must appear in its evidence dir.

Usage:
  python3 check_evidence.py reports/org__repo.md [--evidence DIR]   one report (evidence = reports/org__repo/evidence)
  python3 check_evidence.py reports/                                 every reports/*.md
Exit 0 when every token is found, else prints the missing tokens per report and exits 1.

A token is a digit run, optionally with decimals, thousands commas or a trailing %, not glued to
letters (so commit hashes, 'l10n' or 'v2beta' are not tokens). '1,500' is searched as '1,500' or '1500';
'39.6%' as '39.6'. A match in evidence must not be part of a longer number.
"""
import os, re, sys

TOK = re.compile(r'(?<![A-Za-z0-9_.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(%?)(?![A-Za-z0-9_]|\.\d)')

def tokens(text):
    out = []
    for m in TOK.finditer(text):
        out.append(m.group(1) + m.group(2))
    return sorted(set(out), key=lambda t: (len(t), t))

def load_evidence(d):
    blobs = []
    for root, _, fs in os.walk(d):
        for f in fs:
            try:
                blobs.append(open(os.path.join(root, f), encoding="utf-8", errors="replace").read())
            except OSError:
                pass
    return "\n".join(blobs)

def found(tok, ev):
    t = tok.rstrip('%')
    forms = {t, t.replace(',', '')}
    for f in forms:
        if re.search(r'(?<![0-9])' + re.escape(f) + r'(?![0-9]|\.\d)', ev):
            return True
    return False

def check(report, evdir=None):
    if evdir is None:
        evdir = os.path.join(report[:-3], "evidence")
    if not os.path.isdir(evdir):
        return None, [f"evidence dir missing: {evdir}"]
    ev = load_evidence(evdir)
    text = open(report, encoding="utf-8").read()
    toks = tokens(text)
    return toks, [t for t in toks if not found(t, ev)]

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(2)
    evdir = a[a.index("--evidence") + 1] if "--evidence" in a else None
    target = a[0]
    reports = [os.path.join(target, f) for f in sorted(os.listdir(target)) if f.endswith(".md")] if os.path.isdir(target) else [target]
    bad = 0
    for r in reports:
        toks, missing = check(r, evdir)
        if missing:
            bad += 1
            print(f"FAIL {r}: {len(missing)} of {len(toks) if toks else 0} tokens not in evidence: {' '.join(missing[:40])}")
        else:
            print(f"PASS {r}: {len(toks)} tokens, all found in evidence")
    print(f"{len(reports) - bad}/{len(reports)} reports pass")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
