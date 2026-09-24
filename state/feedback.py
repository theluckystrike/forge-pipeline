import subprocess, json, time
from datetime import datetime, timezone

TRACKED = [
    ("Comfy-Org/ComfyUI_frontend", "18234"),
    ("stellar/stellar-docs", "2865"),
    ("cloudnative-pg/plugin-barman-cloud", "1108"),
    ("Qiskit/documentation", "5676"),
    ("calyxir/calyx", "2724"),
    ("domWalters/mkdocs-to-pdf", "115"),
]

def gh_api(endpoint):
    out = subprocess.run(["gh","api",endpoint], capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return None, out.stderr.strip()[:250]
    return json.loads(out.stdout), None

CUTOFF = datetime(2026, 9, 21, 17, 6, tzinfo=timezone.utc)  # last full sprint
for repo, pr in TRACKED:
    print(f"\n===== {repo}#{pr} =====")
    # issue comments (top-level) since cutoff, not by us
    data, err = gh_api(f"repos/{repo}/issues/{pr}/comments?per_page=100")
    if err:
        print("  comments err:", err); time.sleep(0.5); continue
    for c in data:
        ct = c.get("created_at","")
        login = c.get("user",{}).get("login","")
        try:
            dt = datetime.fromisoformat(ct.replace("Z","+00:00"))
        except Exception:
            dt = None
        if dt and dt >= CUTOFF and login.lower() != "theluckystrike":
            print(f"  NEW comment by {login} @ {ct}: {(c.get('body') or '')[:400]!r}")
    # reviews
    rv, err = gh_api(f"repos/{repo}/pulls/{pr}/reviews?per_page=100")
    if err:
        print("  reviews err:", err); time.sleep(0.5); continue
    for r in rv:
        rt = r.get("submitted_at","")
        login = r.get("user",{}).get("login","")
        try:
            dt = datetime.fromisoformat(rt.replace("Z","+00:00")) if rt else None
        except Exception:
            dt = None
        if dt and dt >= CUTOFF and login.lower() != "theluckystrike":
            state = r.get("state")
            body = (r.get("body") or "")[:300]
            print(f"  NEW review by {login} @ {rt} state={state}: {body!r}")
    time.sleep(0.5)
