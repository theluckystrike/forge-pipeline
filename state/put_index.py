import json, base64, subprocess

# fetch current
out = subprocess.run(["gh","api",
    "repos/theluckystrike/reservoirpy/contents/docs/source/user_guide/index.rst?ref=ws/reset-tutorial-0921",
    "-H","Accept: application/vnd.github+json"], capture_output=True, text=True, timeout=60)
d = json.loads(out.stdout)
sha = d["sha"]
content = base64.b64decode(d["content"]).decode()

# add reset to toctree after jax_backend
old = "    jax_backend"
new = "    jax_backend\n    reset"
assert old in content, "jax_backend not found in toctree"
content2 = content.replace(old, new, 1)
print("added reset entry, diff lines:", content.count("\n"), "->", content2.count("\n"))

# PUT
payload = {
    "message": "docs register reset tutorial in user guide",
    "content": base64.b64encode(content2.encode()).decode(),
    "branch": "ws/reset-tutorial-0921",
    "sha": sha,
}
p = subprocess.run(["gh","api","--method","PUT",
    "repos/theluckystrike/reservoirpy/contents/docs/source/user_guide/index.rst",
    "--input","-"], input=json.dumps(payload), capture_output=True, text=True, timeout=60)
if p.returncode != 0:
    print("PUT error:", p.stderr.strip()[:300])
else:
    r = json.loads(p.stdout)
    print("index.rst PUT OK, new sha:", r["content"]["sha"][:10])
