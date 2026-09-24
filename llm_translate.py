#!/usr/bin/env python3
"""LLM translation helper: reads JSON {key: english} on argv[1], prints {key: french/xx} JSON.
Target language taken from ANVIL_LANG env (default fr). Uses OpenAI-compatible env key if present."""
import json, os, sys, urllib.request

lang = os.environ.get("ANVIL_LANG", "fr")
arg = sys.argv[1]
data = json.loads(open(arg).read()) if os.path.exists(arg) else json.loads(arg)
keys = list(data)
prompt = (
    f"Translate these UI strings to natural {lang}. Keep {{placeholders}} exactly as-is. "
    "Keep proper nouns/tech terms (JWT, OAuth, API, product names) unchanged. "
    'Respond with ONLY a JSON object mapping each key to the translation.\n'
    + json.dumps(data, ensure_ascii=False))

key = os.environ.get("OPENAI_API_KEY") or os.environ.get("HERMES_LLM_KEY") or os.environ.get("NOUS_API_KEY")
if not key:
    print(json.dumps(data)); sys.exit(0)  # passthrough fallback (English) — caller QA will catch

body = json.dumps({
    "model": os.environ.get("ANVIL_LLM_MODEL", "z-ai/glm-5.3-flash"),
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.2,
}).encode()
req = urllib.request.Request(os.environ.get("ANVIL_LLM_BASE", "http://127.0.0.1:8788/v1") + "/chat/completions", data=body,
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
try:
    with urllib.request.urlopen(req, timeout=300) as r:
        txt = json.load(r)["choices"][0]["message"]["content"]
    txt = txt[txt.index("{"):txt.rindex("}")+1] if "{" in txt and "}" in txt else ""
    out = json.loads(txt) if txt else {}
    if not out: raise ValueError("model returned no JSON")
    # guarantee all keys present
    for k in keys: out.setdefault(k, data[k])
    print(json.dumps(out, ensure_ascii=False))
except Exception as e:
    print(f"ERR {e}", file=sys.stderr); sys.exit(1)
