#!/usr/bin/env python3
"""audit_locale.py: locale parity measure for one GitHub repo (WhiteHERO v3 stage 3).

gap(locale) = keys of the source (en) file that are missing in the locale, or whose value is
empty, or whose value is byte-identical to the English value. Identical values are NOT counted
when the English value is legitimately language-neutral: shorter than 3 characters, a URL, an
email, a number, or made only of placeholders/markup (no letters left after stripping them).
--ref switches the skip rule off, which reproduces the older plan-evidence/a3/pass2.py numbers.

Usage:
  python3 audit_locale.py owner/repo [--out file.json] [--ref] [--group SUBSTR]

Cost per repo: 2 REST calls (repos/{r}, git/trees recursive); every file is read from
raw.githubusercontent.com (free). Shared helpers (gh, raw, tree) are imported by audit_drift.py.
"""
import json, os, re, subprocess, sys, time, random, collections, urllib.parse
from concurrent.futures import ThreadPoolExecutor

PIPE = os.path.expanduser("~/oss-pipeline")
CALL_LOG = os.path.join(PIPE, "state", "audit_gh_calls.log")
TIER1 = ["de", "fr", "ja", "es", "pt-BR", "zh-CN", "ko", "it", "nl"]
REST_CAP = int(os.environ.get("AUDIT_REST_CAP", "1500"))

# ---------------------------------------------------------------- GitHub helpers
def _calls_used():
    try:
        with open(CALL_LOG) as f:
            return sum(1 for _ in f)
    except FileNotFoundError:
        return 0

def rate_left():
    r = subprocess.run(["gh", "api", "rate_limit", "--jq", ".resources.core.remaining"],
                       capture_output=True, text=True, timeout=60)
    try:
        return int(r.stdout.strip())
    except ValueError:
        return -1

def gh(path, allow_404=True):
    """One REST call through the gh CLI, logged to state/audit_gh_calls.log, with 20/40/80 s backoff."""
    used = _calls_used()
    if used >= REST_CAP:
        raise RuntimeError(f"audit REST budget exhausted ({used} >= {REST_CAP})")
    if used and used % 200 == 0:
        left = rate_left()
        if 0 <= left < 500:
            raise RuntimeError(f"shared core quota low: {left} left")
    for delay in (0, 20, 40, 80):
        if delay:
            time.sleep(delay)
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=180)
        with open(CALL_LOG, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')}\t{path}\t{r.returncode}\n")
        if r.returncode == 0:
            return json.loads(r.stdout) if r.stdout.strip() else None
        err = (r.stderr + r.stdout)
        if "404" in err or "Not Found" in err:
            return None
        if "409" in err or "Git Repository is empty" in err:
            return None
        if any(s in err for s in ("403", "429", "secondary rate", "rate limit")):
            continue
        return None
    raise RuntimeError(f"gh backoff exhausted for {path}")

def raw(repo, ref, path, timeout=60):
    """Free file read from raw.githubusercontent.com. Returns text or None."""
    url = f"https://raw.githubusercontent.com/{repo}/{ref}/{urllib.parse.quote(path)}"
    for attempt in range(2):
        r = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-w", "\n%{http_code}", url],
                           capture_output=True)
        out = r.stdout.decode("utf-8", "replace")
        body, _, code = out.rpartition("\n")
        if code == "200":
            return body
        if code == "404":
            return None
        time.sleep(1 + attempt)
    return None

def raw_url(repo, ref, path):
    return f"https://raw.githubusercontent.com/{repo}/{ref}/{urllib.parse.quote(path)}"

def repo_meta_and_tree(repo):
    """meta + recursive tree. 2 REST calls. Tree is pinned to the commit sha for reproducibility."""
    m = gh(f"repos/{repo}")
    if not m:
        return None, None
    br = m["default_branch"]
    t = gh(f"repos/{repo}/git/trees/{urllib.parse.quote(br)}?recursive=1")
    return m, t

# ---------------------------------------------------------------- language codes
ISO1 = set("""aa ab af ak am an ar as av ay az ba be bg bh bi bm bn bo br bs ca ce ch co cr cs cu cv cy da de dv dz ee el
en eo es et eu fa ff fi fj fo fr fy ga gd gl gn gu gv ha he hi ho hr ht hu hy hz ia id ie ig ii ik io is it iu iw ja jv ka
kg ki kj kk kl km kn ko kr ks ku kv kw ky la lb lg li ln lo lt lu lv mg mh mi mk ml mn mr ms mt my na nb nd ne ng nl nn no
nr nv ny oc oj om or os pa pi pl ps pt qu rm rn ro ru rw sa sc sd se sg si sk sl sm sn so sq sr ss st su sv sw ta te tg th
ti tk tl tn to tr ts tt tw ty ug uk ur uz ve vi vo wa wo xh yi yo za zh zu in ua""".split())
ISO3 = set("fil kab ckb yue ast zgh tzm ber sat szl hsb dsb nds gsw bar fur haw lij vec scn tok chr ceb hil ilo arq ary arz "
           "tlh sco frp kmr mai mni sah nqo gom kok brx doi".split())
LANG_RE = re.compile(r'^([A-Za-z]{2,3})(?:[-_]([A-Za-z]{4}))?(?:[-_]([A-Za-z]{2}|\d{3})|(?<=[a-z])([A-Z]{2}))?(@\w+)?$')

def norm_lang(tok):
    """Return a normalised code like 'pt-BR' / 'zh-Hans' / 'de' if tok is a language tag, else None."""
    m = LANG_RE.match(tok)
    if not m:
        return None
    base = m.group(1).lower()
    if base not in ISO1 and base not in ISO3:
        return None
    if len(m.group(1)) == 3 and not m.group(1).islower() and not m.group(1).isupper():
        return None
    out = base
    if m.group(2):
        out += "-" + m.group(2).title()
    if m.group(3) or m.group(4):
        out += "-" + (m.group(3) or m.group(4)).upper()
    if m.group(5):
        out += m.group(5)
    return out

def split_lang(stem):
    """Find a language tag inside a file stem. Returns (prefix, lang_raw, suffix) or None.
    Prefers the longest tag, e.g. locale_en-US -> ('locale_', 'en-US', '')."""
    if norm_lang(stem):
        return ("", stem, "")
    starts = [0] + [m.end() for m in re.finditer(r'[._-]', stem)]
    ends = [m.start() for m in re.finditer(r'[._-]', stem)] + [len(stem)]
    best = None
    for a in starts:
        for b in ends:
            if b <= a:
                continue
            cand = stem[a:b]
            if norm_lang(cand) and (best is None or len(cand) > len(best[1])):
                best = (stem[:a], cand, stem[b:])
    return best

def is_en(code):
    return code is not None and code.split("-")[0] == "en"

SRC_PREF = ["en", "en-US", "en-GB", "en-Latn-US"]

def tier1_match(codes):
    """Map each tier-1 target to the best present locale code."""
    out = {}
    low = {c.lower(): c for c in codes}
    alts = {
        "de": ["de", "de-DE"], "fr": ["fr", "fr-FR"], "ja": ["ja", "ja-JP"], "es": ["es", "es-ES", "es-419", "es-MX"],
        "pt-BR": ["pt-BR", "pt", "pt-PT"], "zh-CN": ["zh-CN", "zh-Hans-CN", "zh-Hans", "zh"], "ko": ["ko", "ko-KR"],
        "it": ["it", "it-IT"], "nl": ["nl", "nl-NL"],
    }
    for t in TIER1:
        for a in alts[t]:
            if a.lower() in low:
                out[t] = low[a.lower()]
                break
    return out

# ---------------------------------------------------------------- parsers
EXTS = ("json", "po", "pot", "yml", "yaml", "ts", "js", "mjs", "properties", "arb", "xlf", "xliff",
        "ftl", "toml", "php", "strings", "xml", "edn", "resx")
SKIP_SEG = re.compile(r'(^|/)(node_modules|vendor|vendors|third[_-]?party|bower_components|__tests__|__mocks__|tests?|'
                      r'fixtures?|e2e|dist|build|\.git|\.github|examples?|demo|coverage|storybook-static|public/vendor|'
                      r'site-packages|venv|\.venv|snapshots?|__snapshots__|mocks?|cypress|playwright)(/|$)', re.I)

META_KEYS = {"comment", "comments", "description", "context", "meaning", "placeholders", "_comment", "note", "notes",
             "developer_comment", "translator_comment", "maxLength", "max_length"}

def flatten(obj, pre="", out=None):
    if out is None:
        out = {}
    if isinstance(obj, dict) and obj:
        # {"message": "...", "comment": [...]} (pyright, chrome _locales, formatjs): the message is the leaf
        for f in ("message", "string", "defaultMessage", "translation"):
            if isinstance(obj.get(f), str) and all(k == f or k in META_KEYS for k in obj):
                out[pre] = obj[f]
                return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten(v, f"{pre}.{k}" if pre else str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            flatten(v, f"{pre}.{i}", out)
    else:
        out[pre] = obj
    return out

def strip_lang_root(obj):
    if isinstance(obj, dict) and len(obj) == 1:
        k = next(iter(obj))
        if norm_lang(str(k)) and isinstance(obj[k], dict):
            return obj[k]
    return obj

MSG_FIELDS = ("message", "string", "defaultMessage", "translation")

def reduce_message_objects(j):
    """Chrome _locales messages.json, formatjs/react-intl and saleor store {"id": {"message"|"string": ..., "description": ...}}.
    Keep only the translatable field so English-only descriptions do not count as untranslated keys."""
    if not isinstance(j, dict) or not j:
        return j
    vals = list(j.values())
    for f in MSG_FIELDS:
        n = sum(1 for v in vals if isinstance(v, dict) and f in v and isinstance(v[f], str))
        if n >= 0.8 * len(vals):
            return {k: v[f] for k, v in j.items() if isinstance(v, dict) and isinstance(v.get(f), str)}
    return j

def parse_po(txt, is_source):
    d = {}
    entries = re.split(r'\n\s*\n', txt.replace('\r\n', '\n'))
    def unq(lines):
        s = ""
        for l in lines:
            m = re.match(r'^\s*"(.*)"\s*$', l)
            if m:
                s += m.group(1)
        return s
    for e in entries:
        lines = [l for l in e.split('\n') if not l.startswith('#~')]
        if not any(l.startswith('msgid') for l in lines):
            continue
        cur = None; buf = collections.defaultdict(list)
        for l in lines:
            if l.startswith('#'):
                continue
            m = re.match(r'^(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?)\s+(".*")\s*$', l)
            if m:
                cur = m.group(1); buf[cur].append(m.group(2)); continue
            if cur and l.strip().startswith('"'):
                buf[cur].append(l.strip())
        mid = unq(buf.get("msgid", []))
        if not mid:
            continue
        ctx = unq(buf.get("msgctxt", []))
        key = (ctx + "\x04" if ctx else "") + mid
        val = unq(buf.get("msgstr", [])) if "msgstr" in buf else unq(buf.get("msgstr[0]", []))
        if is_source and not val:
            val = mid
        d[key] = val
    return d

def js_object_parse(txt):
    """Tiny JS/TS object-literal reader: returns flattened {key: string} for the top-level object
    after 'export default', 'module.exports =', or '= {'; if that yields nothing (e.g. registerPack("en", {...})),
    the first 20 '{' positions are tried and the largest result wins. Non-string values are ignored."""
    m = re.search(r'(export\s+default|module\.exports\s*=|exports\.\w+\s*=|=\s*(?=\{)|export\s+const\s+\w+[^=]*=)\s*', txt)
    start = txt.find('{', m.end() if m else 0)
    if start < 0:
        return {}
    best = _js_object_at(txt, start)
    if len(best) < 3:
        for mm in list(re.finditer(r'\{', txt))[:20]:
            r = _js_object_at(txt, mm.start())
            if len(r) > len(best):
                best = r
    return best

_IDENT = re.compile(r'[\w$.\-]+')

def _js_object_at(txt, start):
    i = start; n = len(txt); out = {}; stack = []; key = None; arr_idx = []

    def skip_ws(i):
        while i < n:
            if txt[i].isspace():
                i += 1
            elif txt.startswith('//', i):
                j = txt.find('\n', i); i = n if j < 0 else j + 1
            elif txt.startswith('/*', i):
                j = txt.find('*/', i + 2); i = n if j < 0 else j + 2
            else:
                break
        return i

    def read_str(i):
        q = txt[i]; j = i + 1; s = []
        while j < n and txt[j] != q:
            if txt[j] == '\\' and j + 1 < n:
                s.append(txt[j:j + 2]); j += 2; continue
            s.append(txt[j]); j += 1
        return "".join(s), j + 1

    path = []
    i = start
    kinds = []
    while i < n:
        i = skip_ws(i)
        if i >= n:
            break
        c = txt[i]
        if c == '{':
            kinds.append('o'); path.append(key if key is not None else ""); key = None; i += 1; continue
        if c == '[':
            kinds.append('a'); path.append(key if key is not None else ""); arr_idx.append(0); key = "0"; i += 1; continue
        if c == '}' or c == ']':
            k = kinds.pop() if kinds else 'o'
            if k == 'a' and arr_idx:
                arr_idx.pop()
            path.pop() if path else None
            key = None; i += 1
            if not kinds:
                break
            continue
        if c == ',':
            if kinds and kinds[-1] == 'a':
                arr_idx[-1] += 1; key = str(arr_idx[-1])
            else:
                key = None
            i += 1; continue
        in_obj = kinds and kinds[-1] == 'o'
        if in_obj and key is None:
            # read key
            if c in '"\'`':
                k, i = read_str(i)
            elif c == '[':
                i += 1; continue
            else:
                mm = _IDENT.match(txt, i)
                if not mm:
                    i += 1; continue
                k = mm.group(0); i += len(k)
                if k == '...':
                    continue
            i = skip_ws(i)
            if i < n and txt[i] == ':':
                key = k; i += 1
            continue
        # value
        if c in '"\'`':
            v, i = read_str(i)
            full = ".".join([p for p in path[1:] if p != ""] + [key if key is not None else ""])
            out[full.strip('.')] = v
            # string concatenation 'a' + 'b'
            j = skip_ws(i)
            while j < n and txt[j] == '+':
                j = skip_ws(j + 1)
                if j < n and txt[j] in '"\'`':
                    v2, j = read_str(j); out[full.strip('.')] += v2; i = j; j = skip_ws(j)
                else:
                    break
            if in_obj:
                key = None
            continue
        # other value: skip to , or closing bracket at this depth (handles functions roughly)
        depth = 0
        i0 = i
        while i < n:
            ch = txt[i]
            if ch in '"\'`':
                _, i = read_str(i); continue
            if ch in '([{':
                depth += 1
            elif ch in ')]}':
                if depth == 0:
                    break
                depth -= 1
            elif ch == ',' and depth == 0:
                break
            i += 1
        if i == i0:
            i += 1  # stray closer such as ')' inside an array: always make progress
        if in_obj:
            key = None
    return out

def parse_php(txt):
    out = {}; stack = []; key = None; idx = []
    for m in re.finditer(r"""'((?:[^'\\]|\\.)*)'|"((?:[^"\\]|\\.)*)"|=>|\[|\]|array\s*\(|\)|,|(//[^\n]*|/\*.*?\*/|#[^\n]*)""", txt, re.S):
        t = m.group(0)
        if m.group(3):
            continue
        if t == '=>':
            continue
        if t == '[' or t.startswith('array'):
            stack.append(key if key is not None else ""); key = None; continue
        if t in (']', ')'):
            if stack:
                stack.pop()
            key = None; continue
        if t == ',':
            continue
        s = m.group(1) if m.group(1) is not None else m.group(2)
        # decide key or value: a key is followed by =>
        after = txt[m.end():m.end() + 8].lstrip()
        if after.startswith('=>'):
            key = s
        else:
            if key is not None and stack:
                out[".".join([p for p in stack[1:] if p] + [key])] = s
            key = None
    return out

def parse_xlf(txt):
    src = {}; tgt = {}
    for m in re.finditer(r'<(trans-unit|unit)\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</\1>', txt, re.S):
        body = m.group(3)
        s = re.search(r'<source[^>]*>(.*?)</source>', body, re.S)
        t = re.search(r'<target[^>]*>(.*?)</target>', body, re.S)
        src[m.group(2)] = s.group(1).strip() if s else ""
        if t:
            tgt[m.group(2)] = t.group(1).strip()
    return src, tgt

def parse_file(path, txt, is_source):
    ext = path.rsplit('.', 1)[-1].lower()
    if txt is None:
        return None
    try:
        if ext in ("json", "arb"):
            j = json.loads(txt)
            j = strip_lang_root(j)
            j = reduce_message_objects(j)
            if ext == "arb" or (isinstance(j, dict) and any(str(k).startswith('@') for k in j)):
                j = {k: v for k, v in j.items() if not str(k).startswith('@')} if isinstance(j, dict) else j
            if isinstance(j, dict):
                j.pop("$schema", None)
            f = flatten(j)
            return {k: v for k, v in f.items() if isinstance(v, str)}
        if ext in ("po", "pot"):
            return parse_po(txt, is_source or ext == "pot")
        if ext in ("yml", "yaml"):
            import yaml
            y = yaml.safe_load(txt)
            y = strip_lang_root(y)
            f = flatten(y) if isinstance(y, (dict, list)) else {}
            return {k: v for k, v in f.items() if isinstance(v, str)}
        if ext in ("ts", "js", "mjs"):
            return js_object_parse(txt)
        if ext == "properties":
            d = {}; lines = txt.replace('\r\n', '\n').split('\n'); i = 0
            while i < len(lines):
                l = lines[i]; i += 1
                if not l.strip() or l.lstrip().startswith(('#', '!')):
                    continue
                while l.endswith('\\') and i < len(lines):
                    l = l[:-1] + lines[i].lstrip(); i += 1
                m = re.match(r'^\s*((?:[^=:\s\\]|\\.)+)\s*[=:\s]\s*(.*)$', l)
                if m:
                    d[m.group(1)] = m.group(2)
            return d
        if ext in ("xlf", "xliff"):
            src, tgt = parse_xlf(txt)
            return src if is_source else {"__xlf_src__": src, "__xlf_tgt__": tgt}
        if ext == "ftl":
            return {m.group(1): m.group(2).strip() for m in re.finditer(r'^([a-zA-Z][\w-]*)\s*=\s*(.*)$', txt, re.M)}
        if ext == "toml":
            d = {}; sec = ''
            for l in txt.splitlines():
                m = re.match(r'^\s*\[([^\]]+)\]', l)
                if m:
                    sec = m.group(1); continue
                m = re.match(r'^\s*([\w.\-"]+)\s*=\s*"(.*)"\s*$', l)
                if m:
                    d[(sec + '.' if sec else '') + m.group(1).strip('"')] = m.group(2)
            return d
        if ext == "php":
            return parse_php(txt)
        if ext == "strings":
            return {m.group(1): m.group(2) for m in re.finditer(r'^\s*"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;', txt, re.M)}
        if ext == "xml":
            d = {}
            for m in re.finditer(r'<string\s+name="([^"]+)"([^>]*)>(.*?)</string>', txt, re.S):
                if 'translatable="false"' in m.group(2):
                    continue
                d[m.group(1)] = m.group(3)
            for m in re.finditer(r'<plurals\s+name="([^"]+)"[^>]*>(.*?)</plurals>', txt, re.S):
                for q in re.finditer(r'<item\s+quantity="(\w+)"[^>]*>(.*?)</item>', m.group(2), re.S):
                    d[m.group(1) + "#" + q.group(1)] = q.group(2)
            return d
        if ext == "edn":
            return {m.group(1): m.group(2) for m in re.finditer(r':([\w.\-/]+)\s+"((?:[^"\\]|\\.)*)"', txt)}
        if ext == "resx":
            return {m.group(1): m.group(2) for m in re.finditer(r'<data\s+name="([^"]+)"[^>]*>\s*<value>(.*?)</value>', txt, re.S)}
    except Exception:
        return None
    return None

# ---------------------------------------------------------------- skip rule
PH = [r'\{\{[^{}]*\}\}', r'\{[^{}]*\}', r'%\d+\$[a-zA-Z@]', r'%(\([^)]*\))?[-+ #0]*\d*(\.\d+)?[sdifuxXeEgGc@%]',
      r'\$\{[^}]*\}', r'<[^>]+>', r'(?<![\w])[:@][\w.]+', r'\$t\([^)]*\)', r'&[#\w]+;', r'\$\w+', r'\\[ntr]']

def neutral(v):
    """True when an English value may legitimately stay identical in every language."""
    if not isinstance(v, str):
        return True
    s = v.strip()
    if len(s) < 3:
        return True
    if re.fullmatch(r'(https?://|www\.|mailto:)\S+', s) or re.fullmatch(r'[\w.+-]+@[\w-]+\.[\w.]+', s):
        return True
    if re.fullmatch(r'[-+]?[\d.,:%/ ]+', s):
        return True
    t = s
    for p in PH:
        t = re.sub(p, '', t)
    return not re.search(r'[^\W\d_]', t)

# ---------------------------------------------------------------- discovery
def discover_groups(paths):
    """Return candidate locale groups: {gid: {'kind', 'dir', 'langs': {code: [files]}, 'src': code}}."""
    groups = {}
    blobs = [p for p in paths if not SKIP_SEG.search(p) and not re.search(r'\.(spec|test|stories|d)\.[cm]?[jt]sx?$', p)]
    ext_ok = lambda p: p.rsplit('.', 1)[-1].lower() in EXTS and '.' in p.rsplit('/', 1)[-1]
    # flat: dir/<pre><lang><suf>.<ext>
    for p in blobs:
        if not ext_ok(p):
            continue
        d, _, fn = p.rpartition('/')
        stem, _, ext = fn.rpartition('.')
        if ext.lower() == 'xml':
            continue
        sp = split_lang(stem)
        if not sp:
            continue
        pre, lang, suf = sp
        code = norm_lang(lang)
        gid = f"flat::{d}::{pre}*{suf}.{ext}"
        g = groups.setdefault(gid, {"kind": "flat", "dir": d, "pattern": f"{pre}<lang>{suf}.{ext}", "langs": {}})
        g["langs"].setdefault(code, []).append(p)
    # source without a language tag: messages.properties, messages.xlf, main.pot, messages.pot
    for gid, g in list(groups.items()):
        d = g["dir"]; pat = g["pattern"]
        pre, _, rest = pat.partition("<lang>")
        ext = rest.rsplit('.', 1)[-1]
        if ext.lower() in ("xlf", "xliff"):
            # Angular/XLIFF: the untranslated source (messages.xlf) often sits outside the locale dir
            base = f"{pre.rstrip('._-')}{rest}".lstrip('/')
            hits = sorted((p for p in paths_set_cache if p.rsplit('/', 1)[-1] == base and not SKIP_SEG.search(p)),
                          key=lambda p: (0 if p.startswith(d) else 1, abs(p.count('/') - d.count('/'))))
            if hits:
                g["langs"]["en"] = [hits[0]]; g["src_untagged"] = True
                continue
        if any(is_en(c) for c in g["langs"]):
            continue
        cands = [f"{d}/{pre.rstrip('._-')}{rest}", f"{d}/{pre.rstrip('._-')}.{ext}"]
        cands += [f"{d}/{x}" for x in ("main.pot", "messages.pot", "django.pot", "default.pot", "template.pot",
                                        f"defaultMessages.{ext}", f"default.{ext}", f"source.{ext}", f"base.{ext}",
                                        f"messages.{ext}", f"strings.{ext}", f"translations.{ext}")]
        cands += sorted(p for p in paths_set_cache if p.startswith(d + "/") and p.count('/') == d.count('/') + 1 and p.endswith('.pot'))
        for c in cands:
            c = c.lstrip('/')
            if c in paths_set_cache:
                g["langs"]["en"] = [c]; g["src_untagged"] = True
                break
    # nested: D/<lang>/**/<file>.<ext>
    nested = collections.defaultdict(lambda: collections.defaultdict(list))
    for p in blobs:
        if not ext_ok(p):
            continue
        segs = p.split('/')
        for i in range(len(segs) - 1):
            code = norm_lang(segs[i])
            if not code:
                lp = re.fullmatch(r'(.+)\.lproj', segs[i])
                code = norm_lang(lp.group(1)) if lp else None
                if lp and lp.group(1) == "Base":
                    code = "en"
            if not code:
                av = re.fullmatch(r'values(?:-([a-z]{2,3})(?:-r([A-Z]{2}))?(?:-b\+[\w+]+)?)?', segs[i])
                if av and p.endswith("strings.xml"):
                    code = "en" if not av.group(1) else norm_lang(av.group(1) + ("-" + av.group(2) if av.group(2) else ""))
            if code and i + 1 < len(segs):
                D = "/".join(segs[:i])
                if segs[i].startswith("values"):
                    D += "/values-*"
                rest = "/".join(segs[i + 1:])
                if rest.lower().endswith('.xml') and not rest.endswith('strings.xml'):
                    break
                nested[D][code].append((rest, p))
                break
    for D, langs in nested.items():
        if len(langs) < 1:
            continue
        gid = f"nested::{D}"
        groups[gid] = {"kind": "nested", "dir": D, "pattern": "<lang>/<file>", "langs": {c: [p for _, p in v] for c, v in langs.items()},
                       "rel": {c: {r: p for r, p in v} for c, v in langs.items()}}
    out = {}
    for gid, g in groups.items():
        codes = list(g["langs"])
        src = next((c for c in SRC_PREF if c in g["langs"]), None) or next((c for c in codes if is_en(c)), None)
        if not src:
            continue
        g["src"] = src
        out[gid] = g
    return out

paths_set_cache = set()
LOCALE_CTX = re.compile(r'/(_?locales?|i18n|lang|langs|languages|translations?|messages|l10n|intl|strings|po|res/values[^/]*|nls)/', re.I)

def measure_group(repo, ref, g, ref_mode=False, fetch_cap=1500, seed=1):
    src = g["src"]
    src_files = sorted(g["langs"][src])
    if g["kind"] == "nested":
        rels = sorted(g["rel"][src])
        src_map = {r: g["rel"][src][r] for r in rels}
    else:
        src_map = {"": src_files[0]}
    fetched = []
    def load(p, is_src):
        t = raw(repo, ref, p)
        fetched.append(p)
        return parse_file(p, t, is_src)
    en = {}
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda kv: (kv[0], load(kv[1], True)), src_map.items()))
    for rel, d in res:
        if d:
            for k, v in d.items():
                en[f"{rel}::{k}" if rel else k] = v
    locales = [c for c in g["langs"] if c != src]
    measured_codes = [c for c in locales if not is_en(c)]
    per_file = max(1, len(src_map))
    sampled = False
    if len(measured_codes) * per_file > fetch_cap:
        t1 = set(tier1_match(measured_codes).values())
        rest = [c for c in measured_codes if c not in t1]
        random.Random(seed).shuffle(rest)
        keep = max(0, fetch_cap // per_file - len(t1))
        measured_codes = sorted(t1) + sorted(rest[:keep])
        sampled = True
    ext = src_files[0].rsplit('.', 1)[-1].lower()
    en_neutral = {k: neutral(v) for k, v in en.items()}

    def one(code):
        if g["kind"] == "nested":
            fm = g["rel"].get(code, {})
            loc = {}
            for rel, sp in src_map.items():
                if rel in fm:
                    d = load(fm[rel], False)
                    if d:
                        if "__xlf_tgt__" in d:
                            d = d["__xlf_tgt__"]
                        for k, v in d.items():
                            loc[f"{rel}::{k}"] = v
            files = [fm[r] for r in src_map if r in fm]
        else:
            p = sorted(g["langs"][code])[0]
            d = load(p, False)
            if d is None:
                return code, None
            if "__xlf_tgt__" in d:
                d = d["__xlf_tgt__"]
            loc = d; files = [p]
        present = missing = identical = 0
        miss_keys = []; ident_keys = []
        for k, ev in en.items():
            lv = loc.get(k)
            if lv is None or (isinstance(lv, str) and lv == "" and ev != ""):
                missing += 1; miss_keys.append(k); continue
            present += 1
            if ref_mode:
                if lv == ev:
                    identical += 1; ident_keys.append(k)
            elif lv == ev and not en_neutral[k]:
                identical += 1; ident_keys.append(k)
        n = len(en)
        return code, {"files": files, "locale_keys": len(loc), "present": present, "missing": missing,
                      "identical": identical, "gap_keys": missing + identical,
                      "gap_pct": round(100.0 * (missing + identical) / n, 1) if n else None,
                      "missing_pct": round(100.0 * missing / n, 1) if n else None,
                      "count_pct": round(100.0 * (1 - len(loc) / n), 1) if n else None,
                      "_miss": miss_keys, "_ident": ident_keys}
    out = {}
    if en:
        with ThreadPoolExecutor(8) as ex:
            for code, v in ex.map(one, measured_codes):
                if v:
                    out[code] = v
    return {"src": src, "src_files": list(src_map.values()), "en_keys": len(en),
            "en_neutral_keys": sum(1 for v in en_neutral.values() if v), "format": ext,
            "n_locales_total": len(g["langs"]), "n_locales_measured": len(out), "sampled": sampled,
            "en_variants_skipped": sorted(c for c in locales if is_en(c)), "locales": out, "raw_fetches": len(fetched)}

def audit(repo, meta=None, tree=None, ref_mode=False, group_hint=None, max_groups=6, ref=None):
    if meta is None or tree is None:
        meta, tree = repo_meta_and_tree(repo)
    if not meta or not tree:
        return {"repo": repo, "err": "no meta or tree"}
    pinned = ref
    paths = [t["path"] for t in tree["tree"] if t["type"] == "blob"]
    global paths_set_cache
    paths_set_cache = set(paths)
    o = {"repo": repo, "branch": meta["default_branch"], "commit_tree_sha": tree.get("sha"), "tree_truncated": tree.get("truncated", False),
         "n_files": len(paths), "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
         "definition": "gap = missing or empty or byte-identical to English" + ("" if ref_mode else " (identical skipped when English value is under 3 chars, a URL, email, number or placeholder-only)")}
    # the raw ref must be a commit or branch; tree sha does not work on raw.githubusercontent, so use the branch
    ref = pinned or meta["default_branch"]
    o["ref"] = ref
    groups = discover_groups(paths)
    if group_hint:
        groups = {k: v for k, v in groups.items() if group_hint in k or any(group_hint in f for fs in v["langs"].values() for f in fs)}
    def n_non_en(g):
        return sum(1 for c in g["langs"] if not is_en(c))
    # a group with fewer than 3 languages only counts inside a locale-style folder (avoids log_to_message.ts style hits)
    # a locale group must live in a locale-style folder: this drops docs trees, test specs and search mappings
    groups = {k: v for k, v in groups.items() if LOCALE_CTX.search("/" + v["dir"] + "/")}
    small = {k: v for k, v in groups.items() if n_non_en(v) == 0}
    groups = {k: v for k, v in groups.items() if n_non_en(v) >= 1}
    if not groups:
        o["locale_group"] = None
        # English-only product: an English source file in an i18n/locale dir with fewer than 3 languages beside it
        best = None
        for gid, g in small.items():
            if not re.search(r'(^|/)(locales?|i18n|lang|langs|languages|translations?|messages|l10n|intl|strings|res/values[^/]*)(/|$)', g["dir"] + "/", re.I):
                continue
            sp = g["langs"][g["src"]] if g["kind"] == "flat" else list(g["rel"][g["src"]].values())
            n = 0
            for p in sp[:20]:
                n += len(parse_file(p, raw(repo, ref, p), True) or {})
            if n and (best is None or n > best[0]):
                best = (n, gid, sp, sorted(g["langs"]))
        if best:
            o["english_only"] = {"group": best[1], "src_files": best[2][:20], "en_keys": best[0], "languages": best[3]}
        return o
    # rank candidates: number of locales first, then choose the one with most English keys among the top few
    ranked = sorted(groups.items(), key=lambda kv: -len(kv[1]["langs"]))[:max_groups]
    cand = []
    for gid, g in ranked:
        src_paths = g["langs"][g["src"]] if g["kind"] == "flat" else list(g["rel"][g["src"]].values())
        n = 0
        with ThreadPoolExecutor(8) as ex:
            for d in ex.map(lambda p: parse_file(p, raw(repo, ref, p), True), src_paths[:40]):
                n += len(d or {})
        cand.append((n, len(g["langs"]), gid))
    cand = [c for c in cand if c[0] >= 5] or [(0, 0, None)]
    cand.sort(key=lambda x: (-x[0], -x[1]))
    o["candidate_groups"] = [{"group": gid, "en_keys": n, "n_locales": nl} for n, nl, gid in cand if gid]
    n, nl, best = cand[0]
    if n == 0:
        o["locale_group"] = None
        return o
    g = groups[best]
    o["locale_group"] = best
    r = measure_group(repo, ref, g, ref_mode=ref_mode)
    o.update({k: v for k, v in r.items() if k != "locales"})
    locs = r["locales"]
    o["locales"] = {c: {k: v for k, v in s.items() if not k.startswith("_")} for c, s in sorted(locs.items())}
    o["gap_key_lists"] = {c: {"missing": s["_miss"], "identical": s["_ident"]} for c, s in locs.items()}
    t1 = tier1_match(list(locs))
    o["tier1"] = {t: {"locale": c, "gap_pct": locs[c]["gap_pct"], "gap_keys": locs[c]["gap_keys"],
                      "missing": locs[c]["missing"], "identical": locs[c]["identical"]} for t, c in t1.items()}
    o["tier1_absent"] = [t for t in TIER1 if t not in t1]
    if locs:
        w = max(locs.items(), key=lambda kv: (kv[1]["gap_pct"] or 0, kv[0]))
        o["worst"] = {"locale": w[0], "gap_pct": w[1]["gap_pct"], "gap_keys": w[1]["gap_keys"]}
        if o["tier1"]:
            wt = max(o["tier1"].items(), key=lambda kv: (kv[1]["gap_pct"] or 0, kv[0]))
            o["worst_tier1"] = {"target": wt[0], "locale": wt[1]["locale"], "gap_pct": wt[1]["gap_pct"], "gap_keys": wt[1]["gap_keys"]}
        o["total_gap_keys"] = sum(s["gap_keys"] for s in locs.values())
        gp = sorted(s["gap_pct"] for s in locs.values())
        o["median_gap_pct"] = gp[len(gp) // 2]
    o["raw_url_example"] = raw_url(repo, ref, o["src_files"][0]) if o.get("src_files") else None
    return o

def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(2)
    repo = a[0]
    out = a[a.index("--out") + 1] if "--out" in a else None
    hint = a[a.index("--group") + 1] if "--group" in a else None
    o = audit(repo, ref_mode="--ref" in a, group_hint=hint)
    s = {k: v for k, v in o.items() if k != "gap_key_lists"}
    if out:
        json.dump(o, open(out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: s.get(k) for k in ("repo", "locale_group", "src_files", "en_keys", "n_locales_total",
                                            "n_locales_measured", "tier1", "worst", "worst_tier1", "total_gap_keys", "err")},
                     ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
