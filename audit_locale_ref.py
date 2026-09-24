import json, subprocess, re, sys, os, base64, collections
from concurrent.futures import ThreadPoolExecutor
OUT="results.jsonl"
done=set()
if os.path.exists(OUT):
    for l in open(OUT): 
        try: done.add(json.loads(l)["repo"])
        except: pass

def gh(path, raw=False):
    r=subprocess.run(["gh","api",path],capture_output=True,text=True,timeout=120)
    if r.returncode!=0: return None
    return r.stdout if raw else json.loads(r.stdout)

LOCALE_DIR=re.compile(r'(^|/)(locales?|i18n|lang|langs|languages|translations?|messages|l10n|intl|locale)(/|$)',re.I)
LANG_FILE=re.compile(r'(^|/)([a-z]{2,3})([-_][A-Za-z]{2,4})?\.(json|po|yml|yaml|ts|js|arb|properties|xlf|xliff|resx|ftl|toml|php|edn)$')
def flatten_count(obj):
    if isinstance(obj,dict):
        return sum(flatten_count(v) for v in obj.values()) if obj else 0
    if isinstance(obj,list): return sum(flatten_count(v) for v in obj) if obj else 0
    return 1
def count_po(txt):
    return len(re.findall(r'^msgid\s+"',txt,re.M))-1
def count_yaml(txt):
    return len([l for l in txt.splitlines() if re.match(r'^\s*[^#\s][^:]*:\s*\S',l)])
def count_ts(txt):
    return len(re.findall(r'^\s*["\']?[\w.\-]+["\']?\s*:\s*["\'`]',txt,re.M))
def raw(repo,branch,path):
    r=subprocess.run(["curl","-sL","--max-time","60",f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"],capture_output=True,text=True)
    return r.stdout
def count_file(repo,branch,path):
    t=raw(repo,branch,path)
    if not t or len(t)<2: return None
    ext=path.rsplit('.',1)[-1]
    try:
        if ext=='json':
            return flatten_count(json.loads(t))
        if ext=='po': return count_po(t)
        if ext in('yml','yaml'): return count_yaml(t)
        if ext in('ts','js'): return count_ts(t)
        if ext=='properties': return len([l for l in t.splitlines() if '=' in l and not l.startswith('#')])
        if ext=='arb': return len([k for k in json.loads(t) if not k.startswith('@')])
        if ext=='ftl': return len(re.findall(r'^[a-zA-Z][\w-]*\s*=',t,re.M))
        if ext=='xlf' or ext=='xliff': return t.count('<trans-unit')
        if ext=='resx': return t.count('<data ')
        if ext=='php': return t.count('=>')
        if ext=='toml': return len([l for l in t.splitlines() if '=' in l])
    except Exception as e:
        return None
    return None

def measure(repo):
    o={"repo":repo}
    m=gh(f"repos/{repo}")
    if not m: o["err"]="nometa"; return o
    o.update(stars=m["stargazers_count"],owner_type=m["owner"]["type"],homepage=m.get("homepage"),branch=m["default_branch"],archived=m["archived"],pushed=m["pushed_at"][:10])
    if m["owner"]["type"]=="Organization":
        org=gh(f"orgs/{m['owner']['login']}")
        if org: o["org_blog"]=org.get("blog"); o["org_verified"]=org.get("is_verified")
    tree=gh(f"repos/{repo}/git/trees/{o['branch']}?recursive=1")
    if not tree: o["err"]="notree"; return o
    paths=[t["path"] for t in tree["tree"] if t["type"]=="blob"]
    o["truncated"]=tree.get("truncated",False)
    o["n_files"]=len(paths)
    low=[p.lower() for p in paths]
    o["funding"]=any(p.endswith("funding.yml") for p in low)
    o["crowdin"]=any(re.search(r'(^|/)crowdin\.ya?ml$',p) for p in low)
    o["weblate"]=any('.weblate' in p for p in low)
    o["transifex"]=any(p.endswith('.tx/config') for p in low)
    o["tolgee"]=any('tolgee' in p for p in low)
    o["lingui"]=any(p.endswith('lingui.config.ts') or p.endswith('lingui.config.js') or p.endswith('.linguirc') for p in low)
    # readme scan
    rd=gh(f"repos/{repo}/readme")
    rtxt=""
    if rd and rd.get("content"):
        try: rtxt=base64.b64decode(rd["content"]).decode("utf8","ignore").lower()
        except: pass
    o["readme_tms"]=[k for k in ["crowdin","weblate","transifex","tolgee","lokalise","phrase","localazy","poeditor","translate.","hosted.weblate"] if k in rtxt]
    # locale groups: dir -> files
    groups=collections.defaultdict(list)
    for p in paths:
        if 'node_modules' in p or '/test' in p.lower() or 'fixture' in p.lower() or 'e2e' in p.lower(): continue
        mm=LANG_FILE.search(p)
        d=p.rsplit('/',1)[0] if '/' in p else ''
        if mm and LOCALE_DIR.search('/'+d+'/'):
            groups[d].append(p)
    # also dirs like locales/<lang>/messages.json / translation.json
    for p in paths:
        if 'node_modules' in p: continue
        mm=re.search(r'(^|/)(locales?|i18n|lang|translations?|messages|l10n|intl)/([a-z]{2,3}([-_][A-Za-z]{2,4})?)/([\w\-]+\.(json|po|yml|yaml|ts|js|properties))$',p)
        if mm:
            groups[mm.group(0).rsplit('/',1)[0].rsplit('/',1)[0]+"::"+mm.group(5)].append(p)
    # pick largest group that contains english
    best=None
    for d,fs in groups.items():
        langs={}
        for f in fs:
            fn=f.rsplit('/',1)[-1]
            if '::' in d:
                lang=f.rsplit('/',2)[-2]
            else:
                lang=re.sub(r'\.[^.]+$','',fn)
            langs[lang]=f
        if len(langs)<3: continue
        en=[l for l in langs if l.lower() in ('en','en-us','en_us','en-gb','en_gb','english')]
        if not en: continue
        if best is None or len(langs)>len(best[1]): best=(d,langs,langs[en[0]])
    if not best:
        o["locale_dir"]=None; o["n_locales"]=0
        o["candidate_dirs"]=sorted(groups.keys(), key=lambda k:-len(groups[k]))[:5]
        return o
    d,langs,enf=best
    o["locale_dir"]=d; o["n_locales"]=len(langs); o["en_file"]=enf
    enc=count_file(repo,o["branch"],enf)
    o["en_keys"]=enc
    counts={}
    if enc:
        others=[l for l in langs if langs[l]!=enf]
        # sample up to 12 locales to find weakest
        import random; random.seed(1)
        sample=others if len(others)<=14 else random.sample(others,14)
        for l in sample:
            c=count_file(repo,o["branch"],langs[l])
            if c is not None: counts[l]=c
    o["locale_counts"]=counts
    if counts and enc:
        w=sorted(counts.items(), key=lambda kv:kv[1])[:3]
        o["weakest3"]=[(l,c,round(100*(1-c/enc),1)) for l,c in w]
        o["median_gap_pct"]=round(100*(1-sorted(counts.values())[len(counts)//2]/enc),1)
    return o

repos=[l.strip() for l in open("repos.txt") if l.strip() and l.strip() not in done]
def run(r):
    try: o=measure(r)
    except Exception as e: o={"repo":r,"err":repr(e)}
    with open(OUT,"a") as f: f.write(json.dumps(o)+"\n")
    print(r, o.get("stars"), o.get("n_locales"), o.get("en_keys"), o.get("weakest3"), flush=True)
with ThreadPoolExecutor(4) as ex: list(ex.map(run,repos))
