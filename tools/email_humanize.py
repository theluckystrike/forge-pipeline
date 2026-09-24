#!/usr/bin/env python3
"""Email humanize gate. The source of truth is ~/Desktop/humanize (HUMANIZE.md + scan.py).

Every run: re-sync scan.py and HUMANIZE.md from the Desktop copy (iCloud-safe, 25 s timeout),
then apply ZERO-TOLERANCE rules to an outreach email: every scan.py finding blocks (hard AND soft),
plus the HUMANIZE.md rules scan.py does not check (colon before a list, three similar-length
sentences in a row, no contractions, paragraph over 4 sentences, question opener, exclamation).

Usage: email_humanize.py FILE...   exit 0 clean, 1 findings, prints one line per finding.
"""
import hashlib, importlib.util, os, re, subprocess, sys

PIPE = os.path.expanduser("~/oss-pipeline")
SRC = os.path.expanduser("~/Desktop/humanize")
LOCAL_SCAN = os.path.join(PIPE, "tools", "humanize_scan.py")
LOCAL_MD = os.path.join(PIPE, "docs", "HUMANIZE.md")
SYNC_LOG = os.path.join(PIPE, "state", "humanize-sync.log")


def _read_desktop(name):
    r = subprocess.run(["timeout", "25", "cat", os.path.join(SRC, name)], capture_output=True)
    return r.stdout if r.returncode == 0 and r.stdout else None


def sync():
    """Pull the Desktop rules. Returns a status string. Never raises."""
    notes = []
    for name, dst in (("scan.py", LOCAL_SCAN), ("HUMANIZE.md", LOCAL_MD)):
        b = _read_desktop(name)
        if b is None:
            notes.append(f"{name}: Desktop unreadable, using local copy")
            continue
        cur = open(dst, "rb").read() if os.path.exists(dst) else b""
        if b != cur:
            open(dst, "wb").write(b)
            notes.append(f"{name}: UPDATED from Desktop sha {hashlib.sha256(b).hexdigest()[:12]}")
        else:
            notes.append(f"{name}: in sync sha {hashlib.sha256(b).hexdigest()[:12]}")
    msg = "; ".join(notes)
    try:
        os.makedirs(os.path.dirname(SYNC_LOG), exist_ok=True)
        with open(SYNC_LOG, "a") as f:
            import datetime
            f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} {msg}\n")
    except Exception:
        pass
    return msg


def _scanner():
    spec = importlib.util.spec_from_file_location("humanize_scan", LOCAL_SCAN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


CONTRACTION = re.compile(r"\b\w+'(?:s|t|ll|re|ve|d|m)\b", re.I)
SKIP_LINE = re.compile(r"^(subject|reply-to|to|from)\s*:|^(hi|hello|dear)\b|^michael lip|^mike@|^if this is not relevant", re.I)


def body_of(text):
    lines = text.splitlines()
    # drop header block (up to first blank line after Subject/Reply-To)
    if lines and re.match(r"(?i)subject\s*:", lines[0]):
        i = 0
        while i < len(lines) and lines[i].strip():
            i += 1
        lines = lines[i:]
    return "\n".join(lines).strip()


def sentences(par):
    par = re.sub(r"https?://\S+", "URL", par)
    par = re.sub(r"(\d)\.(\d)", r"\1<d>\2", par)
    parts = re.split(r"(?<=[.?!])\s+(?=[A-Z0-9\"'(])", par.strip())
    return [p.replace("<d>", ".") for p in parts if p.strip()]


def extra_checks(text):
    out = []
    body = body_of(text)
    pars = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    prose = [p for p in pars if not SKIP_LINE.match(p)]
    if "!" in re.sub(r"https?://\S+", "", body):
        out.append(("exclamation", "exclamation mark in email"))
    lines = body.splitlines()
    for i, l in enumerate(lines[:-1]):
        if l.rstrip().endswith(":") and re.match(r"\s*([-*]|\d+[.)])\s", lines[i + 1] or ""):
            out.append(("colon_before_list", l.strip()[:60]))
    if re.search(r"\*\*[^*]+\*\*|^#{1,6}\s", body, re.M):
        out.append(("markdown_formatting", "bold or heading markup in email"))
    if not CONTRACTION.search(body):
        out.append(("no_contractions", "HUMANIZE requires contractions where a person would use them"))
    allsent = []
    for p in prose:
        ss = sentences(p)
        if len(ss) > 4:
            out.append(("paragraph_over_4_sentences", f"{len(ss)} sentences: {p[:50]}"))
        allsent += ss
    lens = [len(s.split()) for s in allsent]
    for i in range(len(lens) - 2):
        a, b, c = lens[i:i + 3]
        if max(a, b, c) - min(a, b, c) <= 3:
            out.append(("sentence_rhythm", f"3 similar-length sentences in a row ({a},{b},{c} words): {allsent[i][:40]}"))
            break
    if allsent and allsent[0].rstrip().endswith("?"):
        out.append(("question_opener", allsent[0][:60]))
    return out


def check_text(text, do_sync=True):
    status = sync() if do_sync else "sync skipped"
    m = _scanner()
    res = m.scan_text(text, False)
    found = []
    # scan_text returns a dict/list of (category, items); accept both shapes
    items = res.items() if isinstance(res, dict) else res
    for entry in items:
        cat, vals = (entry if isinstance(entry, tuple) and len(entry) == 2 else (str(entry), []))
        if vals:
            found.append((f"scan:{cat}", "; ".join(map(str, vals))[:120]))
    found += extra_checks(text)
    return found, status


def main(argv):
    if not argv:
        print(__doc__); return 2
    bad = 0
    status = sync()
    print(f"rules: {status}")
    for p in argv:
        f, _ = check_text(open(p, encoding="utf-8").read(), do_sync=False)
        if f:
            bad += 1
            print(f"FAIL {p}")
            for c, d in f:
                print(f"   [{c}] {d}")
        else:
            print(f"CLEAN {p}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
