import json, subprocess

body = """Adds a tutorial notebook explaining the `reset` method on ReservoirPy nodes and why it matters when you run a trained ESN on new data.

The notebook trains an ESN on the Mackey-Glass series, then predicts the next 500 steps twice, once with the training state intact and once after a `reset()`. The two runs show the cold-start transient that a reset introduces and the tiny error that carrying the training state forward produces. A plot zooms into the first 60 timesteps to make the difference visible.

Closes #218"""

payload = {
    "title": "docs add reset parameter tutorial",
    "head": "theluckystrike:ws/reset-tutorial-0921",
    "base": "master",
    "body": body,
}
p = subprocess.run(["gh","api","--method","POST",
    "repos/reservoirpy/reservoirpy/pulls","--input","-"],
    input=json.dumps(payload), capture_output=True, text=True, timeout=60)
if p.returncode != 0:
    print("PR error:", p.stderr.strip()[:400])
else:
    r = json.loads(p.stdout)
    print("PR created:", r["html_url"])
    print("number:", r["number"])
    print("state:", r["state"])
    print("mergeable_state:", r.get("mergeable_state"))
