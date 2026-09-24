import json, base64, subprocess, hashlib

def read_back(path):
    out = subprocess.run(["gh","api",
        f"repos/theluckystrike/reservoirpy/contents/{path}?ref=ws/reset-tutorial-0921",
        "-H","Accept: application/vnd.github+json"], capture_output=True, text=True, timeout=60)
    d = json.loads(out.stdout)
    return base64.b64decode(d["content"])

# verify notebook
nb_back = read_back("docs/source/user_guide/reset.ipynb")
nb_local = open("/tmp/reset_tutorial.ipynb","rb").read()
print("notebook byte-identical:", nb_back == nb_local, f"({len(nb_back)} bytes)")

# verify index.rst has reset entry
idx_back = read_back("docs/source/user_guide/index.rst").decode()
print("index has reset entry:", "    reset" in idx_back)
print("index toctree tail:")
for line in idx_back.split("\n"):
    if "reset" in line or "jax_backend" in line:
        print("  ", repr(line))
