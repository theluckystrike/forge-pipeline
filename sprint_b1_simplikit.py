#!/usr/bin/env python3
"""ANVIL Sprint B1: translate 15 simplikit API md pages -> zh-Hans, layout per ko/."""
import os, re, json, subprocess, sys
sys.path.insert(0, "/Users/mike/oss-pipeline")

SRC = "/tmp/simplikit/packages/react-simplikit/src"
PAGES = []
for cat in ("utils", "components"):
    base = f"{SRC}/{cat}"
    for name in sorted(os.listdir(base)):
        en = f"{base}/{name}/{name}.md"
        if os.path.exists(en) and not os.path.exists(f"{base}/{name}/zh-Hans/{name}.md"):
            PAGES.append(f"{base}/{name}")

def llm(system, user):
    body = json.dumps({"model": os.environ.get("ANVIL_LLM_MODEL", "z-ai/glm-5.3-flash"),
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                       "temperature": 0.2})
    out = subprocess.run(["curl", "-s", "-m", "120", os.environ.get("ANVIL_LLM_BASE", "http://127.0.0.1:8788/v1") + "/chat/completions",
                          "-H", f"Authorization: Bearer {os.environ['NOUS_API_KEY']}",
                          "-H", "Content-Type: application/json", "-d", body], capture_output=True, text=True).stdout
    try:
        return json.loads(out)["choices"][0]["message"]["content"]
    except Exception:
        return None

SYS = """You are a professional KO->zh-Hans (Simplified Chinese) technical docs translator for React libraries.
Rules (from agent-translation-reviewer):
- Keep ALL markdown structure, code blocks, frontmatter, <Interface .../> JSX tags EXACTLY as-is.
- Inside <Interface> tags translate ONLY the description="..." value; keep name/type/required untouched.
- Do not translate identifiers (function/component/prop names).
- Full-width punctuation for Chinese prose ，。：；、（）？！
- Half-width space between Chinese and adjacent Latin/digit/inline-code.
- Output ONLY the translated markdown, no commentary."""

done, fail = 0, []
for page_dir in PAGES:
    name = os.path.basename(page_dir)
    en_p, ko_p = f"{page_dir}/{name}.md", f"{page_dir}/ko/{name}.md"
    src = open(ko_p if os.path.exists(ko_p) else en_p).read()
    out = llm(SYS, f"Translate this markdown page to Simplified Chinese:\n\n{src}")
    if not out or len(out) < len(src) * 0.4:
        fail.append(name); continue
    os.makedirs(f"{page_dir}/zh-Hans", exist_ok=True)
    open(f"{page_dir}/zh-Hans/{name}.md", "w").write(out.strip() + "\n")
    done += 1
    print(f"OK {name}")

print(f"DONE {done}/15, FAILED: {fail}")
