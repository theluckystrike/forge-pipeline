import json, base64, subprocess, time

def gh_put(path, content_b64, message, branch, sha=None):
    payload = {"message": message, "content": content_b64, "branch": branch}
    if sha:
        payload["sha"] = sha
    p = subprocess.run(["gh","api","--method","PUT",
        f"repos/theluckystrike/reservoirpy/contents/{path}",
        "--input","-"], input=json.dumps(payload), capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        return {"error": p.stderr.strip()[:300]}
    return json.loads(p.stdout)

# 1) PUT the notebook
nb = open("/tmp/reset_tutorial.ipynb","rb").read()
nb_b64 = base64.b64encode(nb).decode()
r1 = gh_put("docs/source/user_guide/reset.ipynb", nb_b64,
    "docs add reset parameter tutorial", "ws/reset-tutorial-0921")
print("notebook PUT:", "OK" if "content" in r1 else r1.get("error","?"))
if "content" in r1:
    print("  sha:", r1["content"]["sha"][:10])
