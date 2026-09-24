#!/usr/bin/env python3
"""Widened L1 discovery prototype for FORGE sprint W23+ (final).

Two widened axes beyond the standard pipeline queries:
  AXIS_A  chatter-eligible  accept unassigned issues with 1-2 claim-chatter
          comments where NO comment links to a real PR (no genuine contention).
  AXIS_B  docs-only axis    label:"documentation" open unassigned, star tier
          just above the 300 repo_health boundary so a clean docs issue can
          reach exactly 100/100.

All GitHub calls carry exponential backoff on the 403 secondary rate limit.
Repo metadata cached per repo; comments only fetched for candidates whose
non-comment base score already reaches the 100 threshold headroom.

Run as: python3 state/widen_proto.py
"""
import json, subprocess, time, sys, urllib.parse
from datetime import datetime, timezone

SLEEP = 1.0
_repo_cache = {}

def gh_raw(args, timeout=60, max_tries=5):
    """Run gh api with backoff on 403 secondary rate limit."""
    for attempt in range(max_tries):
        r = subprocess.run(["gh", "api"] + args, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0:
            return r
        if "rate limit" in (r.stderr or "").lower() or "403" in (r.stderr or ""):
            wait = 15 * (attempt + 1)
            time.sleep(wait)
            continue
        return r
    return r

def gh_json(args):
    r = gh_raw(args)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None

def repo_meta(repo):
    if repo in _repo_cache:
        return _repo_cache[repo]
    d = gh_json(["repos/" + repo, "-q", "."])
    meta = {"stars": 0, "pushed_days": 999}
    if d:
        meta["stars"] = d.get("stargazers_count", 0)
        try:
            p = datetime.fromisoformat(d["pushed_at"].replace("Z", "+00:00"))
            meta["pushed_days"] = max((datetime.now(timezone.utc) - p).days, 0)
        except Exception:
            pass
    _repo_cache[repo] = meta
    time.sleep(SLEEP)
    return meta

def issue_comments(repo, number):
    d = gh_json([f"repos/{repo}/issues/{number}/comments"])
    time.sleep(SLEEP)
    if not d:
        return []
    out = []
    for c in d:
        if isinstance(c, dict):
            out.append({"login": c.get("user", {}).get("login"), "body": c.get("body", "")})
    return out

def comment_has_pr_link(body):
    b = (body or "").lower()
    return "/pull/" in b or "/pulls/" in b

def search(q, per=30):
    p = urllib.parse.quote(q)
    r = gh_raw([f"search/issues?q={p}&per_page={per}"])
    time.sleep(SLEEP)
    if r.returncode != 0:
        return []
    try:
        return json.loads(r.stdout).get("items", [])
    except Exception:
        return []

def score_no_comments(it):
    repo = it["repository_url"].split("repos/")[1]
    meta = repo_meta(repo)
    st = meta["stars"]; pd = meta["pushed_days"]
    body = it.get("body") or ""
    author = it.get("user", {}).get("login")
    labels = [l.get("name", "").lower() for l in it.get("labels", [])]
    is_docs = "documentation" in labels or "docs" in labels
    bd = {}
    bd["repo_health"] = 15 if st >= 300 else (10 if st >= 100 else (5 if st >= 30 else 0))
    bd["recency"] = 10 if pd <= 7 else (8 if pd <= 14 else (6 if pd <= 30 else 4))
    bd["license_ok"] = 10
    bd["assignable"] = 10
    bd["unassigned_now"] = 5 if not it.get("assignee") else 0
    bd["docs_clarity"] = 10 if len(body) > 120 else (6 if body else 4)
    bd["competence"] = 10 if len(body.split()) >= 40 else 7
    bd["risk"] = 9 if is_docs else 7
    bd["authenticity"] = 5 if author and author != "theluckystrike" else 0
    bd["issue_scope"] = 10
    return sum(bd.values()), bd, repo, is_docs

def main():
    axes = {
        "AXIS_A_chatter": [
            'label:"good first issue" OR label:"help wanted" state:open no:assignee comments:1..2 pushed:>2026-08-15 stars:>300',
            'label:"bug" state:open no:assignee comments:1..2 language:python pushed:>2026-08-15 stars:>300',
        ],
        "AXIS_B_docs": [
            'label:"documentation" state:open no:assignee comments:0..2 pushed:>2026-08-25 stars:>300',
            'label:"docs" state:open no:assignee comments:0..2 pushed:>2026-08-25 stars:>300',
        ],
    }
    seen = set()
    results = []
    for axis, queries in axes.items():
        for q in queries:
            items = search(q)
            for it in items:
                repo = it["repository_url"].split("repos/")[1]
                n = it["number"]
                key = (repo, n)
                if key in seen:
                    continue
                seen.add(key)
                base, bd, repo, is_docs = score_no_comments(it)
                if base >= 87:
                    comments = issue_comments(repo, n)
                    has_pr = any(comment_has_pr_link(c.get("body")) for c in comments)
                    n_comm = len(comments)
                    if has_pr:
                        bd["issue_valid"] = 0
                        rej = "comment_links_pr"
                    else:
                        bd["issue_valid"] = 10 if n_comm == 0 else (8 if n_comm <= 2 else 0)
                        rej = None
                    total = min(sum(bd.values()), 100)
                    results.append({
                        "axis": axis, "repo": repo, "number": n,
                        "title": it.get("title", "")[:90],
                        "comments": n_comm, "score": total,
                        "rejected": rej, "breakdown": bd,
                    })
                    print(json.dumps(results[-1]), flush=True)
    print("TOTAL_CANDIDATES", len(results), flush=True)

if __name__ == "__main__":
    main()