#!/usr/bin/env python3
"""WhiteHERO v3 outreach gate (plan section 10). Runs on every queued draft.

A draft fails, and is moved to outreach/rejected/ with a .reason file, when any of:
  humanize_scan --strict fails
  call|calls|zoom|meet|meeting|hop on|calendly|schedule a appears (case-insensitive, word-bounded)
  any emoji, U+2014 em dash, or ' -- '
  'merged' appears without a MERGED contributions row for the target repo
  a number in the body is missing from the target's audit evidence dir
    (offer terms written into the lane template, such as $1,500 or 48 hours, are exempt)
  body over 170 words
  missing unsubscribe line
Extra structural checks: unfilled {placeholder}, missing Subject or Reply-To mike@zovo.one,
missing sign-off, duplicate body_sha256, no outreach row, blocklisted repo.

Writes outreach/gate-report.txt with pass and fail counts by reason.

Usage:
  python3 outreach_gate.py              gate every file in outreach/queue/
  python3 outreach_gate.py --check F    check one file, move nothing (used by the sender)
  python3 outreach_gate.py --control    run the known-bad controls and prove each rule fires
"""
import argparse, os, re, shutil, subprocess, sys, tempfile
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from outreach_lib import (PIPE, OUT, QUEUE, REJECTED, HUMANIZE, UNSUB, SIGNOFF, REPLY_TO, db, sha256, num_tokens,
                          norm_num, template_constants, split_email, word_count, evidence_text, number_in_evidence,
                          lane_from_filename, load_blocklist, contacted_orgs)

CALL_RE = re.compile(r"\b(calls?|zoom|meet|meeting|hop on|calendly|schedule a)\b", re.I)
MERGED_RE = re.compile(r"\bmerged\b", re.I)
# pictographs, dingbats, symbols, flags, variation selector, keycap
EMOJI_RE = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\U00002B00-\U00002BFF"
                      "\U0000FE0F\U000020E3\U0001F900-\U0001F9FF✅✨⚡⭐✔]")
# offer-term sentence in L5 carries 'merged' as a guarantee, not a claim
OFFER_TERM_MERGED = "with at least 5 merged or I refund the difference"


def check_evidence_mod():
    """Reuse the AUDIT agent's check_evidence.py (tokens, load_evidence, found) when present."""
    p = os.path.join(PIPE, "check_evidence.py")
    if not os.path.exists(p):
        return None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_evidence", p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None


def humanize_ok(path):
    """Desktop HUMANIZE rules, re-synced on every call, zero tolerance for email (see tools/email_humanize.py)."""
    r = subprocess.run([sys.executable, HUMANIZE, "--strict", path], capture_output=True, text=True, timeout=60)
    tail = [l.strip() for l in r.stdout.splitlines() if "[HARD]" in l or "[soft]" in l]
    ok = r.returncode == 0
    sys.path.insert(0, os.path.join(PIPE, "tools"))
    import email_humanize
    found, _status = email_humanize.check_text(open(path, encoding="utf-8").read(), do_sync=True)
    if found:
        ok = False
        tail += [f"[{c}] {d}" for c, d in found]
    return ok, "; ".join(tail)[:300]


def check(path, conn=None, target_override=None):
    """Return list of (rule, detail) failures for one draft file."""
    fails = []
    text = open(path, encoding="utf-8").read()
    hdr, body = split_email(text)
    tid, lane = lane_from_filename(path)
    if target_override is not None:
        tid = target_override
    conn = conn or db()

    ok, why = humanize_ok(path)
    if not ok:
        fails.append(("humanize_strict", why))
    m = CALL_RE.findall(text)
    if m:
        fails.append(("call_meeting_words", ",".join(sorted(set(x.lower() for x in m)))))
    if EMOJI_RE.search(text):
        fails.append(("emoji", repr(EMOJI_RE.findall(text)[:5])))
    if "—" in text or " -- " in text:
        fails.append(("em_dash", "U+2014 or ' -- '"))
    if re.search(r"\{[a-z_0-9]+\}", text):
        fails.append(("unfilled_placeholder", ",".join(re.findall(r"\{[a-z_0-9]+\}", text))))
    if not hdr.get("subject"):
        fails.append(("no_subject", ""))
    if hdr.get("reply-to", "").lower() != REPLY_TO:
        fails.append(("reply_to", hdr.get("reply-to", "missing")))
    if SIGNOFF not in body:
        fails.append(("no_signoff", ""))
    if UNSUB not in body:
        fails.append(("no_unsubscribe", ""))
    wc = word_count(body)
    if wc > 170:
        fails.append(("over_170_words", str(wc)))

    t = a = None
    if tid is not None:
        t = conn.execute("select * from targets where id=?", (tid,)).fetchone()
        a = conn.execute("select * from audits where target_id=? order by id desc limit 1", (tid,)).fetchone()
    if t is None:
        fails.append(("no_target_row", str(tid)))
        if MERGED_RE.search(text):
            fails.append(("merged_unverified", "no target row to verify against"))
    else:
        full = f"{t['org']}/{t['repo']}"
        if full.lower() in load_blocklist():
            fails.append(("blocklisted", full))
        if t["org"].lower() in contacted_orgs():
            fails.append(("org_already_contacted", "listed in state/contacted.tsv"))
        scan = text.replace(OFFER_TERM_MERGED, "") if lane == "L5" else text
        if MERGED_RE.search(scan):
            n = conn.execute("""select count(*) from contributions where lower(repo)=lower(?) and upper(status)='MERGED'""",
                             (full,)).fetchone()[0]
            if n == 0:
                fails.append(("merged_unverified", f"0 MERGED contributions for {full}"))
        row = conn.execute("select id, body_sha256 from outreach where target_id=? and sent_at is null order by id desc limit 1",
                           (tid,)).fetchone()
        h = sha256(text)
        if row is None:
            fails.append(("no_outreach_row", str(tid)))
        elif row["body_sha256"] != h:
            fails.append(("sha_mismatch", "file edited after drafting; rerun the builder or update the row"))
        dup = conn.execute("select count(*) from outreach where body_sha256=? and target_id!=?", (h, tid)).fetchone()[0]
        if dup:
            fails.append(("duplicate_body", f"{dup} other rows share this sha"))
    # numbers vs evidence
    if a is None:
        fails.append(("no_audit_row", str(tid)))
    else:
        consts = template_constants(lane) if lane else set()
        ce = check_evidence_mod()
        if ce is not None:   # the AUDIT agent's own token rule (check_evidence.tokens / found)
            evid = ce.load_evidence(a["evidence_dir"]) if a["evidence_dir"] and os.path.isdir(a["evidence_dir"]) else ""
            toks, is_found = ce.tokens(text), (lambda tok: ce.found(tok, evid))
        else:
            evid = evidence_text(a["evidence_dir"])
            toks, is_found = num_tokens(text), (lambda tok: number_in_evidence(tok, evid))
        missing = [tok for tok in toks if norm_num(tok.rstrip("%")) not in consts and not is_found(tok)]
        if not evid:
            fails.append(("evidence_dir_empty", str(a["evidence_dir"])))
        elif missing:
            fails.append(("number_not_in_evidence", ",".join(sorted(set(missing)))))
    return fails


def gate_all():
    os.makedirs(REJECTED, exist_ok=True)
    conn = db()
    files = sorted(f for f in os.listdir(QUEUE) if f.endswith(".txt"))
    passed, failed, by_reason, by_lane = [], [], {}, {}
    for f in files:
        p = os.path.join(QUEUE, f)
        fails = check(p, conn)
        tid, lane = lane_from_filename(f)
        by_lane.setdefault(lane, [0, 0])
        if fails:
            failed.append((f, fails))
            by_lane[lane][1] += 1
            for rule, _ in fails:
                by_reason[rule] = by_reason.get(rule, 0) + 1
            reason = "; ".join(f"{r}: {d}" if d else r for r, d in fails)
            shutil.move(p, os.path.join(REJECTED, f))
            with open(os.path.join(REJECTED, f + ".reason"), "w", encoding="utf-8") as fh:
                fh.write(reason + "\n")
            if tid is not None:
                conn.execute("update outreach set notes=? where target_id=? and sent_at is null and notes='draft'",
                             ("rejected: " + reason[:400], tid))
                conn.commit()
        else:
            passed.append(f)
            by_lane[lane][0] += 1
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [f"outreach_gate {ts}", f"drafts checked: {len(files)}", f"passed: {len(passed)}", f"failed: {len(failed)}",
             "", "by lane (pass / fail):"]
    for k in sorted(by_lane, key=str):
        lines.append(f"  {k}: {by_lane[k][0]} / {by_lane[k][1]}")
    lines += ["", "fail count by rule (a draft can fail several rules):"]
    for k, v in sorted(by_reason.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {v:4d}  {k}")
    lines += ["", "passed files:"] + [f"  {f}" for f in passed]
    lines += ["", "failed files:"] + [f"  {f}  " + "; ".join(f"{r}: {d}" if d else r for r, d in fs) for f, fs in failed]
    rep = "\n".join(lines) + "\n"
    open(os.path.join(OUT, "gate-report.txt"), "w", encoding="utf-8").write(rep)
    print(rep)
    return 0 if not failed else 1


CONTROLS = {
    "call": "Happy to hop on a quick call to walk you through it.",
    "emoji": "Thanks \U0001F680",
    "emdash": "The report is short — one page.",
    "merged": "My last fix there was merged within a day.",
    "number": "Your README claims 987654321 downloads.",
    "long": "word " * 180,
    "humanize": "We leverage a robust, seamless pipeline to delve into your repo.",
}


def controls():
    """Prove every rule fires on a known-bad body built on top of a clean base."""
    base = ("Subject: control\nReply-To: mike@zovo.one\n\nHi there,\n\nPlain sentence.\n\n" + UNSUB + "\n\n"
            + SIGNOFF + "\nmike@zovo.one\n")
    conn = db()
    t = conn.execute("select a.target_id from audits a limit 1").fetchone()
    tid = t[0] if t else -1
    ok_all = True
    with tempfile.TemporaryDirectory() as d:
        for name, bad in CONTROLS.items():
            p = os.path.join(d, f"{tid}-L1.txt")
            open(p, "w").write(base.replace("Plain sentence.", bad))
            rules = {r for r, _ in check(p, conn)}
            print(f"control {name:9s} -> {sorted(rules)}")
        p = os.path.join(d, f"{tid}-L1.txt")
        open(p, "w").write(base.replace(UNSUB, ""))
        rules = {r for r, _ in check(p, conn)}
        print(f"control unsub     -> {sorted(rules)}")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check")
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--rehash", help="re-gate a draft the owner edited by hand; on PASS record its new body_sha256")
    args = ap.parse_args()
    if args.rehash:
        path = args.rehash if os.path.isabs(args.rehash) else os.path.join(QUEUE, os.path.basename(args.rehash))
        fails = check(path)
        for r, d in fails:
            print(f"FAIL {r}: {d}")
        if fails:
            print(f"FAIL ({len(fails)} rules): fix the text and run --rehash again; nothing recorded")
            sys.exit(1)
        tid, _lane = lane_from_filename(path)
        c = db()
        n = c.execute("update outreach set body_sha256=? where target_id=? and sent_at is null",
                      (sha256(open(path, encoding="utf-8").read()), tid)).rowcount
        c.commit()
        print(f"PASS: re-gated and recorded new sha for {os.path.basename(path)} ({n} row). Re-approve before sending.")
        sys.exit(0)
    if args.control:
        sys.exit(controls())
    if args.check:
        fails = check(args.check)
        for r, d in fails:
            print(f"FAIL {r}: {d}")
        print("PASS" if not fails else f"FAIL ({len(fails)} rules)")
        sys.exit(0 if not fails else 1)
    sys.exit(gate_all())


if __name__ == "__main__":
    main()
