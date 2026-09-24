#!/usr/bin/env python3
"""RO-7: Formbricks zh-CN 3->4402. Checkpointed, resumable. Same proven pattern as ro5_cal_th.py."""
import subprocess, json, urllib.request, os, time, re

STATE = "/Users/mike/oss-pipeline/state"
CKPT = f"{STATE}/ro7_formbricks_zh.json"

def rawj(repo, path):
    r = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                        f"repos/{repo}/contents/{path}"], capture_output=True, text=True)
    return r.stdout

def flat(d, p=""):
    o = {}
    for k, v in d.items():
        kk = f"{p}.{k}" if p else k
        if isinstance(v, dict): o.update(flat(v, kk))
        else: o[kk] = v
    return o

def unflat(f):
    o = {}
    for k, v in f.items():
        parts = k.split(".")
        cur = o
        for p in parts[:-1]:
            if not isinstance(cur.get(p), dict): cur[p] = {}
            cur = cur[p]
        cur[parts[-1]] = v
    return o

def llm(batch):
    src = json.dumps(batch, ensure_ascii=False)
    prompt = ("Translate UI strings to Simplified Chinese (zh-CN) for a survey/data-collection SaaS. "
              "Keep {placeholders}, {x}, <tags>, URLs and product names unchanged. "
              "Return ONLY a JSON object mapping each source string to its translation.\n\n" + src)
    body = json.dumps({"model": "z-ai/glm-5.3-flash", "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.2, "max_tokens": 8000}).encode()
    req = urllib.request.Request("http://127.0.0.1:8788/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ.get("NOUS_API_KEY", "")})
    resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
    m = re.search(r"\{.*\}", resp["choices"][0]["message"]["content"], re.S)
    return json.loads(m.group(0))

en = json.loads(rawj("formbricks/formbricks", "apps/web/locales/en-US.json"))
flat_en = flat(en)
todo = [k for k in flat_en if k not in ("app.label", "common.label", "product.label")]
try: tr = json.load(open(CKPT))
except Exception: tr = {}
todo = [k for k in todo if k not in tr]
print("total en keys:", len(flat_en), "remaining:", len(todo), flush=True)

PH = re.compile(r"\{[^}]+\}|<[^>]+>|https?://\S+")
fails = 0
for i in range(0, len(todo), 200):
    chunk = todo[i:i+200]
    batch = {k: flat_en[k] for k in chunk}
    try:
        tr.update(llm(batch)); fails = 0
    except Exception as e:
        print("batch fail:", str(e)[:100]); fails += 1
        if fails > 6: print("too many consecutive failures, stopping for resume"); break
        time.sleep(5); continue
    # placeholder sanity
    bad = [k for k in chunk if sorted(PH.findall(flat_en[k])) != sorted(PH.findall(tr.get(k, "")))]
    for k in bad: tr.pop(k, None)
    json.dump(tr, open(CKPT, "w"), ensure_ascii=False)
    print(f"ckpt {i+len(chunk)}", flush=True)

# fill leftover keys (incl the 3 label keys) with en fallback if missing
json.dump(tr, open(CKPT, "w"), ensure_ascii=False)
full = {k: tr.get(k, flat_en[k]) for k in flat_en}
merged = unflat(full)
json.dump(merged, open("/tmp/formbricks_zh-CN.json", "w"), ensure_ascii=False, indent=2)
print(f"RO5_READY file=/tmp/formbricks_zh-CN.json keys={sum(1 for k in flat_en if k in tr)} / {len(flat_en)}", flush=True)
