"""Compare audit_locale.py against the stored seed measurements.
pass2 (plan-evidence/a3/pass2.jsonl) = missing OR identical, no skip rule  -> compare with --ref mode
seed/locale_results.jsonl = key-count gap (1 - locale_keys/en_keys)          -> compare with count_pct
"""
import json, sys, os
sys.path.insert(0, os.path.expanduser("~/oss-pipeline"))
import audit_locale as A
P = os.path.expanduser("~/oss-pipeline")
pass2 = {json.loads(l)["repo"]: json.loads(l) for l in open(f"{P}/plan-evidence/a3/pass2.jsonl")}
seed = {json.loads(l)["repo"]: json.loads(l) for l in open(f"{P}/seed/locale_results.jsonl")}
repos = sys.argv[1:]
out = {}
for repo in repos:
    p2 = pass2[repo]; sd = seed.get(repo, {})
    hint = p2["en_file"].rsplit("/", 1)[0]
    ref = A.audit(repo, ref_mode=True, group_hint=hint)
    dflt = A.audit(repo, ref_mode=False, group_hint=hint)
    out[repo] = {"ref": {k: v for k, v in ref.items() if k != "gap_key_lists"}, "default": {k: v for k, v in dflt.items() if k != "gap_key_lists"}}
    print(f"\n== {repo}  stored en_file={p2['en_file']} en_keys={p2['en_keys']}  mine src={ref.get('src_files')} en_keys={ref.get('en_keys')}")
    print(f"{'locale':8} {'pass2 gap%':>10} {'mine --ref':>10} {'diff pp':>8} | {'default':>8} | {'seed cnt%':>9} {'mine cnt%':>9} {'diff':>6}")
    sc = {l: g for l, c, g in sd.get("weakest3") or []}
    for loc, stored in sorted(p2.get("big", {}).items()):
        m = ref["locales"].get(A.norm_lang(loc) or loc)
        d = dflt["locales"].get(A.norm_lang(loc) or loc)
        if not m:
            print(f"{loc:8} {stored:>10} {'n/a':>10}"); continue
        cnt_seed = sc.get(loc)
        print(f"{loc:8} {stored:>10} {m['gap_pct']:>10} {round(m['gap_pct']-stored,1):>8} | {d['gap_pct']:>8} | "
              f"{cnt_seed if cnt_seed is not None else '-':>9} {m['count_pct']:>9} {round(m['count_pct']-cnt_seed,1) if cnt_seed is not None else '-':>6}")
    for loc, c, g in sd.get("weakest3") or []:
        if loc in p2.get("big", {}):
            continue
        m = ref["locales"].get(A.norm_lang(loc) or loc)
        if m:
            print(f"{loc:8} {'-':>10} {m['gap_pct']:>10} {'-':>8} | {dflt['locales'][A.norm_lang(loc) or loc]['gap_pct']:>8} | {g:>9} {m['count_pct']:>9} {round(m['count_pct']-g,1):>6}")
json.dump(out, open(f"{P}/state/audit-validation/validate_locale_out.json", "w"), indent=1)
