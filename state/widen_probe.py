"""W23+ widened-discovery prototype.
Adds two axes the strict L1 misses:
  A) accept unassigned issues with 1-2 claim-chatter comments (not just 0)
  B) a docs-only search axis (DOCS_QUERIES exists in pipeline but is never run)
Goal: surface candidates that can reach exactly 100 under the hard gate.
"""
import subprocess, json, time, sys

def gh(endpoint, params=None, method="GET"):
    cmd = ["gh", "api", endpoint]
    if params:
        from urllib.parse import quote
        qs = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
        endpoint = endpoint + ("&" if "?" in endpoint else "?") + qs
        cmd = ["gh", "api", endpoint]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"gh api {endpoint}: {out.stderr.strip()[:300]}")
    return json.loads(out.stdout)

def search(q, n=15):
    for attempt in range(4):
        try:
            return gh("search/issues", {"q": q, "per_page": n, "sort": "updated", "order": "desc"})
        except RuntimeError as e:
            if "rate limit" in str(e).lower() and attempt < 3:
                wait = 20*(attempt+1)
                print(f"  [backoff] {wait}s", flush=True); time.sleep(wait)
            else:
                raise

# AXIS A: allow 1-2 comments (claim-chatter) on a good-first/help-wanted, no assignee
# AXIS B: docs-only, no assignee, freshly pushed
WIDENED_QUERIES = {
    "A1_goodfirst_1to2comments": 'label:"good first issue" state:open language:python comments:1..2 stars:>500 pushed:>2026-09-05 no:assignee',
    "A2_helpwanted_1to2comments": 'label:"help wanted" state:open comments:1..2 stars:>1000 pushed:>2026-09-07 no:assignee',
    "B1_docsaxis":                  'label:"documentation" state:open stars:>2000 pushed:>2026-09-08 no:assignee comments:0..2',
    "B2_docsaxis_gfi":              'label:"documentation" label:"good first issue" state:open stars:>500 pushed:>2026-09-08 no:assignee comments:0..2',
    "B3_docs_pr":                   'is:pr state:open label:"documentation" stars:>3000 linked:none updated:>2026-09-01',
}

out = {}
for name, q in WIDENED_QUERIES.items():
    try:
        r = search(q)
        items = []
        for it in r.get("items", []):
            items.append({
                "repo": it.get("repository_url","").replace("https://api.github.com/repos/",""),
                "number": it["number"],
                "title": it["title"][:90],
                "comments": it.get("comments",0),
                "labels": [l["name"] for l in it.get("labels",[])],
                "state": it.get("state"),
                "url": it.get("html_url"),
                "query": name,
            })
        out[name] = items
        print(f"\n### {name}  (n={len(items)})")
        for i in items:
            print(f"   {i['repo']}#{i['number']} c={i['comments']} labs={i['labels']} :: {i['title']}")
    except Exception as e:
        out[name] = {"error": str(e)[:200]}
        print(f"\n### {name} ERROR: {str(e)[:150]}")
    time.sleep(0.6)

json.dump({"ts": __import__("datetime").datetime.utcnow().isoformat(), "queries": out},
          open("/Users/mike/oss-pipeline/state/widen_probe.json","w"), indent=2)
print("\nSaved widen_probe.json")
