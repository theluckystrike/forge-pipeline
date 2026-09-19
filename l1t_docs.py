#!/usr/bin/env python3
"""L1t: docs/test-coverage target discovery — lower-risk contribution lane."""
import json, subprocess
from datetime import datetime

def gh(endpoint, params=None):
    if params:
        from urllib.parse import quote
        qs = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        endpoint = endpoint + ("&" if "?" in endpoint else "?") + qs
    out = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip()[:300])
    return json.loads(out.stdout)

# Docs-labeled PRs that are stale (linked:none = no PR yet attached, they are the PRs themselves)
# Instead: search for open docs-labeled ISSUES in healthy repos — lower competition than code.
QUERIES = [
    'label:documentation state:open type:issue language:python stars:>1000 pushed:>2026-08-20 no:assignee comments:0',
    'label:"good first issue" state:open type:issue language:python stars:>2000 no:assignee comments:0 label:documentation',
]

out = []
for q in QUERIES:
    try:
        r = gh("search/issues", {"q": q, "per_page": 20, "sort": "updated", "order": "desc"})
        for it in r.get("items", []):
            repo = it["repository_url"].replace("https://api.github.com/repos/", "")
            out.append({"repo": repo, "number": it["number"], "title": it["title"],
                        "url": it["html_url"], "labels": [l["name"] for l in it.get("labels", [])],
                        "comments": it.get("comments", 0), "query": q})
    except Exception as e:
        out.append({"error": str(e), "query": q})

ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
print(json.dumps({"ts": ts, "count": len([o for o in out if 'repo' in o]), "items": out[:25]}, indent=1))
