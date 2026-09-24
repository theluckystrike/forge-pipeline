import subprocess, json, time
prs = [
    ('Comfy-Org/ComfyUI_frontend', '18234'),
    ('stellar/stellar-docs', '2865'),
    ('cloudnative-pg/plugin-barman-cloud', '1108'),
    ('Qiskit/documentation', '5676'),
    ('calyxir/calyx', '2724'),
    ('domWalters/mkdocs-to-pdf', '115'),
]
for repo, pr in prs:
    print(f"===== {repo}#{pr} REVIEWS =====")
    r = subprocess.run(['gh','api',f'repos/{repo}/pulls/{pr}/reviews','--jq','.[] | select(.user.login != "theluckystrike") | "[" + .user.login + " " + .state + " @ " + .submitted_at + "] " + (.body|gsub("\\n";" "))'], capture_output=True, text=True, timeout=40)
    out = r.stdout.strip()
    print('\n'.join(out.split('\n')[-4:]) if out else '  (no non-own reviews)')
    time.sleep(1.0)