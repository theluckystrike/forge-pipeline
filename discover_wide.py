#!/usr/bin/env python3
"""Widened L1 discovery — one-off, prints top raw candidates."""
import json, subprocess, time, urllib.parse

def gh(path, params):
    qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    out = subprocess.run(["gh", "api", f"{path}?{qs}"], capture_output=True, text=True)
    return json.loads(out.stdout) if out.returncode == 0 else {"error": out.stderr[:200]}

queries = [
    'label:documentation state:open comments:0 language:python stars:>800 pushed:>2026-09-12 no:assignee',
    'label:"good first issue" state:open comments:0 language:typescript stars:>1000 pushed:>2026-09-12 no:assignee',
    'label:docs state:open comments:0 stars:>500 pushed:>2026-09-10 no:assignee',
    'label:"help wanted" state:open comments:0 language:rust stars:>400 pushed:>2026-09-12 no:assignee',
]
res = []
for q in queries:
    d = gh("search/issues", {"q": q, "per_page": 15, "sort": "created", "order": "desc"})
    for it in d.get("items", []):
        if "pull_request" in it:
            continue
        res.append({
            "repo": it["repository_url"].replace("https://api.github.com/repos/", ""),
            "num": it["number"],
            "title": it["title"][:90],
            "labels": [l["name"] for l in it["labels"]],
            "comments": it["comments"],
            "author": it["user"]["login"],
            "url": it["html_url"],
        })
    time.sleep(10)

print(json.dumps(res, indent=1))
