#!/usr/bin/env python3
"""Discovery round 2 — big repos only (>=300 stars), doc/i18n issues."""
import json, subprocess, time, urllib.parse

def gh(path, params):
    qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    out = subprocess.run(["gh", "api", f"{path}?{qs}"], capture_output=True, text=True)
    return json.loads(out.stdout) if out.returncode == 0 else {"error": out.stderr[:200]}

queries = [
    'label:documentation state:open comments:0 stars:>300 no:assignee pushed:>2026-09-05',
    'label:good-first-issue state:open comments:0 stars:>300 no:assignee pushed:>2026-09-05',
    'state:open comments:0 stars:>500 "documentation" in:title no:assignee pushed:>2026-09-01',
]
seen = {}
for q in queries:
    d = gh("search/issues", {"q": q, "per_page": 20, "sort": "created", "order": "desc"})
    for it in d.get("items", []):
        if "pull_request" in it or it["number"] in seen:
            continue
        seen[it["number"]] = {
            "repo": it["repository_url"].replace("https://api.github.com/repos/", ""),
            "num": it["number"],
            "title": it["title"][:90],
            "comments": it["comments"],
            "author": it["user"]["login"],
        }
    time.sleep(12)
print(json.dumps(list(seen.values()), indent=1))
