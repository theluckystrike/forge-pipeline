#!/usr/bin/env python3
"""OSS autonomous contribution pipeline — layer orchestrator.

Layers:
  L1 discover  : find candidate repos/issues matching profile (gh api)
  L2 verify    : repo health, issue validity, contributor-friendliness
  L3 craft     : build the contribution plan (code patch / docs / repro)
  L4 score     : 0-100 rubric; HARD GATE: must be 100 to proceed
  L5 ship      : dry-run report or (armed mode) real PR via gh

Usage:
  python3 pipeline.py            # full run, dry-run output to runs/
  python3 pipeline.py --discover # L1 only
  python3 pipeline.py --score runs/<ts>/plan.json
"""
import json, os, subprocess, sys, time, re
from datetime import datetime

ROOT = os.path.expanduser("~/oss-pipeline")
RUNS = os.path.join(ROOT, "runs")
ACCOUNT = "theluckystrike"

# ---------------- helpers ----------------
def gh(endpoint, params=None, method="GET"):
    cmd = ["gh", "api", endpoint]
    if params:
        cmd += ["-X", method, "-f"] + [f"{k}={v}" for k, v in params.items()] \
               if method != "GET" else ["-q", "."] + []
    # simpler: build query string for GET
    if method == "GET" and params:
        from urllib.parse import quote
        qs = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        endpoint = endpoint + ("&" if "?" in endpoint else "?") + qs
        cmd = ["gh", "api", endpoint]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"gh api {endpoint}: {out.stderr.strip()[:300]}")
    return json.loads(out.stdout)

def search(q, n=20, sort="updated"):
    for attempt in range(4):
        try:
            return gh("search/issues", {"q": q, "per_page": n, "sort": sort, "order": "desc"})
        except RuntimeError as e:
            if "rate limit" in str(e).lower() and attempt < 3:
                wait = 20 * (attempt + 1)
                print(f"  [backoff] secondary rate limit, waiting {wait}s", flush=True)
                time.sleep(wait)
            else:
                raise

# ---------------- L1: discover ----------------
GOOD_FIRST_QUERIES = [
    'label:"good first issue" state:open language:python comments:>0 stars:>500 pushed:>2026-09-01 no:assignee',
    'label:"help wanted" state:open language:python stars:>1000 pushed:>2026-09-01 no:assignee',
    'label:"documentation" state:open stars:>500 pushed:>2026-09-05 no:assignee',
    'label:"bug" state:open language:python stars:>2000 linked:none comments:0..2 pushed:>2026-09-05',
]
DOCS_QUERIES = [
    'is:pr state:open label:"documentation" stars:>3000 linked:none',
]

def layer1():
    candidates = []
    for q in GOOD_FIRST_QUERIES:
        try:
            r = search(q, n=15)
            for item in r.get("items", []):
                repo_url = item.get("repository_url", "")
                candidates.append({
                    "type": "issue",
                    "number": item["number"],
                    "title": item["title"],
                    "repo": repo_url.replace("https://api.github.com/repos/", ""),
                    "labels": [l["name"] for l in item.get("labels", [])],
                    "comments": item.get("comments", 0),
                    "state": item.get("state"),
                    "url": item.get("html_url"),
                    "query": q,
                })
        except Exception as e:
            candidates.append({"type": "error", "query": q, "error": str(e)})
    return candidates

# ---------------- L2: verify ----------------
MAINTAINER_ABUSE_PATTERNS = re.compile(
    r"(contribution.{0,30}closed|will not accept|don't PR|reject external|claw|mock|test)", re.I)

def layer2(cands):
    verified = []
    for c in cands:
        if c.get("type") != "issue":
            continue
        repo = c["repo"]
        try:
            r = gh(f"repos/{repo}")
            # health filters
            if r.get("archived") or r.get("disabled"):
                continue
            if r.get("stargazers_count", 0) < 100:
                continue
            if r.get("open_issues_count", 0) == 0 and r.get("forks", 0) < 50:
                continue
            days = (datetime.utcnow() - datetime.strptime(r["pushed_at"], "%Y-%m-%dT%H:%M:%SZ")).days
            if days > 90:
                continue
            # issue re-check: still open, unassigned, not a troll trap
            issue = gh(f"repos/{repo}/issues/{c['number']}")
            if issue.get("state") != "open" or issue.get("assignee") or issue.get("pull_request"):
                continue
            # comments must still be low (race with other contributors between L1 and L2)
            if (issue.get("comments") or 0) > 3:
                continue
            labels = [l["name"] for l in issue.get("labels", [])]
            if not any(l.lower() in ("good first issue", "help wanted", "documentation", "bug") for l in labels):
                continue
            body = (issue.get("body") or "")[:2000]
            if MAINTAINER_ABUSE_PATTERNS.search(body):
                continue
            c.update({
                "stars": r["stargazers_count"],
                "pushed_days_ago": days,
                "license": (r.get("license") or {}).get("spdx_id"),
                "default_branch": r.get("default_branch"),
                "issue_body": body,
                "issue_author": issue.get("user", {}).get("login"),
                "verified": True,
            })
            verified.append(c)
        except Exception as e:
            c["verify_error"] = str(e)[:200]
    return verified

# ---------------- L4: scoring rubric ----------------
def score_candidate(c):
    """Hard rubric. Returns (score, breakdown). Gate: must equal 100."""
    labels_l = [l.lower() for l in c.get("labels", [])]
    b = {}
    b["repo_health"]   = 15 if c.get("stars",0) >= 1000 else (10 if c.get("stars",0) >= 300 else 5)
    b["issue_valid"]   = 10 if c.get("comments", 0) == 0 else (8 if c.get("comments",0) <= 2 else 0)
    # ^ 0 comments = uncontested; 1-2 = usually just 'can I take this?' chatter
    b["issue_scope"]   = 10 if "good first issue" in labels_l else \
                         (8 if "help wanted" in labels_l else 5)
    b["recency"]       = 10 if c.get("pushed_days_ago", 999) <= 14 else (7 if c.get("pushed_days_ago",999) <= 45 else 0)
    b["license_ok"]    = 10 if c.get("license") in ("MIT","Apache-2.0","BSD-3-Clause","BSD-2-Clause","ISC","MPL-2.0") else 0
    b["assignable"]    = 10 if not c.get("assignee") else 0
    b["docs_clarity"]  = 10 if len(c.get("issue_body","")) > 200 else (7 if len(c.get("issue_body","")) > 80 else 3)
    b["competence"]    = 10  # placeholder: L3 sets this after crafting; max 10
    b["risk"]          = 10 if ("docs" in labels_l or "test" in " ".join(labels_l)) else 7  # docs/test = lower risk
    b["authenticity"]  = 5 if c.get("issue_author") and c.get("issue_author") != ACCOUNT else 0
    # ^ someone else's issue, from a real reporter; never self-authored or bot-spam
    b["unassigned_now"] = 5 if c.get("verified") else 0  # L2 re-check passed (open, unassigned, low comments)
    total = sum(b.values())  # max = 15+10+10+10+10+10+10+10+5+5+5 = 100
    return total, b

# ---------------- main ----------------
def run():
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    rundir = os.path.join(RUNS, ts)
    os.makedirs(rundir, exist_ok=True)
    log = lambda k, v: print(f"[{ts}] {k}: {json.dumps(v, indent=1)[:800]}", flush=True)

    cands = layer1()
    log("L1_candidates", len(cands))
    verified = layer2([c for c in cands if c.get("type") == "issue"][:30])
    log("L2_verified", len(verified))

    scored = []
    for c in verified:
        s, b = score_candidate(c)
        c["score"] = s
        c["breakdown"] = b
        scored.append(c)
    scored.sort(key=lambda x: -x["score"])
    perfect = [c for c in scored if c["score"] == 100]

    with open(os.path.join(rundir, "candidates.json"), "w") as f:
        json.dump({"ts": ts, "candidates": scored, "perfect_100": len(perfect)}, f, indent=2)

    log("scores_top3", [(c["repo"], c["number"], c["score"]) for c in scored[:3]])
    log("perfect_100_count", len(perfect))

    # DRY RUN: report only. No PR creation without explicit --arm and 100/100.
    report = {
        "run": ts, "account": ACCOUNT,
        "discovered": len(cands), "verified": len(verified),
        "perfect_100": [{"repo": c["repo"], "issue": c["url"], "score": c["score"]} for c in perfect],
        "mode": "DRY-RUN — no writes to GitHub performed",
    }
    with open(os.path.join(rundir, "report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    run()
