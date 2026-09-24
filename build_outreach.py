#!/usr/bin/env python3
"""WhiteHERO v3 outreach drafter (plan section 5, Phase 2 steps 2.1 and 2.2).

For every target with an audits row and a contact_email, pick a lane, fill the lane
template with the top 3 measured findings from the audit report (numbers quoted exactly
as the report writes them), write outreach/queue/<target_id>-<lane>.txt and insert an
outreach row (channel 'email', sent_at NULL, notes 'draft').

Nothing is sent. Rules enforced in code:
  one draft per org ever (any lane, any state except 'rejected' when --redraft-rejected);
  orgs listed in state/contacted.tsv (emailed outside this pipeline) count as already contacted
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
                          db_lane, contacted_orgs, split_email, word_count, evidence_text, number_in_evidence, template_constants)

sys.path.insert(0, os.path.join(PIPE, "tools"))
try:
    from humanize_scan import scan_text as _hz_scan
except Exception:  # scanner missing means we cannot pre-screen; the gate still runs it
    _hz_scan = None

BANNED_WORDS = re.compile(r"\b(calls?|zoom|meet|meeting|hop on|calendly|schedule a|merged)\b", re.I)
# L1 buyer persona is a 5 to 50 developer company; mega-corp websites and orgs are skipped (lead, 2026-09-24)
MEGA_HOST_SUFFIXES = ("microsoft.com", "google", "google.com", "nvidia.com", "amazon.com", "aws.amazon.com",
                      "ycombinator.com", "bloomberg.com", "techatbloomberg.com", "hashicorp.com", "ibm.com", "oracle.com", "meta.com",
                      "facebook.com", "apple.com")
MEGA_ORGS = {"microsoft", "google", "googleapis", "aws", "amzn", "nvidia", "facebook", "meta", "apple", "ibm", "oracle"}


def is_mega_corp(t):
    from urllib.parse import urlparse
    w = (t["website"] or "").strip()
    host = (urlparse(w if "://" in w else "https://" + w).hostname or "").lower().rstrip(".") if w else ""
    if host and any(host == suf or host.endswith("." + suf) for suf in MEGA_HOST_SUFFIXES):
        return f"website {host}"
    if (t["org"] or "").lower() in MEGA_ORGS:
        return f"org {t['org']}"
    return None


ROLE_EXCLUDED = re.compile(r"^(support|help|security|privacy|legal|abuse|no-?reply|careers?|jobs?|hr|press|media|billing|dmca|compliance|postmaster|webmaster|unsubscribe|notifications?)$", re.I)


# ---------------------------------------------------------------- findings
# The audit agent (audit_report.py) writes reports/<org>__<repo>.md from evidence/drift.json and
# evidence/locale.json. Findings are rebuilt here from the same JSON with the report's own number
# formats (percent with one decimal, plain integers), and every number is then required to appear
# verbatim in the report text, so the email quotes the report exactly.
def _pct(v):
    return f"{v:.1f}%"


def _load(evidence_dir, name):
    p = os.path.join(evidence_dir or "", name)
    try:
        return json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _link_sentence(f):
    where = f"{f['file']} line {f['line_no']}"
    if f["check"] == "b_missing_relative_target":
        return f"{where} links to {f['claimed']}, a path that does not exist in the repo."
    m = f.get("measured") or ""
    if m.startswith("HTTP"):
        return f"{where} links to {f['claimed']}, which returns {m}."
    if "DNS" in m:
        return f"{where} links to {f['claimed']}, whose domain no longer resolves."
    return f"{where} links to {f['claimed']}, which is dead ({m})."


def findings_for(audit, kinds=("stale", "links", "locale")):
    """Return (findings, facts). findings is an ordered list of sentences; facts holds the
    structured values the lane logic and subject line need."""
    ev = audit["evidence_dir"]
    dr = _load(ev, "drift.json") or {}
    loc = _load(ev, "locale.json") or {}
    F = dr.get("findings", [])
    stale = [f for f in F if f["check"] in ("c_version_drift", "d_count_claim", "e_engine_claim")]
    broken = [f for f in F if f["check"] in ("a_dead_link", "b_missing_relative_target")]
    cc = dr.get("counts", {})
    facts = {"stale": len(stale), "broken": len(broken), "links_checked": cc.get("links_checked"),
             "rel_checked": cc.get("relative_links_checked"), "english_only": loc.get("english_only"),
             "en_keys": loc.get("en_keys"), "worst_tier1": loc.get("worst_tier1"), "tier1": loc.get("tier1") or {},
             "total_gap": loc.get("total_gap_keys"), "n_measured": loc.get("n_locales_measured"),
             "locale_group": loc.get("locale_group")}
    out = []
    if "stale" in kinds:
        for f in stale[:3]:
            out.append(f"README line {f['line_no']} claims {f['claimed']}, but the repo measures {f['measured']}.")
    if "links" in kinds and broken:
        if len(broken) >= 2 and facts["links_checked"] is not None:
            ext, rel = facts["links_checked"], facts["rel_checked"] or 0
            tail = f"{ext} external link{'s' if ext != 1 else ''}" + (f" and {rel} relative link{'s' if rel != 1 else ''}" if rel else "")
            out.append(f"Your README and docs have {len(broken)} broken links, out of {tail} checked.")
        # README links first, then short URLs, so the example reads cleanly in a plain-text email
        for f in sorted(broken, key=lambda f: (f["file"] != "README.md", len(f["claimed"]) > 70))[:2]:
            out.append(_link_sentence(f))
    if "locale" in kinds:
        eo = facts["english_only"]
        if eo and eo.get("en_keys"):
            out.append(f"{eo['src_files'][0]} holds {eo['en_keys']} English keys, and its locale folder holds no other language.")
        wt = facts["worst_tier1"]
        if wt and facts["locale_group"] and facts["en_keys"] and wt.get("gap_keys"):
            out.append(f"Your {wt['locale']} locale is {_pct(wt['gap_pct'])} untranslated "
                       f"({wt['gap_keys']} of {facts['en_keys']} keys missing or identical to English).")
            others = sorted((v for k, v in facts["tier1"].items() if v and v.get("locale") != wt["locale"] and v.get("gap_keys")),
                            key=lambda v: -v["gap_pct"])
            if others:
                o = others[0]
                out.append(f"The {o['locale']} locale is {_pct(o['gap_pct'])} untranslated ({o['gap_keys']} keys).")
        if facts["locale_group"] and facts["total_gap"]:
            out.append(f"Across the {facts['n_measured']} locales measured, {facts['total_gap']} keys are untranslated.")
    return out, facts


def quoted_from_report(finding, report_text):
    """Every number in the finding must appear in the report as written."""
    for tok in num_tokens(finding):
        if not re.search(r"(?<![\d.])" + re.escape(tok) + r"(?![\d])", report_text):
            return False
    return True


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
def pct_value(p):
    if p is None:
        return None
    p = float(p)
    return p * 100 if p <= 1.0 else p


def base_lang(loc):
    return re.split(r"[-_]", (loc or "").strip().lower())[0]


def is_english_only(facts):
    """English-only flagship: the audit found an English source with no other language beside it,
    holding at least 300 keys, outside example or demo apps."""
    eo = facts.get("english_only")
    if not eo or (eo.get("languages") or []) != ["en"]:
        return False
    if (eo.get("en_keys") or 0) < 300:
        return False
    return not re.search(r"(example|demo|sample|fixture|test)", " ".join(eo.get("src_files") or []), re.I)


def pick_lane(t, a, facts):
    if is_english_only(facts):
        return "L2a", "english-only flagship"
    B = t["B"] or 0
    drift = (a["stale_claims"] or 0) + (a["failing_examples"] or 0)
    if (t["owner_type"] or "") == "Organization" and B >= 0.4 and drift >= 3:
        return "L1", f"org B={B:.2f} drift={drift}"
    wp = pct_value(a["worst_pct"])
    tms = (t["tms"] or "").strip().lower()
    if base_lang(a["worst_locale"]) in TIER1 and wp is not None and wp >= 20 and tms in ("", "none", "no", "null"):
        return "L2b", f"tier-1 {a['worst_locale']} {wp:.1f}% no TMS"
    return None, (f"no lane (owner={t['owner_type']} B={B} drift={drift} worst={a['worst_locale']} "
                  f"{wp} tms={tms or '-'})")


LANE_KINDS = {"L1": ("stale", "links", "locale"), "L2a": ("locale", "stale", "links"), "L2b": ("locale",)}


def subject_fact(lane, a, facts, report_text):
    """Short subject phrase carrying one measured number, written as the report writes it."""
    cands = []
    if lane == "L1":
        if facts["stale"]:
            n = facts["stale"]
            cands.append((str(n), f"{n} stale README claim{'s' if n != 1 else ''}"))
        if facts["broken"]:
            n = facts["broken"]
            cands.append((str(n), f"{n} broken doc link{'s' if n != 1 else ''}"))
    elif lane == "L2a":
        n = (facts.get("english_only") or {}).get("en_keys")
        if n:
            cands.append((str(n), f"{n} English-only strings"))
    elif lane == "L2b":
        wt = facts.get("worst_tier1")
        if wt:
            p = _pct(wt["gap_pct"])
            cands.append((p[:-1], f"{p} of the {wt['locale']} UI untranslated"))
    for tok, phrase in cands:
        if re.search(r"(?<![\d.])" + re.escape(tok) + r"(?![\d])", report_text):
            return phrase
    return None


def greeting(t):
    name = (t["contact_name"] or "").strip()
    if name and re.match(r"^[A-Za-zÀ-ÿ'’-]{2,}", name):
        return name.split()[0]
    return "there"


def fill(lane, t, a, findings, subj, locale=""):
    tpl = open(template_path(lane), encoding="utf-8").read()
    repo = f"{t['org']}/{t['repo']}"
    vals = {
        "subject_fact": subj, "repo": repo, "greeting": greeting(t),
        "finding_1": findings[0], "finding_2": findings[1], "finding_3": findings[2],
        "locale": locale or a["worst_locale"] or "",
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
    block = load_blocklist()
    contacted = contacted_orgs()
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
        mega = is_mega_corp(r)
        if mega:
            skip(f"mega-corp: {mega}", r); continue
        if re.search(r"github", r["contact_source"] or "", re.I):
            skip("contact from GitHub (AUP 4)", r); continue
        em = r["contact_email"].strip()
        if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", em) or re.match(r"^u00[0-9a-f]{2}", em, re.I):
            skip("bad email", r); continue
        if ROLE_EXCLUDED.match(em.split("@")[0]):
            skip("role address not for sales (jobs, support, ...)", r); continue
        if r["org"].lower() in contacted:
            skip("org already contacted (state/contacted.tsv)", r); continue
        prior = c.execute("""select o.id, o.notes, o.sent_at from outreach o join targets t2 on t2.id=o.target_id
                             where lower(t2.org)=lower(?)""", (r["org"],)).fetchall()
        live_prior = [p for p in prior if not (args.redraft_rejected and p["sent_at"] is None
                                                and (p["notes"] or "").startswith("rejected"))]
        if live_prior:
            skip("org already has an outreach row", r); continue
        if any(m["org"].lower() == r["org"].lower() for m in made):
            skip("org already drafted this run", r); continue

        evid = evidence_text(r["evidence_dir"])
        if not evid:
            skip("evidence dir empty or missing", r); continue
        try:
            report_text = open(r["report_path"], encoding="utf-8").read()
        except (OSError, TypeError):
            skip("report missing", r); continue
        _, facts = findings_for(r)
        lane, why = pick_lane(r, r, facts)
        if not lane:
            skip(why, r); continue
        bucket = db_lane(lane)
        cap = args.max_l1 if bucket == "L1" else args.max_l2
        if counts[bucket] >= cap:
            skip(f"{bucket} cap reached", r); continue

        allf, _ = findings_for(r, LANE_KINDS[lane])
        good = []
        for f in allf:
            ok, why_bad = usable(f, evid)
            if ok and not quoted_from_report(f, report_text):
                ok = False
            if ok:
                good.append(f)
        if len(good) < 3:
            skip(f"fewer than 3 measured findings ({len(good)} usable of {len(allf)})", r); continue
        subj = subject_fact(lane, r, facts, report_text)
        if not subj:
            skip("no subject number found in report", r); continue
        loc = (facts.get("worst_tier1") or {}).get("locale", "")
        body = fill(lane, r, r, good[:3], subj, loc)
        if word_count(split_email(body)[1]) > 170:
            shorter = sorted(good, key=lambda g: len(g.split()))[:3]
            body = fill(lane, r, r, shorter, subj, loc)
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
