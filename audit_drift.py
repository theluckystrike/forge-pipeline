#!/usr/bin/env python3
"""audit_drift.py: deterministic README/docs drift checks for one GitHub repo (no LLM judgment).

Checks (README.md plus top-level docs/*.md only):
  a  dead external links: HEAD then GET, 8 s timeout, max 60 unique links; only 404, 410 and DNS
     failure count, and each failure is re-checked once before it counts.
  b  relative links to files or dirs that are not in the git tree (one recursive tree call).
  c  version drift: versions pinned in README install snippets vs manifest version / latest release.
  d  count claims ("N tests", "N+ integrations", "N languages") vs counts taken from the tree,
     flagged when they differ by more than 10 percent.
  e  Node/Python minimum-version claims in README vs engines.node / requires-python.

Every finding keeps the exact line, the measured value and the command or URL that measured it.

Usage: python3 audit_drift.py owner/repo [--out findings.json]
Cost: 2 REST calls for meta+tree (shared with audit_locale when run from audit_report.py),
1 REST call for releases/latest (+1 for tags if there is no release); the rest is raw/curl.
"""
import json, os, re, subprocess, sys, time, posixpath, urllib.parse
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from audit_locale import gh, raw, raw_url, repo_meta_and_tree, SKIP_SEG

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
MAX_LINKS = 60
SKIP_HOST = re.compile(r'^(localhost|127\.|0\.0\.0\.0|10\.|192\.168\.|\[::1\]|.*\.local$|.*\.internal$|.*\.test$|.*\.invalid$|'
                       r'.*\.example$|example\.(com|org|net)$|.*\.example\.(com|org|net)$|your[-_.]|my[-_.]?(app|domain|site)|'
                       r'foo\.|bar\.|host$|server$|domain\.com$|yourdomain|mydomain)', re.I)

# ---------------------------------------------------------------- text helpers
def code_fence_mask(lines):
    """Return list of (in_fence, fence_lang) per line."""
    out = []; inside = False; lang = ""; fence = ""
    for l in lines:
        m = re.match(r'^\s*(```+|~~~+)\s*([\w+-]*)', l)
        if m and (not inside or m.group(1)[0] == fence[0]):
            if not inside:
                inside = True; fence = m.group(1); lang = m.group(2).lower(); out.append((True, lang)); continue
            else:
                inside = False; out.append((True, lang)); lang = ""; continue
        out.append((inside, lang))
    return out

LINK_PATTERNS = [
    re.compile(r'!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?([^()\s<>]+(?:\([^()\s]*\)[^()\s<>]*)*)>?(?:\s+["\'(][^)]*)?\)'),
    re.compile(r'^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s+["\'(].*)?$'),
    re.compile(r'\b(?:href|src)\s*=\s*["\']([^"\']+)["\']', re.I),
]
BARE_URL = re.compile(r'<?(https?://[^\s<>"\'`\])]+)')

def extract_links(text):
    """Yield (line_no, url, line, in_code) for every link-like target. Inline code spans and fenced
    blocks are examples, not links, so bare URLs inside them are reported with in_code=True."""
    lines = text.split('\n')
    mask = code_fence_mask(lines)
    seen = set()
    for i, l in enumerate(lines, 1):
        in_code = mask[i - 1][0]
        found = []
        prose = re.sub(r'(`+)(?:(?!\1).)+\1', ' ', l) if not in_code else ""
        rest = prose
        if not in_code:
            for pat in LINK_PATTERNS:
                for m in pat.finditer(prose):
                    t = m.group(1)
                    if t.startswith('[') or '](' in t or not re.search(r'[A-Za-z0-9]', t):
                        continue
                    found.append(t)
                rest = pat.sub(' ', rest)
        for m in BARE_URL.finditer(rest if not in_code else l):
            u = m.group(1).rstrip('.,;:!?*_')
            if u.count('(') < u.count(')'):
                u = u[:u.rfind(')')]
            found.append(u)
        for u in found:
            key = (i, u)
            if key in seen:
                continue
            seen.add(key)
            yield i, u, l, in_code

# ---------------------------------------------------------------- (a) dead links
def curl(url, method):
    args = ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "-L", "--max-time", "8", "-A", UA,
            "-H", "Accept: text/html,application/xhtml+xml,*/*;q=0.8"]
    if method == "HEAD":
        args.append("-I")
    args.append(url)
    r = subprocess.run(args, capture_output=True, text=True, timeout=20)
    return r.stdout.strip() or "000", r.returncode, r.stderr.strip()[:200]

def check_link(url):
    """HEAD, fall back to GET; returns dict with verdict dead/ok/unknown."""
    rec = {"url": url}
    code, rc, err = curl(url, "HEAD")
    rec.update(head_code=code, head_exit=rc)
    if code in ("404", "410") or rc != 0 or code in ("000", "400", "403", "405", "429", "500", "501", "502", "503"):
        code, rc, err = curl(url, "GET")
        rec.update(get_code=code, get_exit=rc, get_err=err)
    rec["final_code"] = code; rec["final_exit"] = rc
    rec["dead"] = code in ("404", "410") or rc == 6
    rec["reason"] = ("DNS resolution failed (curl exit 6)" if rc == 6 else f"HTTP {code}") if rec["dead"] else ""
    return rec

def dead_links(docs):
    """docs: list of (path, text). Returns (checked records, findings)."""
    cand = []; seen = set()
    for path, text in docs:
        for ln, u, line, in_code in extract_links(text):
            if not re.match(r'https?://', u) or in_code:
                continue
            host = urllib.parse.urlsplit(u).hostname or ""
            if not host or SKIP_HOST.search(host) or '{' in u or '<' in u or '$' in u or '*' in host or '..' in host \
                    or host.endswith('-') or re.search(r'(^|\.)(some|your|my)-', host) or 'path/to' in u:
                continue
            # GitHub pages that answer 404 to anonymous clients while working for signed-in readers
            if re.match(r'https?://github\.com/[^/]+/[^/]+/(stargazers|watchers|network|forks|graphs|pulse|assets)(/|$|\?)', u) \
                    or 'user-attachments' in u or 'private-user-images' in u \
                    or re.match(r'https?://(www\.)?(x|twitter)\.com/[^/]+/status/', u):
                continue
            base = u.split('#')[0]
            if base in seen:
                continue
            seen.add(base)
            cand.append({"file": path, "line_no": ln, "line": line, "url": base})
    cand = cand[:MAX_LINKS]
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda c: check_link(c["url"]), cand))
    recs = []
    for c, r in zip(cand, res):
        c.update(r); recs.append(c)
    # re-check every failure once (sequential, after a pause)
    fails = [r for r in recs if r["dead"]]
    if fails:
        time.sleep(3)
        for r in fails:
            code, rc, err = curl(r["url"], "GET")
            r["recheck_code"] = code; r["recheck_exit"] = rc
            r["dead"] = code in ("404", "410") or rc == 6
            if r["dead"]:
                r["reason"] = "DNS resolution failed (curl exit 6)" if rc == 6 else f"HTTP {code}"
    findings = []
    for r in recs:
        if r["dead"]:
            findings.append({"check": "a_dead_link", "file": r["file"], "line_no": r["line_no"], "line": r["line"],
                             "claimed": r["url"], "measured": r["reason"],
                             "measured_by": f"curl -sS -o /dev/null -w '%{{http_code}}' -L --max-time 8 -H 'Accept: text/html' '{r['url']}' (HEAD, GET, GET re-check)"})
    return recs, findings

# ---------------------------------------------------------------- (b) relative links
REPO_PAGES = {"issues", "pulls", "pull", "wiki", "discussions", "releases", "actions", "security", "projects",
              "graphs", "network", "compare", "commits", "tags", "blob", "tree", "raw", "stargazers", "fork", "milestones", "labels"}

SITE_GEN = re.compile(r'(^|/)(mkdocs\.ya?ml|docusaurus\.config\.[jt]s|book\.toml|hugo\.(toml|ya?ml)|astro\.config\.[mc]?[jt]s|'
                      r'\.vitepress/config\.[mc]?[jt]s|_config\.yml|conf\.py|docs\.json|mint\.json|antora\.yml|_sidebar\.md|docs/index\.html)$')

def relative_links(docs, repo, branch, paths, dirs, truncated):
    findings = []; checked = []
    if truncated:
        return checked, findings
    # docs/*.md rendered by a site generator resolve links against the site, not the git tree
    site_docs = any(SITE_GEN.search(p) and (p.startswith('docs/') or '/' not in p or p.startswith('website/')) for p in paths)
    for path, text in docs:
        base_dir = posixpath.dirname(path)
        is_doc = path.lower().startswith('docs/')
        if is_doc and site_docs:
            continue
        for ln, u, line, in_code in extract_links(text):
            if in_code or re.match(r'^[a-z][a-z0-9+.-]*:', u, re.I) or u.startswith(('#', '//', '{', '<', '$', '@')):
                continue
            target = urllib.parse.unquote(u.split('#')[0].split('?')[0]).strip()
            if not target or not re.search(r'[A-Za-z0-9]', target):
                continue
            if is_doc and target.startswith('/'):
                continue
            full = posixpath.normpath(target.lstrip('/') if target.startswith('/') else posixpath.join(base_dir, target))
            if full.startswith('..') or full == '.':
                continue
            first = full.split('/')[0]
            if first in REPO_PAGES and full not in paths and full not in dirs:
                continue
            ok = full in paths or full in dirs
            checked.append({"file": path, "line_no": ln, "link": u, "resolved": full, "exists": ok})
            if not ok:
                findings.append({"check": "b_missing_relative_target", "file": path, "line_no": ln, "line": line,
                                 "claimed": u, "measured": f"path '{full}' not in git tree of {branch}",
                                 "measured_by": f"gh api 'repos/{repo}/git/trees/{branch}?recursive=1' --jq '.tree[].path' | grep -Fx '{full}'"})
    return checked, findings

# ---------------------------------------------------------------- versions
def vtuple(v):
    m = re.match(r'v?(\d+)(?:\.(\d+))?(?:\.(\d+))?', str(v).strip())
    if not m:
        return None
    return tuple(int(x) if x is not None else None for x in m.groups())

def latest_release(repo):
    r = gh(f"repos/{repo}/releases/latest")
    if r and r.get("tag_name"):
        return {"tag": r["tag_name"], "source": f"gh api repos/{repo}/releases/latest --jq .tag_name", "published_at": r.get("published_at")}
    t = gh(f"repos/{repo}/tags?per_page=100")
    if t:
        best = None
        for x in t:
            m = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?$', x["name"])
            if m and not re.search(r'(alpha|beta|rc|canary|next|dev|pre)', x["name"], re.I):
                tup = tuple(int(g or 0) for g in m.groups())
                if best is None or tup > best[0]:
                    best = (tup, x["name"])
        if best:
            return {"tag": best[1], "source": f"gh api 'repos/{repo}/tags?per_page=100' --jq '.[].name' (max stable semver)"}
    return None

def pkg_norm(n):
    return re.sub(r'[-_.]+', '-', n.lower())

INSTALL = [
    ("npm", re.compile(r'\b(?:npm\s+(?:i|install|add)|yarn\s+(?:global\s+)?add|pnpm\s+(?:add|i|install)|bun\s+(?:add|i|install)|npx|deno\s+add)\b(.*)', re.I),
     re.compile(r'(?<![\w/])((?:@[\w.-]+/)?[\w.-]+)@[\^~]?v?(\d+(?:\.\d+){0,2})(?![\w.])')),
    ("pip", re.compile(r'\b(?:pip3?|uv\s+pip|python3?\s+-m\s+pip|pipx|uv)\s+(?:install|add)\b(.*)', re.I),
     re.compile(r'(?<![\w/])([A-Za-z][\w.\-]*)(?:\[[^\]]*\])?\s*==\s*v?(\d+(?:\.\d+){0,3})')),
    ("poetry", re.compile(r'\bpoetry\s+add\b(.*)', re.I), re.compile(r'([A-Za-z][\w.\-]*)(?:@|==)[\^~]?(\d+(?:\.\d+){0,2})')),
    ("cargo", re.compile(r'\bcargo\s+(?:add|install)\b(.*)', re.I), re.compile(r'([\w-]+)@[\^~=]?(\d+(?:\.\d+){0,2})')),
    ("go", re.compile(r'\bgo\s+(?:get|install)\b(.*)', re.I), re.compile(r'([\w.\-]+(?:/[\w.\-]+)+)@v(\d+\.\d+\.\d+)')),
    ("gem", re.compile(r'\bgem\s+(.*)'), re.compile(r'''^['"]([\w-]+)['"]\s*,\s*['"][~>=\s]*(\d+(?:\.\d+){0,2})''')),
    ("docker", re.compile(r'\b(?:docker\s+(?:run|pull|create)|podman\s+(?:run|pull)|image:|FROM)\b(.*)', re.I),
     re.compile(r'(?<![\w.:/-])((?:[\w.\-]+/)*[\w.\-]+):v?(\d+\.\d+(?:\.\d+)?)(?![\w.])')),
    ("gha", re.compile(r'\buses:\s*(.*)'), re.compile(r'([\w.\-]+/[\w.\-]+)@v(\d+(?:\.\d+){0,2})\b')),
    ("gradle", re.compile(r'(implementation|api|compile|testImplementation)\b(.*)'), re.compile(r'''['"]([\w.\-]+):([\w.\-]+):(\d+\.\d+(?:\.\d+)?)['"]''')),
]

def version_claims(readme, repo, manifests, release, raw_base):
    """manifests: dict of known package names -> (version, source description)."""
    org, name = repo.split('/')
    findings = []; claims = []
    lines = readme.split('\n')
    mask = code_fence_mask(lines)
    rel_t = vtuple(release["tag"].split('@')[-1].lstrip('v').split('/')[-1]) if release else None
    rel_ver = None
    if release:
        m = re.search(r'(\d+\.\d+(?:\.\d+)?)', release["tag"])
        rel_ver = m.group(1) if m else None
    for i, l in enumerate(lines, 1):
        for kind, trig, tok in INSTALL:
            tm = trig.search(l)
            if not tm:
                continue
            tail = tm.group(tm.lastindex) if tm.lastindex else l
            for m in tok.finditer(tail):
                if kind == "gradle":
                    pkg, ver = m.group(2), m.group(3)
                else:
                    pkg, ver = m.group(1), m.group(2)
                pn = pkg_norm(pkg.split('/')[-1] if kind in ("npm",) else pkg)
                cur = None; src = None
                if kind == "npm":
                    full = pkg.lower()
                    if full in manifests:
                        cur, src = manifests[full]
                    elif pn == pkg_norm(name) and ("npm:" + pn) in manifests:
                        cur, src = manifests["npm:" + pn]
                    elif pn == pkg_norm(name) and rel_ver:
                        cur, src = rel_ver, release["source"]
                elif kind in ("pip", "poetry"):
                    key = "py:" + pkg_norm(pkg)
                    if key in manifests:
                        cur, src = manifests[key]
                    elif pkg_norm(pkg) == pkg_norm(name) and rel_ver:
                        cur, src = rel_ver, release["source"]
                elif kind == "cargo":
                    key = "rs:" + pkg_norm(pkg)
                    if key in manifests:
                        cur, src = manifests[key]
                    elif pkg_norm(pkg) == pkg_norm(name) and rel_ver:
                        cur, src = rel_ver, release["source"]
                elif kind == "go":
                    if "go:module" in manifests and pkg.startswith(manifests["go:module"][0]) and rel_ver:
                        cur, src = rel_ver, release["source"]
                    elif pkg.lower().startswith(f"github.com/{repo.lower()}") and rel_ver:
                        cur, src = rel_ver, release["source"]
                elif kind == "docker":
                    last = pkg.split('/')[-1].lower()
                    if (last == name.lower() or (last == org.lower() and '/' in pkg)) and rel_ver:
                        cur, src = rel_ver, release["source"]
                elif kind == "gha":
                    if pkg.lower() == repo.lower() and rel_ver:
                        cur, src = rel_ver, release["source"]
                elif kind == "gem":
                    if pkg_norm(pkg) == pkg_norm(name) and rel_ver:
                        cur, src = rel_ver, release["source"]
                elif kind == "gradle":
                    if pkg_norm(pkg) == pkg_norm(name) and rel_ver:
                        cur, src = rel_ver, release["source"]
                if cur is None:
                    continue
                ct, mt = vtuple(ver), vtuple(cur)
                if not ct or not mt:
                    continue
                rec = {"kind": kind, "line_no": i, "line": l, "package": pkg, "claimed": ver, "current": cur, "current_source": src}
                claims.append(rec)
                # compare at the precision the README uses (major for gha tags like v3, else major.minor)
                prec = 1 if kind == "gha" or ct[1] is None else 2
                a = tuple(x or 0 for x in ct[:prec]); b = tuple(x or 0 for x in mt[:prec])
                if a < b:
                    findings.append({"check": "c_version_drift", "file": "README.md", "line_no": i, "line": l,
                                     "claimed": f"{pkg} {ver}", "measured": f"current {cur}", "measured_by": src})
    return claims, findings

def load_manifests(repo, ref, paths, readme):
    """Read root manifests (and package manifests whose name the README installs). Raw reads only."""
    out = {}; files = {}
    def get(p):
        if p in paths:
            t = raw(repo, ref, p)
            if t is not None:
                files[p] = t
            return t
        return None
    pj = get("package.json")
    engines_node = None
    if pj:
        try:
            j = json.loads(pj)
            if j.get("engines", {}).get("node"):
                engines_node = (j["engines"]["node"], f"curl -sL {raw_url(repo, ref, 'package.json')} | jq -r .engines.node")
            if j.get("name") and j.get("version") and j.get("version") not in ("0.0.0", "0.0.0-development") and not j.get("private"):
                out[j["name"].lower()] = (j["version"], f"curl -sL {raw_url(repo, ref, 'package.json')} | jq -r .version")
                out["npm:" + pkg_norm(j["name"].split('/')[-1])] = out[j["name"].lower()]
        except Exception:
            pass
    # package.json of npm packages the README installs, found by directory name (max 6 raw reads)
    wanted = set()
    for m in re.finditer(r'(?:npm\s+(?:i|install|add)|yarn\s+add|pnpm\s+add|bun\s+add)\s+[^\n]*', readme):
        for t in re.finditer(r'((?:@[\w.-]+/)?[\w.-]+)@\d', m.group(0)):
            wanted.add(t.group(1).lower())
    n = 0
    for w in sorted(wanted):
        last = w.split('/')[-1]
        for p in sorted(paths):
            if n >= 6:
                break
            if p.endswith(f"/{last}/package.json") and 'node_modules' not in p and p.count('/') <= 4:
                t = get(p); n += 1
                try:
                    j = json.loads(t or "{}")
                except Exception:
                    continue
                if j.get("name", "").lower() == w and j.get("version"):
                    out[w] = (j["version"], f"curl -sL {raw_url(repo, ref, p)} | jq -r .version")
                    engines_node = engines_node or ((j["engines"]["node"], f"curl -sL {raw_url(repo, ref, p)} | jq -r .engines.node") if j.get("engines", {}).get("node") else None)
    requires_python = None
    pp = get("pyproject.toml")
    if pp:
        m = re.search(r'^\s*name\s*=\s*"([^"]+)"', pp, re.M)
        v = re.search(r'^\s*version\s*=\s*"([^"]+)"', pp, re.M)
        if m and v:
            out["py:" + pkg_norm(m.group(1))] = (v.group(1), f"curl -sL {raw_url(repo, ref, 'pyproject.toml')} | grep -m1 '^version'")
        rp = re.search(r'^\s*requires-python\s*=\s*["\']([^"\']+)["\']', pp, re.M)
        if rp:
            requires_python = (rp.group(1), f"curl -sL {raw_url(repo, ref, 'pyproject.toml')} | grep requires-python")
        else:
            rp = re.search(r'^\s*python\s*=\s*["\']([^"\']+)["\']', pp, re.M)
            if rp:
                requires_python = (rp.group(1), f"curl -sL {raw_url(repo, ref, 'pyproject.toml')} | grep '^python ='")
    if not requires_python:
        for f in ("setup.cfg", "setup.py"):
            t = get(f)
            if t:
                rp = re.search(r'python_requires\s*=\s*["\']?([^"\'\n,]+)', t)
                if rp:
                    requires_python = (rp.group(1).strip(), f"curl -sL {raw_url(repo, ref, f)} | grep python_requires")
                    break
    ct = get("Cargo.toml")
    if ct:
        sec = re.search(r'^\[package\](.*?)(?=^\[|\Z)', ct, re.M | re.S)
        if sec:
            m = re.search(r'^\s*name\s*=\s*"([^"]+)"', sec.group(1), re.M)
            v = re.search(r'^\s*version\s*=\s*"([^"]+)"', sec.group(1), re.M)
            if m and v:
                out["rs:" + pkg_norm(m.group(1))] = (v.group(1), f"curl -sL {raw_url(repo, ref, 'Cargo.toml')} | grep -m1 '^version'")
    gm = get("go.mod")
    if gm:
        m = re.search(r'^module\s+(\S+)', gm, re.M)
        if m:
            out["go:module"] = (m.group(1), "go.mod")
    return out, files, engines_node, requires_python

# ---------------------------------------------------------------- (d) count claims
TEST_FILE = re.compile(r'(\.(test|spec)\.[cm]?[jt]sx?$|_test\.(go|py|rs|rb|exs?)$|(^|/)test_[^/]+\.py$|_spec\.rb$|Tests?\.(java|kt|cs|swift)$)')
NOUNS = ["integrations", "connectors", "plugins", "providers", "adapters", "templates", "icons", "themes", "extensions", "nodes"]

def count_claims(readme, paths, dirs, locale_n):
    findings = []; claims = []
    lines = readme.split('\n')
    test_files = [p for p in paths if TEST_FILE.search(p) and 'node_modules' not in p]
    # children per noun dir
    noun_dirs = {}
    for d in dirs:
        segs = d.split('/')
        if len(segs) > 5 or SKIP_SEG.search(d.replace('/tests', '')) and 'test' not in segs[-1]:
            pass
        last = segs[-1].lower()
        # only canonical containers: <noun>/, <pkg>/<noun>/, src/<noun>/ (depth <= 2), never docs or vendored trees
        if last in NOUNS and len(segs) <= 3 and not re.search(r'(^|/)(node_modules|vendor|dist|build|docs?|website|tests?|examples?|__tests__|fixtures?)(/|$)', d):
            noun_dirs.setdefault(last, []).append(d)
    child_count = {}
    for noun, ds in noun_dirs.items():
        best = None
        for d in ds:
            pre = d + '/'
            kids = set()
            for p in paths:
                if p.startswith(pre):
                    first = p[len(pre):].split('/')[0]
                    if first.lower() not in ("index.ts", "index.js", "readme.md", "__init__.py", "mod.rs", "index.tsx") and not first.startswith('.'):
                        kids.add(first)
            if best is None or len(kids) > best[1]:
                best = (d, len(kids))
        if best and best[1] >= 10:
            child_count[noun] = best
    for i, l in enumerate(lines, 1):
        low = urllib.parse.unquote(l).lower()
        # tests
        for m in re.finditer(r'(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+)\s*(\+|k\+?)?\s+(?:unit\s+|integration\s+|e2e\s+|end-to-end\s+|automated\s+)?tests\b', low):
            n = int(m.group(1).replace(',', '')) * (1000 if (m.group(2) or '').startswith('k') else 1)
            claims.append({"kind": "tests", "line_no": i, "claimed": n, "measured": len(test_files)})
            if n and len(test_files) > 1.10 * n:
                findings.append({"check": "d_count_claim", "file": "README.md", "line_no": i, "line": l,
                                 "claimed": f"{m.group(0).strip()}", "measured": f"{len(test_files)} test files in tree (a lower bound on tests)",
                                 "measured_by": "git tree paths matching " + TEST_FILE.pattern})
        # languages
        for m in re.finditer(r'(?<![\w.])(\d{1,3})\s*(\+)?\s+(?:human\s+|spoken\s+|ui\s+)?languages\b', low):
            if re.search(r'programming|coding|code\s|query|scripting|syntax', low):
                continue
            n = int(m.group(1))
            if locale_n:
                claims.append({"kind": "languages", "line_no": i, "claimed": n, "measured": locale_n})
                if (locale_n < 0.90 * n) if m.group(2) else (abs(locale_n - n) > 0.10 * n):
                    findings.append({"check": "d_count_claim", "file": "README.md", "line_no": i, "line": l,
                                     "claimed": m.group(0).strip(), "measured": f"{locale_n} locales in the locale directory (including the English source)",
                                     "measured_by": "audit_locale.py n_locales_total (see locale.json)"})
        for m in re.finditer(r'(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+)\s*(\+)?\s+(?:[\w-]+\s+)?(' + "|".join(NOUNS) + r')\b', low):
            noun = m.group(3)
            if noun not in child_count:
                continue
            n = int(m.group(1).replace(',', ''))
            d, k = child_count[noun]
            if n < 3:
                continue
            plus = bool(m.group(2))
            claims.append({"kind": noun, "line_no": i, "claimed": n, "plus": plus, "measured": k, "dir": d})
            # "N+" is a floor: only an overclaim (tree has under 90% of N) is drift; exact N drifts both ways
            if (k < 0.90 * n) if plus else (abs(k - n) > 0.10 * n):
                findings.append({"check": "d_count_claim", "file": "README.md", "line_no": i, "line": l,
                                 "claimed": m.group(0).strip(), "measured": f"{k} entries directly under {d}/",
                                 "measured_by": f"git tree: count distinct first path segments under {d}/"})
    return claims, findings, {"test_files": len(test_files), "noun_dirs": {k: {"dir": v[0], "entries": v[1]} for k, v in child_count.items()}}

# ---------------------------------------------------------------- (e) engine claims
def min_major_minor(spec):
    """Smallest version satisfying a simple range like '>=18.0.0', '^20 || ^22', '>=3.9,<4'."""
    vs = []
    for m in re.finditer(r'(>=|\^|~|>|==|=)?\s*v?(\d+)(?:\.(\d+|x))?', spec):
        op = m.group(1) or ""
        if op == '>':
            continue
        vs.append((int(m.group(2)), int(m.group(3)) if m.group(3) and m.group(3).isdigit() else 0))
    return min(vs) if vs else None

def engine_claims(readme, engines_node, requires_python, pkgname="\x00"):
    findings = []; claims = []
    lines = readme.split('\n')
    MINW = r'(\+|\s*or\s+(?:higher|later|newer|above|greater)|\s*and\s+(?:up|above|later|newer))'
    for i, l in enumerate(lines, 1):
        low = urllib.parse.unquote(l)
        # node
        # lines that describe an older release of the package itself ("redis-py 5.1 supports Python 3.8+") are history
        if re.search(r'\b' + re.escape(pkgname) + r'\s+v?\d+\.\d+', low, re.I):
            continue
        for m in re.finditer(r'\bnode(?:\.?js)?\b[\s:-]*(?:version\s*)?(?:(>=|≥|\^|~|at\s+least|minimum(?:\s+of)?|min\.?)\s*)?v?(\d{1,2})(?:\.(\d+|x))?(?:\.\d+)?' + MINW + '?', low, re.I):
            op, maj, plus = m.group(1), int(m.group(2)), m.group(4)
            req = re.search(r'(requires?|required|prerequisites?|needs?)[\s:*_-]{0,6}$', low[:m.start()], re.I)
            if not (op or plus or req) or not (4 <= maj <= 30) or not engines_node:
                continue
            mv = min_major_minor(engines_node[0])
            if not mv:
                continue
            claims.append({"kind": "node", "line_no": i, "claimed": maj, "manifest": engines_node[0]})
            if maj != mv[0]:
                findings.append({"check": "e_engine_claim", "file": "README.md", "line_no": i, "line": l,
                                 "claimed": f"Node {m.group(0).strip()}", "measured": f"engines.node is '{engines_node[0]}' (minimum major {mv[0]})",
                                 "measured_by": engines_node[1]})
        for m in re.finditer(r'\bpython\b[\s:-]*(?:version\s*)?(?:(>=|≥|\^|~|at\s+least|minimum(?:\s+of)?)\s*)?v?(3)\.(\d{1,2})(?:\.\d+)?' + MINW + '?', low, re.I):
            op, mi, plus = m.group(1), int(m.group(3)), m.group(4)
            req = re.search(r'(requires?|required|prerequisites?|needs?)[\s:*_-]{0,6}$', low[:m.start()], re.I)
            if not (op or plus or req) or not requires_python:
                continue
            mv = min_major_minor(requires_python[0])
            if not mv:
                continue
            claims.append({"kind": "python", "line_no": i, "claimed": f"3.{mi}", "manifest": requires_python[0]})
            if (3, mi) != mv:
                findings.append({"check": "e_engine_claim", "file": "README.md", "line_no": i, "line": l,
                                 "claimed": f"Python {m.group(0).strip()}", "measured": f"requires-python is '{requires_python[0]}' (minimum {mv[0]}.{mv[1]})",
                                 "measured_by": requires_python[1]})
    # one finding per (kind, line)
    seen = set(); uniq = []
    for f in findings:
        k = (f["check"], f["line_no"], f["claimed"].split()[0])
        if k not in seen:
            seen.add(k); uniq.append(f)
    return claims, uniq

# ---------------------------------------------------------------- driver
def audit(repo, meta=None, tree=None, locale_n=None, ref=None):
    if meta is None or tree is None:
        meta, tree = repo_meta_and_tree(repo)
    if not meta or not tree:
        return {"repo": repo, "err": "no meta or tree"}
    branch = meta["default_branch"]
    ref = ref or branch
    paths = set(t["path"] for t in tree["tree"] if t["type"] == "blob")
    dirs = set(t["path"] for t in tree["tree"] if t["type"] == "tree")
    readme_path = next((p for p in sorted(paths) if re.fullmatch(r'readme\.(md|markdown|mdx)', p, re.I)), None)
    docs = []
    readme = ""
    if readme_path:
        readme = raw(repo, ref, readme_path) or ""
        docs.append((readme_path, readme))
    for p in sorted(paths):
        if re.fullmatch(r'docs/[^/]+\.md', p, re.I) and len(docs) < 25:
            t = raw(repo, ref, p)
            if t:
                docs.append((p, t))
    o = {"repo": repo, "branch": branch, "ref": ref, "readme_path": readme_path, "readme_lines": len(readme.split('\n')) if readme else 0,
         "docs_files": [p for p, _ in docs], "tree_truncated": tree.get("truncated", False), "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    link_recs, fa = dead_links(docs)
    rel_checked, fb = relative_links(docs, repo, branch, paths, dirs, tree.get("truncated", False))
    manifests, mfiles, engines_node, requires_python = load_manifests(repo, ref, paths, readme)
    need_release = bool(re.search(r'(docker|npm|yarn|pnpm|pip|cargo|go get|go install|uses:|gem |implementation|poetry|bun add)', readme, re.I))
    release = latest_release(repo) if need_release else None
    vclaims, fc = version_claims(readme, repo, manifests, release, None)
    cclaims, fd, counts = count_claims(readme, paths, dirs, locale_n)
    eclaims, fe = engine_claims(readme, engines_node, requires_python, repo.split('/')[1])
    o.update({"links_checked": link_recs, "relative_checked": rel_checked, "manifests": {k: v[0] for k, v in manifests.items()},
              "manifest_files": sorted(mfiles), "engines_node": engines_node[0] if engines_node else None,
              "requires_python": requires_python[0] if requires_python else None, "latest_release": release,
              "version_claims": vclaims, "count_claims": cclaims, "tree_counts": counts, "engine_claims": eclaims,
              "findings": fa + fb + fc + fd + fe})
    o["counts"] = {"a_dead_link": len(fa), "b_missing_relative_target": len(fb), "c_version_drift": len(fc),
                   "d_count_claim": len(fd), "e_engine_claim": len(fe), "links_checked": len(link_recs),
                   "relative_links_checked": len(rel_checked)}
    o["_manifest_texts"] = mfiles
    o["_docs"] = docs
    return o

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(2)
    o = audit(a[0])
    out = a[a.index("--out") + 1] if "--out" in a else None
    s = {k: v for k, v in o.items() if not k.startswith('_')}
    if out:
        json.dump(s, open(out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({"counts": s.get("counts"), "findings": s.get("findings"), "err": s.get("err")}, indent=1, ensure_ascii=False))

if __name__ == "__main__":
    main()
