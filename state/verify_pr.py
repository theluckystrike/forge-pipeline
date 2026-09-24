import json, subprocess

def gh(endpoint):
    out = subprocess.run(["gh","api",endpoint,"-H","Accept: application/vnd.github+json"],capture_output=True,text=True,timeout=60)
    return json.loads(out.stdout) if out.returncode==0 else {"error":out.stderr.strip()[:200]}

pr = gh("repos/reservoirpy/reservoirpy/pulls/249")
print("title:", pr.get("title"))
print("state:", pr.get("state"))
print("head:", pr.get("head",{}).get("label"))
print("base:", pr.get("base",{}).get("ref"))
print("mergeable:", pr.get("mergeable"))
print("mergeable_state:", pr.get("mergeable_state"))
print("body head:", (pr.get("body") or "")[:120])

files = gh("repos/reservoirpy/reservoirpy/pulls/249/files")
print("--- files ---")
for f in files:
    print(" ", f.get("filename"), f.get("status"), f"+{f.get('additions')}/-{f.get('deletions')}")
