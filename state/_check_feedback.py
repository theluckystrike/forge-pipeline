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
    print(f"===== {repo}#{pr} =====")
    # latest issue comments (review comments appear here too)
    r = subprocess.run(['gh','api',f'repos/{repo}/issues/{pr}/comments','--jq','.[] | "[" + .user.login + " @ " + .created_at + "] " + (.body|gsub("\\n";" "))'], capture_output=True, text=True, timeout=40)
    out = r.stdout.strip()
    print("ISSUE COMMENTS (last 3):")
    print('\n'.join(out.split('\n')[-3:]) if out else '  (none)')
    time.sleep(1.0)