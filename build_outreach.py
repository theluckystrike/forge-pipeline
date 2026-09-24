#!/usr/bin/env python3
"""WhiteHERO v3 outreach drafter (plan section 5, Phase 2 steps 2.1 and 2.2).

For every target with an audits row and a contact_email, pick a lane, fill the lane
template with the top 3 measured findings from the audit report (numbers quoted exactly
as the report writes them), write outreach/queue/<target_id>-<lane>.txt and insert an
outreach row (channel 'email', sent_at NULL, notes 'draft').

Nothing is sent. Rules enforced in code:
  one draft per org ever (any lane, any state except 'rejected' when --redraft-rejected)
  body_sha256 unique across the outreach table
  blocklisted repos skipped (state/blocklist.txt)
  audits with fewer than 3 measured findings skipped
  contacts whose source is GitHub skipped (AUP section 4)
  L4 and L5 are manual lanes and are never drafted here

Usage:
  python3 build_outreach.py [--max-l1 40] [--max-l2 20] [--dry-run] [--redraft-rejected]
"""
import argparse, json, os, re, sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from outreach_lib import (PIPE, OUT, QUEUE, TIER1, db, sha256, num_tokens, template_path, load_blocklist,
                          db_lane, split_email, word_count, evidence_text, number_in_evidence, template_constants)

sys.path.insert(0, os.path.join(PIPE, "tools"))
try:
    from humanize_scan import scan_text as _hz_scan
except Exception:  # scanner missing means we cannot pre-screen; the gate still runs it
    _hz_scan = None

SEED_LOCALE = os.path.join(PIPE, "seed", "locale_results.jsonl")
BANNED_WORDS = re.compile(r"\b(calls?|zoom|meet|meeting|hop on|calendly|schedule a|merged)\b", re.I)
EN_ONLY_TAGS = {None, "", "none", "en", "en-only", "english-only", "english", "n/a"}


# ---------------------------------------------------------------- findings
def _clean_line(ln):
    ln = re.sub(r"^\s*(?:[-*+]|\d+[.)])\s+", "", ln)          # bullet or ordinal
    ln = re.sub(r"\*\*([^*]+)\*\*", r"\1", ln)                   # bold
    ln = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", r"\1", ln)         # italics
    ln = ln.replace("`", "")
    ln = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", ln)            # md links keep text
    ln = re.sub(r"\s+", " ", ln).strip()
    return ln


def _sentence(t):
    t = t.strip().rstrip(";,:")
    if not t:
        return t
    if t[0].islower() and not re.match(r"^[a-z0-9_.-]+/[a-z0-9_.-]+", t):
        t = t[0].upper() + t[1:]
    if t[-1] not in ".?":
        t += "."
    return t


def _findings_from_json(evidence_dir):
    for name in ("findings.json", "findings.jsonl"):
        p = os.path.join(evidence_dir or "", name)
        if not os.path.isfile(p):
            continue
        raw = open(p, encoding="utf-8").read()
        try:
            data = json.loads(raw)
        except ValueError:
            data = [json.loads(l) for l in raw.splitlines() if l.strip()]
        if isinstance(data, dict):
            data = data.get("findings", [])
        out = []
        for f in data:
            if isinstance(f, str):
                out.append(f)
            elif isinstance(f, dict):
                txt = f.get("sentence") or f.get("text") or f.get("finding") or f.get("summary")
                if txt and f.get("measured", True) is not False:
                    out.append(txt)
        return out
    return None


SECTION_OK = re.compile(r"(finding|measured|stale|claim|example|locale|gap|drift|parity|result|summary)", re.I)
SECTION_SKIP = re.compile(r"(command|how|method|reproduc|evidence|appendix|raw|note|caveat|next step|offer|price)", re.I)


def _findings_from_report(report_path):
    """Measured findings = bullet or numbered lines containing a number, inside a findings-like
    section when the report has sections. Order is the report's own order (the report ranks)."""
    if not report_path or not os.path.isfile(report_path):
        return []
    lines = open(report_path, encoding="utf-8", errors="replace").read().splitlines()
    has_sections = any(re.match(r"^#{1,4}\s", l) for l in lines)
    ok_section = not has_sections
    out, in_code = [], False
    for l in lines:
        if l.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        h = re.match(r"^#{1,4}\s+(.*)", l)
        if h:
            title = h.group(1)
            ok_section = bool(SECTION_OK.search(title)) and not SECTION_SKIP.search(title)
            continue
        if not ok_section:
            continue
        if not re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", l):
            continue
        t = _clean_line(l)
        if not num_tokens(t):
            continue
        if re.search(r"(\$ |^\$|evidence/|\.txt\b|\.json\b|command:|cmd:)", t, re.I):
            continue
        out.append(t)
    return out


def findings_for(audit):
    f = _findings_from_json(audit["evidence_dir"])
    if f is None:
        f = _findings_from_report(audit["report_path"])
    return [_sentence(x) for x in f if x and x.strip()]


def usable(finding, evid, max_words=32):
    """A finding can go in an email when it is short, passes the prose scan, has no banned
    outreach word, and every number in it is present in the evidence dir."""
    if len(finding.split()) > max_words:
        return False, "too long"
    if BANNED_WORDS.search(finding):
        return False, "banned word"
    if "—" in finding or "--" in finding or "!" in finding:
        return False, "punctuation"
    if _hz_scan is not None and _hz_scan(finding, False):
        return False, "humanize"
    toks = num_tokens(finding)
    if not toks:
        return False, "no number"
    miss = [t for t in toks if not number_in_evidence(t, evid)]
    if miss:
        return False, "number not in evidence: " + ",".join(miss)
    return True, ""


# ---------------------------------------------------------------- lanes
def seed_locale_counts():
    d = {}
    if os.path.exists(SEED_LOCALE):
        for l in open(SEED_LOCALE, encoding="utf-8"):
            try:
                r = json.loads(l)
                d[r["repo"].lower()] = r.get("n_locales")
            except Exception:
                pass
    return d


def pct_value(p):
    if p is None:
        return None
    p = float(p)
    return p * 100 if p <= 1.0 else p


def base_lang(loc):
    return re.split(r"[-_]", (loc or "").strip().lower())[0]


def is_english_only(t, a, seed):
    wl = (a["worst_locale"] or "").strip().lower() or None
    gap = a["locale_gap_keys"] or 0
    if gap <= 0:
        return False
    if wl in EN_ONLY_TAGS:
        n = seed.get(f"{t['org']}/{t['repo']}".lower())
        return n in (None, 0) or wl in {"en-only", "english-only"}
    return False


def pick_lane(t, a, seed):
    if is_english_only(t, a, seed):
        return "L2a", "english-only flagship"
    B = t["B"] or 0
    drift = (a["stale_claims"] or 0) + (a["failing_examples"] or 0)
    if (t["owner_type"] or "") == "Organization" and B >= 0.4 and drift >= 3:
        return "L1", f"org B={B:.2f} drift={drift}"
    wp = pct_value(a["worst_pct"])
    tms = (t["tms"] or "").strip().lower()
    if base_lang(a["worst_locale"]) in TIER1 and wp is not None and wp >= 20 and tms in ("", "none", "no", "null"):
        return "L2b", f"tier-1 {a['worst_locale']} {wp:.1f}% no TMS"
    return None, f"no lane (owner={t['owner_type']} B={B} drift={drift} worst={a['worst_locale']} {wp} tms={tms or '-'})"


def fmt_pct(p):
    s = f"{p:.1f}"
    return s[:-2] if s.endswith(".0") else s


def subject_fact(lane, a, findings, evid):
    """Short subject phrase carrying one measured number that the evidence dir contains."""
    cands = []
    if lane == "L1":
        if a["stale_claims"]:
            n = a["stale_claims"]
            cands.append((str(n), f"{n} stale numeric claim{'s' if n != 1 else ''}"))
        if a["failing_examples"]:
            n = a["failing_examples"]
            cands.append((str(n), f"{n} failing example{'s' if n != 1 else ''}"))
    elif lane == "L2a":
        n = a["locale_gap_keys"]
        if n:
            cands.append((str(n), f"{n:,} English-only strings"))
            cands.append((str(n), f"{n} English-only strings"))
    elif lane == "L2b":
        wp = pct_value(a["worst_pct"])
        if wp is not None:
            p = fmt_pct(wp)
            cands.append((p, f"{p}% of the {a['worst_locale']} UI untranslated"))
    for tok, phrase in cands:
        if number_in_evidence(tok, evid) or number_in_evidence(f"{int(float(tok)):,}" if tok.isdigit() else tok, evid):
            return phrase
    return None


def greeting(t):
    name = (t["contact_name"] or "").strip()
    if name and re.match(r"^[A-Za-zÀ-ÿ'’-]{2,}", name):
        return name.split()[0]
    return "there"


def fill(lane, t, a, findings, subj):
    tpl = open(template_path(lane), encoding="utf-8").read()
    repo = f"{t['org']}/{t['repo']}"
    vals = {
        "subject_fact": subj, "repo": repo, "greeting": greeting(t),
        "finding_1": findings[0], "finding_2": findings[1], "finding_3": findings[2],
        "locale": a["worst_locale"] or "",
    }
    out = tpl
    for k, v in vals.items():
        out = out.replace("{" + k + "}", v)
    if re.search(r"\{[a-z_0-9]+\}", out):
        raise ValueError("unfilled placeholder: " + ",".join(re.findall(r"\{[a-z_0-9]+\}", out)))
    return out


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-l1", type=int, default=40)
    ap.add_argument("--max-l2", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true", help="write nothing, print decisions")
    ap.add_argument("--redraft-rejected", action="store_true",
                    help="allow a new draft for an org whose only row is a gate-rejected unsent draft")
    args = ap.parse_args()

    os.makedirs(QUEUE, exist_ok=True)
    c = db()
    seed = seed_locale_counts()
    block = load_blocklist()
    rows = c.execute("""
        select t.*, a.id as audit_id, a.stale_claims, a.failing_examples, a.locale_gap_keys, a.worst_locale,
               a.worst_pct, a.report_path, a.evidence_dir, a.created_at as audit_at
        from targets t join audits a on a.target_id = t.id
        where t.contact_email is not null and trim(t.contact_email) != ''
        order by coalesce(t.score, 0) desc, a.id desc""").fetchall()

    seen_target = set()
    existing_sha = {r[0] for r in c.execute("select body_sha256 from outreach where body_sha256 is not null")}
    counts = {"L1": 0, "L2": 0}
    skips = {}
    made = []

    def skip(reason, t):
        key = reason.split(":")[0].split(" (")[0]
        skips.setdefault(key, []).append(f"{t['org']}/{t['repo']} {reason}")

    for r in rows:
        if r["id"] in seen_target:   # several audits per target: newest only
            continue
        seen_target.add(r["id"])
        full = f"{r['org']}/{r['repo']}".lower()
        if full in block:
            skip("blocklisted", r); continue
        if re.search(r"github", r["contact_source"] or "", re.I):
            skip("contact from GitHub (AUP 4)", r); continue
        if not re.match(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$", r["contact_email"].strip()):
            skip("bad email", r); continue
        prior = c.execute("""select o.id, o.notes, o.sent_at from outreach o join targets t2 on t2.id=o.target_id
                             where lower(t2.org)=lower(?)""", (r["org"],)).fetchall()
        live_prior = [p for p in prior if not (args.redraft_rejected and p["sent_at"] is None
                                                and (p["notes"] or "").startswith("rejected"))]
        if live_prior:
            skip("org already has an outreach row", r); continue
        if any(m["org"].lower() == r["org"].lower() for m in made):
            skip("org already drafted this run", r); continue

        lane, why = pick_lane(r, r, seed)
        if not lane:
            skip(why, r); continue
        bucket = db_lane(lane)
        cap = args.max_l1 if bucket == "L1" else args.max_l2
        if counts[bucket] >= cap:
            skip(f"{bucket} cap reached", r); continue

        evid = evidence_text(r["evidence_dir"])
        if not evid:
            skip("evidence dir empty or missing", r); continue
        allf = findings_for(r)
        good, bad = [], []
        for f in allf:
            ok, why_bad = usable(f, evid)
            (good if ok else bad).append((f, why_bad))
        if len(good) < 3:
            skip(f"fewer than 3 measured findings ({len(good)} usable of {len(allf)})", r); continue
        top = [g[0] for g in good[:3]]
        subj = subject_fact(lane, r, top, evid)
        if not subj:
            skip("no subject number found in evidence", r); continue
        body = fill(lane, r, r, top, subj)
        hdr, main_body = split_email(body)
        if word_count(main_body) > 170:
            # try shorter findings before giving up
            shorter = sorted(good, key=lambda g: len(g[0].split()))[:3]
            body = fill(lane, r, r, [g[0] for g in shorter], subj)
            if word_count(split_email(body)[1]) > 170:
                skip("over 170 words with shortest findings", r); continue
        h = sha256(body)
        if h in existing_sha:
            skip("duplicate body sha", r); continue
        fn = os.path.join(QUEUE, f"{r['id']}-{lane}.txt")
        made.append({"org": r["org"], "repo": r["repo"], "id": r["id"], "lane": lane, "file": fn, "sha": h})
        counts[bucket] += 1
        existing_sha.add(h)
        if args.dry_run:
            print(f"DRY {lane} {r['org']}/{r['repo']} -> {fn}")
            continue
        with open(fn, "w", encoding="utf-8") as fh:
            fh.write(body)
        if args.redraft_rejected:
            c.execute("""delete from outreach where target_id in (select id from targets where lower(org)=lower(?))
                         and sent_at is null and notes like 'rejected%'""", (r["org"],))
        c.execute("""insert into outreach(target_id, lane, channel, body_sha256, sent_at, notes)
                     values(?,?,?,?,NULL,'draft')""", (r["id"], bucket, "email", h))
        c.commit()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [f"build_outreach {ts}", f"candidate rows (targets with audit and contact_email): {len(rows)}",
             f"distinct targets considered: {len(seen_target)}",
             "drafted: " + ", ".join(f"{k}={sum(1 for m in made if m['lane']==k)}" for k in ("L1", "L2a", "L2b")),
             "skipped by reason:"]
    for k, v in sorted(skips.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"  {len(v):4d}  {k}")
    report = "\n".join(lines)
    print(report)
    if not args.dry_run:
        with open(os.path.join(OUT, "build-report.txt"), "w", encoding="utf-8") as fh:
            fh.write(report + "\n\nskip detail\n")
            for k, v in sorted(skips.items()):
                for x in v:
                    fh.write(f"{k}\t{x}\n")


if __name__ == "__main__":
    main()
