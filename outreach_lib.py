#!/usr/bin/env python3
"""Shared helpers for the WhiteHERO v3 outreach lane (builder, gate, sender).

Nothing here sends anything. Pure stdlib.
"""
import os, re, sqlite3, hashlib, json

PIPE = os.path.expanduser("~/oss-pipeline")
DB = os.environ.get("OUTREACH_DB") or os.path.join(PIPE, "state", "kpi.db")          # override only for tests
OUT = os.environ.get("OUTREACH_DIR") or os.path.join(PIPE, "outreach")
TEMPLATES = os.path.join(PIPE, "outreach", "templates")
QUEUE = os.path.join(OUT, "queue")
REJECTED = os.path.join(OUT, "rejected")
BLOCKLIST = os.path.join(PIPE, "state", "blocklist.txt")
# orgs contacted outside this pipeline (first column = org); they count under one message per org ever
CONTACTED = os.environ.get("OUTREACH_CONTACTED") or os.path.join(PIPE, "state", "contacted.tsv")
HUMANIZE = os.path.join(PIPE, "tools", "humanize_scan.py")

UNSUB = "If this is not relevant, reply 'no' and I will not write again."
SIGNOFF = "Michael Lip, zovo.one"
REPLY_TO = "mike@zovo.one"
TIER1 = {"fr", "de", "es", "it", "ja", "pt", "zh", "ko", "nl"}  # matches audit_locale.py TIER1 base codes

# numbers: a digit run that is not glued to a letter or underscore (so n8n, v2, i18n,
# web3 and sha fragments are identifiers, not measured claims)
NUM_RE = re.compile(r"(?<![A-Za-z0-9_.])(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?(?![A-Za-z0-9_])")


def db():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    return c


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def num_tokens(text):
    """Return every standalone number in text as it is written ('1,234', '39.6', '20')."""
    out = []
    for m in NUM_RE.finditer(text):
        tok = m.group(0)
        out.append(tok)
    return out


def norm_num(tok):
    return tok.replace(",", "")


def template_path(lane):
    return os.path.join(TEMPLATES, f"{lane}.md")


def template_constants(lane):
    """Numbers written into the lane template itself (prices, 20 fixes, 48 hours, 3 languages).
    These are offer terms, not claims about the target repo, so the evidence check skips them."""
    p = template_path(lane)
    if not os.path.exists(p):
        return set()
    t = re.sub(r"\{[a-z_0-9]+\}", " ", open(p, encoding="utf-8").read())
    return {norm_num(x) for x in num_tokens(t)}


def split_email(text):
    """Return (headers dict, body str). Headers end at the first blank line."""
    head, _, body = text.partition("\n\n")
    hdr = {}
    for ln in head.splitlines():
        if ":" in ln:
            k, v = ln.split(":", 1)
            hdr[k.strip().lower()] = v.strip()
    return hdr, body


def word_count(body):
    return len(re.findall(r"\S+", body))


def load_blocklist():
    s = set()
    if os.path.exists(BLOCKLIST):
        for ln in open(BLOCKLIST, encoding="utf-8"):
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                s.add(ln.lower())
    return s


def contacted_orgs():
    """Orgs listed in state/contacted.tsv. A missing file means none; an unreadable one raises
    so the builder fails closed instead of drafting to an org that was already emailed."""
    s = set()
    if os.path.exists(CONTACTED):
        for ln in open(CONTACTED, encoding="utf-8"):
            if not ln.strip() or ln.lstrip().startswith("#"):
                continue
            org = ln.split("\t")[0].strip().lower()
            if org:
                s.add(org)
    return s


def lane_from_filename(name):
    m = re.match(r"(\d+)-(L[0-9][ab]?)\.txt$", os.path.basename(name))
    return (int(m.group(1)), m.group(2)) if m else (None, None)


def db_lane(lane):
    """kpi.db lane column: L2a and L2b are both lane 'L2' (plan 2.2 acceptance query uses lane='L2')."""
    return "L2" if lane.startswith("L2") else lane


# -------- evidence --------
_EVID_CACHE = {}


def evidence_text(evidence_dir, max_bytes=60_000_000):
    """Concatenate every readable file under the audit evidence dir (text only)."""
    if evidence_dir in _EVID_CACHE:
        return _EVID_CACHE[evidence_dir]
    buf, total = [], 0
    if evidence_dir and os.path.isdir(evidence_dir):
        for root, _, files in os.walk(evidence_dir):
            for f in sorted(files):
                p = os.path.join(root, f)
                try:
                    b = open(p, "rb").read(max_bytes - total)
                except OSError:
                    continue
                total += len(b)
                buf.append(b.decode("utf-8", "replace"))
                if total >= max_bytes:
                    break
    t = "\n".join(buf)
    _EVID_CACHE[evidence_dir] = t
    return t


def number_in_evidence(tok, evid):
    """True when the number appears in the evidence as written or without thousands commas,
    bounded so 39.6 does not match 139.6 or 39.61."""
    forms = {tok, norm_num(tok)}
    if "," not in tok and len(tok) > 3 and "." not in tok:
        forms.add(f"{int(tok):,}")
    for f in forms:
        if re.search(r"(?<![\d.])" + re.escape(f) + r"(?![\d])", evid):
            return True
    return False
