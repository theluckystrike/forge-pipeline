import json, base64, subprocess

# get current index.rst from fork branch
out = subprocess.run(["gh","api",
    "repos/theluckystrike/reservoirpy/contents/docs/source/user_guide/index.rst?ref=ws/reset-tutorial-0921",
    "-H","Accept: application/vnd.github+json"], capture_output=True, text=True, timeout=60)
d = json.loads(out.stdout)
sha = d["sha"]
content = base64.b64decode(d["content"]).decode()
print("current sha:", sha)
print("--- current toctree ---")
for line in content.split("\n"):
    if "quickstart" in line or "advanced_demo" in line or "jax_backend" in line or "toctree" in line or "maxdepth" in line:
        print(" ", repr(line))
