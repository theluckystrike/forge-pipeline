#!/usr/bin/env python3
"""RO-5: Cal.com th locale 0->full. Checkpointed, resumable."""
import subprocess, json, urllib.request, os, time, re, sys

def rawj(path):
    r = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                        f"repos/calcom/cal.diy/contents/{path}"], capture_output=True, text=True)
    return json.loads(r.stdout)

def flat(d, pre=""):
    out = {}
    for k, v in d.items():
        key = f"{pre}{k}"
        if isinstance(v, dict): out.update(flat(v, key + "."))
        else: out[key] = v
    return out

en = flat(rawj("packages/i18n/locales/en/common.json"))
keys = list(en)
print("total en keys:", len(keys), flush=True)

key = os.environ.get("NOUS_API_KEY", "")
H = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
URL = "http://127.0.0.1:8788/v1/chat/completions"
CKPT = "/Users/mike/oss-pipeline/state/ro5_cal_th.json"
out = json.load(open(CKPT)) if os.path.exists(CKPT) else {}
B = 50
fails = 0
for i in range(0, len(keys), B):
    ck = [k for k in keys[i:i+B] if k not in out]
    if not ck: continue
    payload = {"model": "z-ai/glm-5.3-flash", "messages": [
        {"role": "system", "content": "Translate UI strings from English to Thai (th) for a scheduling app. Preserve ALL {{placeholders}} exactly; keep product names and technical terms (API, URL, webhook) untranslated. Output STRICT JSON mapping keys to translations."},
        {"role": "user", "content": json.dumps({k: en[k] for k in ck}, ensure_ascii=False)}],
        "temperature": 0.2}
    try:
        r = urllib.request.Request(URL, data=json.dumps(payload).encode(), headers=H)
        resp = json.loads(urllib.request.urlopen(r, timeout=240).read())
        txt = resp["choices"][0]["message"]["content"]
        txt = txt[txt.find("{"):txt.rfind("}") + 1]
        out.update(json.loads(txt))
        fails = 0
    except Exception as e:
        fails += 1
        print("chunk", i, "ERR", e, flush=True)
        if fails > 10:
            print("too many consecutive failures, exiting (checkpoint kept)", flush=True)
            break
        time.sleep(5)
        continue
    if (i // B) % 10 == 9:
        json.dump(out, open(CKPT, "w"), ensure_ascii=False)
        print("ckpt", len(out), flush=True)
    time.sleep(0.5)

json.dump(out, open(CKPT, "w"), ensure_ascii=False)
missing = [k for k in keys if k not in out]
print("DONE", len(out), "/", len(keys), "missing:", len(missing), flush=True)

# QA: placeholder integrity
bad = [k for k, v in out.items() if set(re.findall(r"\{\{[^}]+\}\}", en[k])) != set(re.findall(r"\{\{[^}]+\}\}", v))]
print("placeholder violations:", len(bad), flush=True)
if not missing and not bad:
    open("/Users/mike/oss-pipeline/state/ro5_cal_th_DONE", "w").write("ok\n")
    print("RO5_READY", flush=True)
