#!/usr/bin/env python3
"""WhiteHERO v3 contacts agent (plan Phase 1 step 1.3, corrected by docs/AGENT-RULES.md).

Contacts come ONLY from the company's own website. No GitHub-derived emails.
Writes only targets.contact_name, contact_email, contact_source, R, score.

Usage:
  contacts.py --orgs medusajs=https://medusajs.com ...   test mode, no DB writes
  contacts.py --top 200 [--offset 0]                      crawl top targets (B>=0.4) and write
  contacts.py --recompute                                 recompute R and score only
"""
import argparse, concurrent.futures as cf, html, json, os, re, subprocess, sqlite3, sys, threading, time
import urllib.parse, urllib.robotparser
from datetime import datetime, timezone

PIPE = os.path.expanduser("~/oss-pipeline")
DB = os.path.join(PIPE, "state/kpi.db")
RAW = os.path.join(PIPE, "state/contacts-raw")
UA = "Mozilla/5.0 (Macintosh) contacts-check"
UA_TOKEN = "contacts-check"
MAX_BYTES = 400 * 1024
TIMEOUT = 10
PAGES = ["/", "/about", "/team", "/company", "/contact", "/partners"]
KEYWORDS = {"/about": r"about", "/team": r"team|people", "/company": r"company",
            "/contact": r"contact", "/partners": r"partner"}
PERSONA_PAGES = {"/about", "/team", "/company"}

PREFERRED = ["partnerships", "partners", "devrel", "founders", "hello", "hi", "contact", "team", "sales", "info"]
OTHER_OK = ["partnership", "partner", "business", "biz", "bd", "enterprise", "founder", "ceo", "cto", "office",
            "inquiries", "enquiries", "general", "community", "oss", "opensource", "developers", "dev", "hey", "howdy"]
EXCLUDED = re.compile(r"^(support|help|helpdesk|security|secure|privacy|dpo|gdpr|legal|abuse|no-?reply|do-?not-?reply|"
                      r"donotreply|careers?|jobs?|hr|recruit\w*|talent|hiring|press|media|pr|billing|invoices?|accounts?|"
                      r"payments?|ap|ar|finance|accounting|investors?|ir|dmca|compliance|trust|postmaster|webmaster|hostmaster|mailer-daemon|bounces?|"
                      r"events?|webinars?|unsubscribe|notifications?|alerts?|status|conduct|coc|vulnerabilit\w*|bugs?|feedback)$", re.I)
PLACEHOLDER = re.compile(r"^(you|your|yourname|name|email|user|username|example|test|someone|john|jane|john\.doe|"
                         r"jane\.doe|firstname|first\.last|me|foo|bar)$", re.I)
SOCIAL = re.compile(r"(^|\.)(twitter\.com|x\.com|github\.com|github\.io|gitlab\.com|gitlab\.io|linkedin\.com|facebook\.com|"
                    r"youtube\.com|medium\.com|discord\.gg|discord\.com|t\.me|npmjs\.com|readthedocs\.io|notion\.site|"
                    r"substack\.com|instagram\.com|reddit\.com|bsky\.app|mastodon\.social|"
                    r"opencollective\.com|patreon\.com|vercel\.app|netlify\.app|pages\.dev|gitbook\.io|linktr\.ee)$", re.I)
MULTI_SUFFIX = {"co.uk", "org.uk", "ac.uk", "com.au", "net.au", "org.au", "co.jp", "ne.jp", "or.jp", "com.br", "com.cn",
                "com.tw", "co.kr", "co.in", "co.nz", "co.za", "com.mx", "com.ar", "com.tr", "com.sg", "com.hk", "co.il",
                "com.ua", "com.pl", "co.id", "com.my", "com.vn", "com.co", "com.pe", "com.ph"}

TITLE_ORDER = ["CTO", "Co-founder", "Founder", "CEO", "Head of Engineering", "VP Engineering", "Head of DevRel",
               "Developer Relations"]
TITLE_RE = re.compile(
    r"\b(Chief Technology Officer|Chief Executive Officer|Co-?\s?founder|Founder|CEO|CTO|Head of Engineering|"
    r"VP,? (?:of )?Engineering|Vice President,? (?:of )?Engineering|Head of (?:DevRel|Developer Relations)|"
    r"Developer Relations|DevRel)\b", re.I)
TITLE_LINE = re.compile(
    r"^(?:(?:Co-?\s?founder|Founder|CEO|CTO|Chief (?:Technology|Executive) Officer|Head of Engineering|"
    r"VP,? (?:of )?Engineering|Vice President,? (?:of )?Engineering|Head of (?:DevRel|Developer Relations)|"
    r"Developer Relations(?: Lead| Manager| Engineer)?|DevRel(?: Lead| Engineer)?|President|Chairman|Chair|COO|CPO|CFO|"
    r"Chief \w+ Officer|Head of \w+|Engineering)"
    r"(?:\s*(?:&|and|,|/|\||\+|·|-)\s*)?)+(?:\s+(?:at|@)\s+(?P<co>[\w .&-]{2,40}))?$", re.I)
L = r"[^\W\d_]"
NAME_WORD = rf"[A-ZÀ-Þ]{L}*(?:[-'’]{L}+)*\.?"
NAME_RE = re.compile(rf"^{NAME_WORD}(?:\s+(?:van|von|de|da|der|del|di|la|le|dos|du)?\s*{NAME_WORD}){{1,3}}$")
NAME_STOP = set("""team our the meet about company founder founders cofounder co-founder ceo cto engineering head of and open source
careers contact blog product pricing docs community read more learn join us investors investor board advisors advisor
leadership inc ltd gmbh llc labs corp co cloud platform enterprise developer developers relations devrel vp vice president
chief officer technology executive home view all see news backed by partners partner customers our story mission values
features solutions resources get started sign up login log in free trial book demo request privacy terms policy
linkedin twitter github email office the welcome hello contact support sales marketing operations design data
security legal hiring we are why how what new latest announcing release series seed funding round""".split())
SECTION_BAD = re.compile(r"(?i)\b(investors?|backed by|backers|advisors?|advisory|angels?|board of|supported by|"
                         r"testimonials?|what (?:our |people |customers |users )?.{0,20}say|trusted by|customers|"
                         r"loved by|case stud|our partners)\b")
SECTION_GOOD = re.compile(r"(?i)\b(our team|the team|team members|leadership|founding team|the founders|our founders|founders|"
                          r"management|meet the|our people|executive team|who we are)\b")
LOCATIONS = set("""san francisco new york london berlin paris amsterdam remote tokyo singapore toronto bay area seattle austin
boston los angeles munich lisbon madrid barcelona warsaw krakow bangalore bengaluru mumbai delhi sydney melbourne dublin
zurich stockholm helsinki oslo copenhagen tel aviv vienna prague uk usa us germany france india israel canada brazil
spain italy poland portugal netherlands sweden finland norway denmark switzerland austria ireland japan china
australia hamburg montreal vancouver chicago denver miami atlanta portland brooklyn hong kong shanghai beijing
seoul taipei dubai cape town nairobi lagos mexico city buenos aires sao paulo bogota santiago lima kyiv bucharest
budapest athens istanbul belgrade sofia riga tallinn vilnius edinburgh manchester cambridge oxford salt lake city st louis san diego san jose palo alto mountain view""".split())
NAME_TITLE_RE = re.compile(
    r"(?P<name>" + NAME_WORD + r"(?:\s+" + NAME_WORD + r"){1,2})\s*(?:,|-|\u2013|\||\()\s*"
    r"(?P<title>(?:Co-?\s?founder|Founder|CEO|CTO|Chief (?:Technology|Executive) Officer|Head of Engineering|"
    r"VP,? (?:of )?Engineering|Head of (?:DevRel|Developer Relations)|Developer Relations)"
    r"(?:\s*(?:&|and|,|/)\s*(?:CEO|CTO|Co-?founder|Founder))*)"
    r"(?:\s*(?:,|\s(?:at|@|of|from))\s*(?P<co>[\w .&-]{2,40}))?")
EMAIL_RE = re.compile(r"(?<![\w.+-])([A-Za-z0-9][A-Za-z0-9._%+-]{0,63})@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
OBF_RE = re.compile(r"\b([A-Za-z0-9._%+-]{1,64})\s*[\[\(\{]\s*at\s*[\]\)\}]\s*([A-Za-z0-9-]+)\s*[\[\(\{]\s*dot\s*[\]\)\}]\s*"
                    r"([A-Za-z]{2,10})\b", re.I)

_host_lock = threading.Lock()
_host_last = {}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def reg_domain(host):
    host = (host or "").lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    if len(parts) >= 3 and ".".join(parts[-2:]) in MULTI_SUFFIX:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def normalize_origin(website):
    w = (website or "").strip()
    if not w:
        return None
    if not re.match(r"^https?://", w, re.I):
        w = "https://" + w
    p = urllib.parse.urlsplit(w)
    host = (p.hostname or "").lower()
    if not host or "." not in host:
        return None
    return "https://" + host


def polite_wait(host):
    with _host_lock:
        last = _host_last.get(host, 0)
        wait = last + 1.0 - time.time()
        _host_last[host] = max(time.time(), last + 1.0)
    if wait > 0:
        time.sleep(wait)


def fetch(url, log):
    """curl GET, follow redirects, 10 s timeout, keep at most 400 KB. Returns dict."""
    host = urllib.parse.urlsplit(url).hostname
    polite_wait(host)
    cmd = ["curl", "-sS", "-L", "--max-redirs", "5", "--max-time", str(TIMEOUT), "--compressed", "-A", UA,
           "-H", "Accept: text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5",
           "-w", "%{stderr}\n@@W %{http_code} %{url_effective} %{content_type}\n", url]
    t0 = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    body = p.stdout.read(MAX_BYTES + 1)
    truncated = len(body) > MAX_BYTES
    if truncated:
        body = body[:MAX_BYTES]
        while p.stdout.read(65536):  # drain the rest so curl finishes and reports status; keep only 400 KB
            pass
    try:
        _, err = p.communicate(timeout=TIMEOUT + 5)
    except subprocess.TimeoutExpired:
        p.kill(); _, err = p.communicate()
    err = err.decode("utf-8", "replace")
    m = re.search(r"@@W (\d+) (\S+) ?(.*)", err)
    code = int(m.group(1)) if m else 0
    final = m.group(2) if m else url
    ctype = (m.group(3) if m else "").strip()
    curl_err = err[:m.start()].strip() if m else err.strip()
    rec = {"ts": now(), "url": url, "final": final, "code": code, "ctype": ctype, "bytes": len(body),
           "truncated": truncated, "secs": round(time.time() - t0, 2), "rc": p.returncode,
           "err": curl_err[:200] if p.returncode not in (0, None) else ""}
    log.append(rec)
    text = body.decode("utf-8", "replace")
    return rec, text


def load_robots(origin, log):
    rec, text = fetch(origin + "/robots.txt", log)
    if rec["code"] == 0:
        rec, text = fetch(origin + "/robots.txt", log)  # one retry on network failure
    rp = urllib.robotparser.RobotFileParser()
    code = rec["code"]
    if code == 0:
        # unreachable robots.txt: RFC 9309 says treat as full disallow; record and skip the site
        rp.disallow_all = True
        return rp, "robots_unreachable:" + rec["err"]
    if code in (401, 403) and not text.strip():
        rp.allow_all = True
        return rp, "robots_%d_allow" % code
    if 400 <= code < 500 or "html" in rec["ctype"].lower():
        rp.allow_all = True
        return rp, "robots_%d_allow" % code
    if code >= 500:
        rp.disallow_all = True
        return rp, "robots_%d_disallow_all" % code
    rp.parse(text.splitlines())
    return rp, "robots_ok"


def decode_cf(hexs):
    try:
        b = bytes.fromhex(hexs)
        k = b[0]
        return "".join(chr(c ^ k) for c in b[1:])
    except Exception:
        return ""


def html_to_lines(raw):
    s = re.sub(r"(?is)<(script|style|noscript|svg|template)\b.*?</\1\s*>", "\n", raw)
    s = re.sub(r"(?s)<!--.*?-->", "\n", s)
    s = re.sub(r"<[^>]+>", "\n", s)
    s = html.unescape(s)
    lines = []
    for ln in s.split("\n"):
        ln = re.sub(r"[\s ​]+", " ", ln).strip()
        if ln:
            lines.append(ln)
    return lines


def extract_emails(raw, url):
    """Returns list of (email, method)."""
    out = []
    raw = re.sub(r"\\u00[0-9a-fA-F]{2}", lambda m: "@" if m.group(0).lower() == "\\u0040" else " ", raw)
    unesc = html.unescape(raw)
    for m in re.finditer(r"(?i)mailto:([^\"'<>\s?]+)", unesc):
        e = urllib.parse.unquote(m.group(1)).strip().strip(".,;")
        if "@" in e:
            out.append((e.lower(), "mailto"))
    for m in re.finditer(r"data-cfemail=\"([0-9a-fA-F]+)\"", raw):
        e = decode_cf(m.group(1))
        if "@" in e:
            out.append((e.lower(), "cfemail"))
    for m in re.finditer(r"/cdn-cgi/l/email-protection#([0-9a-fA-F]+)", raw):
        e = decode_cf(m.group(1))
        if "@" in e:
            out.append((e.lower(), "cfemail"))
    text = "\n".join(html_to_lines(raw))
    for m in EMAIL_RE.finditer(text):
        out.append((("%s@%s" % (m.group(1), m.group(2))).lower().strip("."), "text"))
    for m in OBF_RE.finditer(text):
        out.append((("%s@%s.%s" % m.groups()).lower(), "obfuscated"))
    # emails inside inline JSON / script payloads of the site's own page (e.g. Next.js data)
    src = re.sub(r"\\u00(?:3[cC]|3[eE]|22|27|26)", " ", unesc.replace("\\u0040", "@"))  # JSON-escaped < > " ' &
    src = re.sub(r"\\[nrt/]", " ", src)
    for m in EMAIL_RE.finditer(src):
        out.append((("%s@%s" % (m.group(1), m.group(2))).lower().strip("."), "page-source"))
    seen, res = set(), []
    for e, meth in out:
        e = re.sub(r"[^a-z0-9._%+@-]", "", e)
        if e.count("@") != 1 or e in seen:
            continue
        if re.search(r"\.(png|jpe?g|gif|svg|webp|avif|css|js|ico)$", e):
            continue
        seen.add(e)
        res.append((e, meth))
    return res


def role_rank(local):
    l = local.lower()
    if EXCLUDED.match(l) or PLACEHOLDER.match(l) or re.fullmatch(r"[0-9a-f]{16,}", l):
        return None  # hex locals are Sentry DSNs / tracking keys embedded in page source
    if l in PREFERRED:
        return PREFERRED.index(l)
    if l in OTHER_OK:
        return 20 + OTHER_OK.index(l)
    return 50  # personal or other on-domain address


def role_type(local):
    l = local.lower()
    if l in PREFERRED or l in OTHER_OK:
        return l
    if EXCLUDED.match(l):
        return "excluded"
    return "personal/other"


def canon_title(t):
    t = t.lower()
    if "technology" in t or t == "cto":
        return "CTO"
    if "co" in t and "founder" in t:
        return "Co-founder"
    if "founder" in t:
        return "Founder"
    if "executive" in t or t == "ceo":
        return "CEO"
    if "head of engineering" in t:
        return "Head of Engineering"
    if "engineering" in t:
        return "VP Engineering"
    if t.startswith("head of"):
        return "Head of DevRel"
    return "Developer Relations"


def good_name(n, org_words):
    n = n.strip(" ,.-|:")
    if not NAME_RE.match(n):
        return None
    words = [w.strip(".").lower() for w in n.split()]
    if any(w in NAME_STOP or w in org_words for w in words) or all(w.strip(",") in LOCATIONS for w in words):
        return None
    if len(n) > 40:
        return None
    return n


def titles_in(s):
    return [canon_title(m.group(1)) for m in TITLE_RE.finditer(s)]


def best_title(ts):
    ts = [t for t in ts if t in TITLE_ORDER]
    return min(ts, key=TITLE_ORDER.index) if ts else None


def co_ok(co, org_words):
    if not co:
        return True
    ws = set(re.findall(r"[a-z0-9]+", co.lower()))
    return bool(ws & org_words)


def extract_personas(raw, url, org_words):
    found = []
    # JSON-LD / inline JSON Person objects
    for m in re.finditer(r"(?is)<script[^>]+application/ld\+json[^>]*>(.*?)</script>", raw):
        try:
            data = json.loads(m.group(1).strip())
        except Exception:
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d); continue
            if not isinstance(d, dict):
                continue
            if str(d.get("@type", "")).lower() == "person" and d.get("name") and d.get("jobTitle"):
                t = best_title(titles_in(str(d["jobTitle"])))
                n = good_name(str(d["name"]), org_words)
                if t and n:
                    found.append((n, t, "json-ld"))
            stack.extend(v for v in d.values() if isinstance(v, (dict, list)))
    # inline JSON pairs like {"name":"Jane Doe","role":"Co-founder & CTO"}
    un = raw.replace('\\"', '"')
    for m in re.finditer(r'"name"\s*:\s*"([^"]{3,60})"[^{}]{0,300}?"(?:title|role|position|jobTitle|designation)"\s*:\s*"([^"]{2,80})"', un):
        t = best_title(titles_in(m.group(2)))
        n = good_name(html.unescape(m.group(1)), org_words)
        if t and n and re.fullmatch(r"[^@]{0,80}", m.group(2)) and co_ok(re.search(r"(?:at|@)\s+(.+)$", m.group(2)).group(1) if re.search(r"\s(?:at|@)\s+(.+)$", m.group(2)) else "", org_words):
            found.append((n, t, "inline-json"))
    for m in re.finditer(r'"(?:title|role|position|jobTitle|designation)"\s*:\s*"([^"]{2,80})"[^{}]{0,300}?"name"\s*:\s*"([^"]{3,60})"', un):
        t = best_title(titles_in(m.group(1)))
        n = good_name(html.unescape(m.group(2)), org_words)
        if t and n and not re.search(r"\s(?:at|@)\s", m.group(1)):
            found.append((n, t, "inline-json"))
    lines = html_to_lines(raw)
    if re.search(r"(?i)lorem ipsum", raw):
        return []  # placeholder page: team cards are fake (seen on hoppscotch.com/about)
    blocked_section = False
    for i, ln in enumerate(lines):
        core = ln.strip(" ,-|·:")
        if len(core) <= 60 and not TITLE_RE.search(core):
            if SECTION_BAD.search(core) and len(core.split()) >= 2:
                blocked_section = i  # heading-like phrase, not a one-word nav link
            elif SECTION_GOOD.search(core):
                blocked_section = False
        if blocked_section is not False and i - blocked_section > 80:
            blocked_section = False
        if blocked_section is not False:
            continue
        if len(core) <= 70 and TITLE_RE.search(core):
            tm = TITLE_LINE.match(core)
            if tm and co_ok(tm.group("co"), org_words):
                t = best_title(titles_in(core))
                if t:
                    prev = lines[i - 1] if i > 0 else ""
                    n = good_name(prev, org_words)
                    nxt2 = (lines[i + 1] if i + 1 < len(lines) else "").strip()
                    # "Co-founder" followed by another company name line (investor/advisor card): skip
                    if n and nxt2 and len(nxt2) <= 30 and not good_name(nxt2, set()) and not TITLE_RE.search(nxt2) \
                            and not re.search(r"[.!?\u201c\u201d\"]", nxt2) and nxt2[:1].isupper() \
                            and not (set(re.findall(r"[a-z0-9]+", nxt2.lower())) & org_words) and len(nxt2.split()) <= 3 \
                            and re.fullmatch(r"(?i)co-?\s?founder|founder", core):
                        continue
                    if n:
                        found.append((n, t, "name-line/title-line", core)); continue
                    nxt = lines[i + 1] if i + 1 < len(lines) else ""
                    if nxt and all(w.strip(",.").lower() in LOCATIONS for w in nxt.split()) and i + 2 < len(lines):
                        nxt = lines[i + 2]  # "Title / City / Name" card layout
                    n = good_name(nxt, org_words)
                    if n:
                        found.append((n, t, "title-line/name-line", core)); continue
        # "Name, Title" / "Name - Title" / "Name (Title)" / "Title: Name"
        for m in NAME_TITLE_RE.finditer(ln):
            if not co_ok(m.group("co"), org_words):
                continue
            n = good_name(m.group("name"), org_words)
            t = best_title(titles_in(m.group("title")))
            if n and t:
                found.append((n, t, "name, title", m.group("title")))
        for m in re.finditer(rf"\b(CTO|CEO|Co-?\s?founder|Founder|Head of Engineering|VP Engineering|Head of DevRel)\s*:\s*({NAME_WORD}(?:\s+{NAME_WORD}){{1,2}})", ln):
            n = good_name(m.group(2), org_words)
            t = best_title(titles_in(m.group(1)))
            if n and t:
                found.append((n, t, "title: name"))
    return found


def mx_lookup(domain):
    try:
        out = subprocess.run(["dig", "+short", "+time=3", "+tries=2", "MX", domain], capture_output=True, text=True,
                             timeout=15).stdout
    except Exception as e:
        return None, "dig_error:%s" % e
    recs = []
    for ln in out.splitlines():
        parts = ln.split()
        if len(parts) == 2 and parts[0].isdigit():
            recs.append((int(parts[0]), parts[1].rstrip(".")))
    recs = [r for r in recs if r[1]]  # null MX "0 ." has empty host
    if not recs:
        return None, "no_mx:" + out.strip()[:80]
    recs.sort()
    return recs[0][1], "ok"


def discover_links(raw, origin, final_host):
    links = {}
    site_rd = reg_domain(final_host)
    for m in re.finditer(r"(?i)href=[\"']([^\"'#]+)", raw):
        href = html.unescape(m.group(1)).strip()
        u = urllib.parse.urljoin(origin + "/", href)
        p = urllib.parse.urlsplit(u)
        if p.scheme not in ("http", "https") or reg_domain(p.hostname or "") != site_rd:
            continue
        path = p.path.rstrip("/") or "/"
        if path.count("/") > 2 or re.search(r"\.(pdf|png|jpe?g|svg|zip)$", path, re.I):
            continue
        # skip docs/blog subdomains for these keyword pages
        if (p.hostname or "").split(".")[0] in ("docs", "blog", "status", "community", "forum", "help", "support"):
            continue
        last = path.split("/")[-1].lower()
        for key, kw in KEYWORDS.items():
            if key in links:
                continue
            if re.fullmatch(rf"(?:{kw})(?:-?us|-?page)?|(?:our-?)?(?:{kw})|(?:{kw})s?", last):
                links[key] = "https://%s%s" % (p.hostname, path)
    return links


def analyze(res, pages_raw, host, final_host, org_words):
    res["pages"] = []
    site_rds = {reg_domain(h) for h in (host, final_host) if h and not SOCIAL.search(h)}
    res["site_domains"] = sorted(site_rds)
    cand = {}
    personas = []
    slug = re.sub(r"[^a-z0-9]", "", host.split(".")[0])
    for path, rec, text in pages_raw:
        pg = {"path": path, "url": rec["url"], "final": rec["final"], "code": rec["code"], "bytes": rec["bytes"],
              "err": rec["err"]}
        res["pages"].append(pg)
        if rec["code"] != 200 or not text:
            continue
        # never read a page served by GitHub or another third-party platform (AGENT-RULES: website only)
        if SOCIAL.search(urllib.parse.urlsplit(rec["final"]).hostname or ""):
            pg["note"] = "redirected_to_third_party"
            continue
        # a page that redirected back to home is not a separate page
        fpath = urllib.parse.urlsplit(rec["final"]).path.rstrip("/") or "/"
        if path != "/" and fpath == "/":
            pg["note"] = "redirected_home"
            continue
        for e, meth in extract_emails(text, rec["final"]):
            local, dom = e.split("@")
            dom_rd = reg_domain(dom)
            if dom_rd not in site_rds:
                continue
            if dom != dom_rd and re.match(r"(?:hr|jobs|careers|support|help|security|noreply|no-reply|bounce|lists?|mail-?lists?|o[0-9]+\.ingest|social)\.", dom):
                continue  # e.g. info@hr.ibm.com is an HR mailbox
            if e not in cand:
                cand[e] = {"email": e, "local": local, "domain": dom, "method": meth, "source": rec["final"],
                           "rank": role_rank(local), "type": role_type(local)}
        if path in PERSONA_PAGES:
            ow = set(org_words) | {slug}
            for f in extract_personas(text, rec["final"], ow):
                n, t, how = f[:3]
                disp = f[3] if len(f) > 3 else t
                disp = re.sub(r"\s+", " ", disp).strip(" ,-|:")[:60]
                disp = re.sub(r"(?i)[\s,]*(?:&|and|/)$", "", disp).strip(" ,")
                personas.append({"name": n, "title": t, "display": disp, "how": how, "source": rec["final"]})
    res["emails"] = sorted(cand.values(), key=lambda c: (999 if c["rank"] is None else c["rank"], c["email"]))
    # dedupe personas by name, keep best title
    byname = {}
    for p in personas:
        q = byname.get(p["name"])
        if not q or TITLE_ORDER.index(p["title"]) < TITLE_ORDER.index(q["title"]):
            byname[p["name"]] = p
    res["personas"] = sorted(byname.values(), key=lambda p: TITLE_ORDER.index(p["title"]))
    if all(p["code"] != 200 for p in res["pages"]):
        res["status"] = "no_pages_200"
    # choose best email + MX. Role addresses first (brief order); if the only usable addresses are personal
    # ones published on the site, prefer the one matching a named persona and make that persona the contact.
    best = next((c for c in res["emails"] if c["rank"] is not None), None)
    if best and best["rank"] >= 50 and res.get("personas"):
        for pz in res["personas"]:
            first = pz["name"].split()[0].lower()
            last = pz["name"].split()[-1].lower()
            m = next((c for c in res["emails"] if c["rank"] == 50 and
                      c["local"] in (first, last, first + "." + last, first + last, first[0] + last)), None)
            if m:
                best = dict(m, matched_persona=pz["name"])
                res["personas"] = [pz] + [q for q in res["personas"] if q is not pz]
                break
    res["best"] = None
    if best:
        mx, mxnote = mx_lookup(best["domain"])
        best = dict(best, mx=mx, mx_note=mxnote)
        res["best"] = best
    res["persona"] = res["personas"][0] if res["personas"] else None
    return res


def crawl_origin(origin, org_words):
    host = urllib.parse.urlsplit(origin).hostname
    log = []
    res = {"origin": origin, "ts": now(), "pages": [], "emails": [], "personas": [], "status": "ok", "notes": []}
    rp, rnote = load_robots(origin, log)
    res["robots"] = rnote
    if rnote.startswith("robots_unreachable"):
        res["status"] = "unreachable"
    blocked = []
    if res["status"] == "ok":
        home_rec, home = (None, "")
        plan = []
        for path in PAGES:
            if path == "/":
                url = origin + "/"
            else:
                url = None
            plan.append([path, url])
        # fetch home first to discover real links for the other 5 slots
        if rp.can_fetch(UA_TOKEN, origin + "/"):
            home_rec, home = fetch(origin + "/", log)
            final_host = urllib.parse.urlsplit(home_rec["final"]).hostname or host
            res["final_host"] = final_host
            disc = discover_links(home, "https://" + final_host, final_host) if home_rec["code"] == 200 else {}
            res["discovered"] = disc
            base = "https://" + final_host
            pages_raw = [("/", home_rec, home)]
        else:
            blocked.append(origin + "/")
            final_host = host
            res["final_host"] = host
            disc = {}
            base = origin
            pages_raw = []
        for path in PAGES[1:]:
            url = disc.get(path) or (base + path)
            if not rp.can_fetch(UA_TOKEN, url) or not rp.can_fetch(UA_TOKEN, path):
                blocked.append(url); continue
            rec, text = fetch(url, log)
            pages_raw.append((path, rec, text))
        for path, rec, text in pages_raw:
            if rec["code"] == 200 and text:
                fname = re.sub(r"[^A-Za-z0-9._-]", "_", (path.strip("/") or "home")) + ".html"
                d = os.path.join(RAW, host)
                os.makedirs(d, exist_ok=True)
                with open(os.path.join(d, fname), "w") as f:
                    f.write(text)
        analyze(res, pages_raw, host, final_host, org_words)
    res["blocked_by_robots"] = blocked
    if res["status"] != "ok":
        res["best"], res["persona"] = None, None
    res["fetch_log"] = log
    with open(os.path.join(RAW, "fetch-log.jsonl"), "a") as f:
        for r in log:
            f.write(json.dumps(dict(r, origin=origin)) + "\n")
    return res


def reparse(res, org_words):
    """Re-run extraction on the saved raw HTML of a cached crawl (no network except dig MX)."""
    if res.get("status") not in ("ok", "no_pages_200") or not res.get("pages"):
        return res
    host = urllib.parse.urlsplit(res["origin"]).hostname
    final_host = res.get("final_host") or host
    pages_raw = []
    for pg in res["pages"]:
        fname = re.sub(r"[^A-Za-z0-9._-]", "_", (pg["path"].strip("/") or "home")) + ".html"
        fp = os.path.join(RAW, host, fname)
        text = open(fp).read() if (pg["code"] == 200 and os.path.exists(fp)) else ""
        rec = {k: pg.get(k) for k in ("url", "final", "code", "bytes", "err")}
        pages_raw.append((pg["path"], rec, text))
    res = dict(res, status="ok", reparsed_at=now())
    return analyze(res, pages_raw, host, final_host, org_words)


def cache_path():
    return os.path.join(RAW, "results.jsonl")


def load_cache():
    c = {}
    if os.path.exists(cache_path()):
        for ln in open(cache_path()):
            try:
                r = json.loads(ln)
                c[r["origin"]] = r
            except Exception:
                pass
    return c


def org_words_for(org, repo=""):
    ws = set(re.findall(r"[a-z0-9]+", (org or "").lower())) | set(re.findall(r"[a-z0-9]+", (repo or "").lower()))
    ws.add(re.sub(r"[^a-z0-9]", "", (org or "").lower()))
    return {w for w in ws if len(w) >= 3}


def run_crawl(items, workers=2, use_cache=True, do_reparse=False):
    """items: list of (origin, org_words). Returns {origin: result}. Max 2 hosts at a time."""
    cache = load_cache() if use_cache else {}
    out, todo = {}, []
    for origin, ow in items:
        if origin in cache:
            r = cache[origin]
            if do_reparse:
                r = reparse(r, ow)
                with open(cache_path(), "a") as f:
                    f.write(json.dumps(r) + "\n")
            out[origin] = r
        else:
            todo.append((origin, ow))
    lock = threading.Lock()

    def job(a):
        origin, ow = a
        try:
            r = crawl_origin(origin, ow)
        except Exception as e:
            r = {"origin": origin, "status": "exception", "error": repr(e)[:300], "emails": [], "personas": [],
                 "best": None, "persona": None, "pages": [], "blocked_by_robots": []}
        with lock:
            with open(cache_path(), "a") as f:
                f.write(json.dumps(r) + "\n")
            b = r.get("best") or {}
            p = r.get("persona") or {}
            print("%-40s %-14s %-38s mx=%-5s %s" % (origin[:40], r.get("status"), b.get("email", "-"),
                                                    bool(b.get("mx")), (p.get("name", "") + " (" + p.get("title", "") + ")") if p else ""),
                  flush=True)
        return origin, r

    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for origin, r in ex.map(job, todo):
            out[origin] = r
    return out


def db():
    c = sqlite3.connect(DB, timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    return c


def pr_orgs(conn):
    """orgs where our PR is MERGED (contributions table). Reviewed-open PRs are checked via gh on our own PRs."""
    merged, open_prs = set(), []
    for repo, status, url in conn.execute("select repo, status, pr_url from contributions"):
        org = (repo or "").split("/")[0].lower()
        if (status or "").upper() == "MERGED":
            merged.add(org)
        elif (status or "").upper() == "OPEN" and url:
            open_prs.append((org, url))
    return merged, open_prs


def reviewed_orgs(open_prs, target_orgs):
    rev = set()
    for org, url in open_prs:
        if org not in target_orgs or org in rev:
            continue
        r = subprocess.run(["gh", "pr", "view", url, "--json", "reviews,reviewDecision"], capture_output=True,
                           text=True, timeout=30)
        try:
            d = json.loads(r.stdout)
            if d.get("reviews") or d.get("reviewDecision"):
                rev.add(org)
        except Exception:
            pass
    return rev


def defect_counts(conn):
    d = {}
    for tid, s, f, g in conn.execute(
            "select target_id, stale_claims, failing_examples, locale_gap_keys from audits a where id = "
            "(select max(id) from audits b where b.target_id=a.target_id)"):
        d[tid] = (s or 0) + (f or 0) + (1 if (g or 0) > 0 else 0)
    return d


def recompute(conn, ids=None, log=None):
    merged, open_prs = pr_orgs(conn)
    rows = conn.execute("select id, org, B, R, L, contact_name, contact_email from targets" +
                        (" where id in (%s)" % ",".join(str(i) for i in ids) if ids else "")).fetchall()
    torgs = {(r[1] or "").lower() for r in rows}
    rev = reviewed_orgs(open_prs, torgs)
    dc = defect_counts(conn)
    n = 0
    for tid, org, B, R, Lv, cname, cemail in rows:
        o = (org or "").lower()
        contact = 0.40 if (cname and cemail) else (0.20 if cemail else 0.0)
        pr = 0.30 if (o in merged or o in rev) else 0.0
        defect = 0.30 if dc.get(tid, 0) >= 5 else 0.0
        newR = round(contact + pr + defect, 4)
        score = round((B or 0) * newR * (0.5 if Lv is None else Lv), 6)
        conn.execute("update targets set R=?, score=? where id=?", (newR, score, tid))
        n += 1
        if log is not None:
            log.append({"id": tid, "org": org, "oldR": R, "R": newR, "contact": contact, "pr": pr, "defect": defect,
                        "defects": dc.get(tid), "score": score})
    conn.commit()
    return n


def report(conn, ids):
    cache = load_cache()
    rows = conn.execute("select id, org, repo, website, contact_name, contact_email, contact_source, B, R, L, score "
                        "from targets where id in (%s)" % ",".join(str(i) for i in ids)).fetchall()
    origins = {}
    for r in rows:
        o = normalize_origin(r[3])
        if o and o in cache:
            origins[o] = cache[o]
    st = {"target_rows": len(rows), "unique_origins_crawled": len(origins)}
    st["sites_with_200_page"] = sum(1 for v in origins.values() if any(p.get("code") == 200 for p in v.get("pages", [])))
    st["sites_status"] = {}
    for v in origins.values():
        st["sites_status"][v.get("status")] = st["sites_status"].get(v.get("status"), 0) + 1
    bt, mxp, mxf = {}, 0, 0
    for v in origins.values():
        b = v.get("best")
        if b:
            bt[b["type"]] = bt.get(b["type"], 0) + 1
            if b.get("mx"):
                mxp += 1
            else:
                mxf += 1
    st["sites_best_email_by_role"] = dict(sorted(bt.items(), key=lambda x: -x[1]))
    st["sites_mx_pass"], st["sites_mx_fail"] = mxp, mxf
    st["sites_only_excluded_addresses"] = sum(1 for v in origins.values() if v.get("emails") and not v.get("best"))
    st["sites_with_named_persona"] = sum(1 for v in origins.values() if v.get("persona"))
    st["targets_email_mx_ok"] = sum(1 for r in rows if r[5])
    st["targets_named_persona"] = sum(1 for r in rows if r[4])
    st["targets_persona_and_email"] = sum(1 for r in rows if r[4] and r[5])
    st["targets_generic_only"] = sum(1 for r in rows if r[5] and not r[4])
    st["share_generic_only_of_emailed"] = round(st["targets_generic_only"] / max(1, st["targets_email_mx_ok"]), 3)
    to, blocked, errs = [], [], {}
    for o, v in origins.items():
        for f in v.get("fetch_log", []):
            if f.get("err"):
                k = "timeout" if ("timed out" in f["err"] or f.get("rc") == 28) else ("dns" if "resolve" in f["err"] else "other")
                errs[k] = errs.get(k, 0) + 1
                if k == "timeout":
                    to.append(f["url"])
        blocked += v.get("blocked_by_robots", [])
    st["fetch_errors"] = errs
    st["timeouts"] = to
    st["blocked_by_robots"] = blocked
    st["unreachable_sites"] = [o for o, v in origins.items() if v.get("status") != "ok"]
    ex = [(r[1], r[4], r[5], r[6]) for r in rows if r[5]]
    ex.sort(key=lambda x: (x[1] is None, x[0]))
    st["examples"] = ex[:20]
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orgs", nargs="*", help="test mode: org=website pairs, no DB writes")
    ap.add_argument("--top", type=int, default=0)
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--recompute", action="store_true")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--reparse", action="store_true", help="re-extract cached sites from saved HTML")
    ap.add_argument("--refresh-cached", action="store_true", help="rewrite contact columns for every cached/written row")
    ap.add_argument("--report", type=int, default=0, help="report over top N B>=0.4 rows")
    a = ap.parse_args()
    os.makedirs(RAW, exist_ok=True)
    if a.orgs:
        items, meta = [], []
        for pair in a.orgs:
            org, site = pair.split("=", 1)
            o = normalize_origin(site)
            if not o or SOCIAL.search(urllib.parse.urlsplit(o).hostname):
                print("%-40s skip non_company_website %s" % (org, site)); continue
            items.append((o, org_words_for(org)))
        res = run_crawl(items, use_cache=not a.no_cache, do_reparse=a.reparse)
        print(json.dumps({k: {"best": v.get("best"), "persona": v.get("persona"), "personas": v.get("personas")[:5],
                              "emails": [(e["email"], e["type"], e["source"]) for e in v.get("emails", [])][:10],
                              "status": v.get("status"), "robots": v.get("robots"),
                              "blocked": v.get("blocked_by_robots"),
                              "pages": [(p["path"], p["code"], p["final"], p.get("note", "")) for p in v.get("pages", [])]}
                          for k, v in res.items()}, indent=1))
        return
    conn = db()
    if a.top or a.refresh_cached:
        if a.refresh_cached:
            # every row whose site is already crawled or that holds contact data from an earlier parser version;
            # no network except dig MX
            cache_keys = set(load_cache())
            allrows = conn.execute("select id, org, repo, website, contact_email, contact_name from targets").fetchall()
            rows = [r[:4] for r in allrows if normalize_origin(r[3]) in cache_keys or r[4] or r[5]]
        else:
            rows = conn.execute("select id, org, repo, website from targets where B >= 0.4 order by B desc, L desc "
                                "limit ? offset ?", (a.top, a.offset)).fetchall()
        items, seen, row_origin, skipped = [], set(), {}, []
        for tid, org, repo, site in rows:
            o = normalize_origin(site)
            if not o or SOCIAL.search(urllib.parse.urlsplit(o).hostname or ""):
                skipped.append((tid, org, site)); continue
            row_origin[tid] = (o, org)
            if o not in seen:
                seen.add(o); items.append((o, org_words_for(org, repo)))
        print("rows=%d unique_origins=%d skipped_non_company=%d" % (len(rows), len(items), len(skipped)), flush=True)
        with open(os.path.join(RAW, "skipped-non-company.jsonl"), "a") as f:
            for s in skipped:
                f.write(json.dumps({"ts": now(), "id": s[0], "org": s[1], "website": s[2]}) + "\n")
        if a.refresh_cached:
            ck = load_cache()
            items = [it for it in items if it[0] in ck]
        res = run_crawl(items, use_cache=not a.no_cache, do_reparse=a.reparse)
        written = 0
        for tid, (o, org) in row_origin.items():
            r = res.get(o) or {}
            b = r.get("best")
            p = r.get("persona")
            email = b["email"] if (b and b.get("mx")) else None
            name = ("%s (%s)" % (p["name"], p.get("display") or p["title"])) if p else None
            source = b["source"] if email else None
            conn.execute("update targets set contact_name=?, contact_email=?, contact_source=? where id=?",
                         (name, email, source, tid))
            written += 1
        conn.commit()
        print("contact rows written:", written)
        rl = []
        n = recompute(conn, ids=list(row_origin) + [s[0] for s in skipped], log=rl)
        with open(os.path.join(RAW, "recompute-%s.jsonl" % now().replace(":", "")), "w") as f:
            for r in rl:
                f.write(json.dumps(r) + "\n")
        print("R/score recomputed:", n)
    if a.report:
        ids = [r[0] for r in conn.execute("select id from targets where B >= 0.4 order by B desc, L desc limit ?",
                                          (a.report,))]
        print(json.dumps(report(conn, ids), indent=1))
    if a.recompute:
        rl = []
        n = recompute(conn, log=rl)
        with open(os.path.join(RAW, "recompute-all-%s.jsonl" % now().replace(":", "")), "w") as f:
            for r in rl:
                f.write(json.dumps(r) + "\n")
        print("R/score recomputed (all rows):", n)


if __name__ == "__main__":
    main()
