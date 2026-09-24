#!/usr/bin/env python3
"""
scan.py - AI-formatting detector for prose and web pages.

Usage:
  python3 scan.py <file-or-dir> [<file-or-dir> ...]
  python3 scan.py --strict <path>     # any HARD violation exits 1
  python3 scan.py --quiet <path>      # summary only

Scans .md .markdown .txt .html .htm. For HTML it checks the rendered prose
(scripts/styles/code stripped) plus a few markup-level tells (bold-in-body,
emoji, colon headings). Exit code is nonzero when a HARD-fail category is hit,
so it works as a pre-deploy gate:  python3 scan.py --strict ./site || abort
"""
import sys, os, re, html as _html

EXTS = {".md", ".markdown", ".txt", ".html", ".htm"}

# ---- word/phrase lists (curated from HUMANIZE-CONTENT.md v5.0) ----
TIER1 = ["delve","delves","delved","delving","multifaceted","tapestry","intricacies","showcasing"]
BANNED = [
 "intricate","underscores","nuanced","comprehensive","pivotal","groundbreaking","innovative",
 "holistic","commendable","noteworthy","meticulous","meticulously","invaluable","utilizes","utilize",
 "facilitates","facilitate","endeavors","navigating","navigate","realm","landscape","testament",
 "robust","seamless","seamlessly","foster","fostering","bolster","bolstering","surpassing","elevate",
 "amplify","catalyze","spearhead","harness","harnessing","leverage","leveraging","optimize","optimizing",
 "streamline","streamlining","empower","empowering","bespoke","scalable","paradigm","synergy","ecosystem",
 "bedrock","cornerstone","linchpin","underpinning","zeitgeist","crucial","vital","game-changer",
 "game-changing","cutting-edge","state-of-the-art","next-level","best-in-class","world-class","top-notch",
 "unparalleled","unmatched","unrivaled","transformative","revolutionary","disruptive","trailblazing",
 "pioneering","supercharge","turbocharge","catapult","unlock","unlocking","sophisticated","demystify",
]
PHRASES = [
 "it's worth noting","it is worth noting","it's important to note","it is important to note",
 "in today's digital age","in the realm of","one might argue","it goes without saying",
 "at the end of the day","when it comes to","on the other hand","let's dive in","without further ado",
 "needless to say","make no mistake","the fact of the matter is","in terms of","with that being said",
 "having said that","at its core","in a nutshell","the bottom line is","all things considered",
 "actionable insights","key takeaways","deep dive","moving forward","going forward","low-hanging fruit",
 "pain point","value proposition","thought leadership","rest assured","feel free to","don't hesitate to",
 "i hope this helps","in conclusion","to summarize","in today's","needless to say",
]
TRANSITIONS = ["furthermore","moreover","additionally","consequently","nevertheless","thus","hence",
 "thereby","nonetheless","notwithstanding","henceforth","whereby","wherein","therein"]
# web / marketing CTA tells
CTA = ["get started today","unlock the power","take it to the next level","transform your",
 "supercharge your","elevate your","revolutionize","join thousands","trusted by thousands",
 "say goodbye to","take your .* to the next level","powered by ai","the future of",
 "in today's fast-paced","whether you're a"]

EMOJI = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF✨✅⚡⭐✔]")

def hard(cat): return cat in {"em_dash","tier1","label","heading_colon","bold_body","emoji"}

def strip_html(t):
    t = re.sub(r"(?is)<(script|style|code|pre)\b.*?</\1>", " ", t)
    t = re.sub(r"(?s)<[^>]+>", " ", t)
    return _html.unescape(t)

def scan_text(raw, is_html):
    # exempt code: markdown fenced blocks and inline code (examples live here)
    raw = re.sub(r"(?s)```.*?```", "\n", raw)
    raw = re.sub(r"`[^`\n]+`", " ", raw)
    prose = strip_html(raw) if is_html else raw
    markup = re.sub(r"(?is)<(script|style|code|pre)\b.*?</\1>", " ", raw) if is_html else raw
    low = prose.lower()
    hits = {}
    def add(cat, items):
        if items: hits[cat] = items

    # em dash + double hyphen (prose)
    em = prose.count("—") + len(re.findall(r"(?<!-)--(?!-)", prose))
    if em: add("em_dash", [f"{em} found (— or --)"])
    # tier1
    t1 = [w for w in TIER1 if re.search(r"\b"+re.escape(w)+r"\b", low)]
    add("tier1", t1)
    # banned words
    bw = sorted({w for w in BANNED if re.search(r"\b"+re.escape(w)+r"\b", low)})
    add("banned_words", bw)
    # phrases + transitions + CTA
    ph = [p for p in PHRASES if p in low]
    add("phrases", ph)
    tr = [w for w in TRANSITIONS if re.search(r"\b"+re.escape(w)+r"\b", low)]
    add("transitions", tr)
    cta = [c for c in CTA if re.search(c, low)]
    add("cta_marketing", cta)
    # LABEL: structures  (**Word:**  or <strong>Word:</strong>)
    lab = re.findall(r"\*\*[^*\n]{1,40}:\*\*", markup) + re.findall(r"(?is)<(?:strong|b)>[^<]{1,40}:</(?:strong|b)>", markup)
    add("label", lab[:10])
    # colon in headings (md ###, and html h1-4) excluding time codes
    hc = re.findall(r"(?m)^#{1,4}\s+.*\w:\s+\S", markup) + re.findall(r"(?is)<h[1-4][^>]*>[^<]*\w:\s*\S[^<]*</h[1-4]>", markup)
    add("heading_colon", [h.strip()[:60] for h in hc[:10]])
    # bold in body (markdown **..** on non-heading lines; html <strong>/<b> inside <p>)
    bb = []
    for ln in markup.splitlines():
        if ln.lstrip().startswith("#"): continue
        bb += [m for m in re.findall(r"\*\*[^*\n]{2,60}\*\*", ln) if not m.endswith(":**")]
    bb += re.findall(r"(?is)<p(?:\s[^>]*)?>.*?<(?:strong|b)>.*?</(?:strong|b)>.*?</p>", markup)[:0]  # html bold-in-p (counted below)
    pbold = len(re.findall(r"(?is)<p(?:\s[^>]*)?>(?:(?!</p>).)*?<(?:strong|b)>", markup))
    if pbold: bb.append(f"{pbold} <strong>/<b> inside <p>")
    add("bold_body", bb[:10])
    # exclamation in prose
    # Do not treat the programming inequality operator (!=) as punctuation.
    exq = len(re.findall(r"!(?!=)", prose))
    if exq: add("exclamation", [f"{exq} in prose"])
    # "This is" openers (line/sentence start)
    ti = re.findall(r"(?m)(?:^|\.\s+)This is\b", prose)
    if ti: add("this_is_opener", [f"{len(ti)}"])
    # There is/are openers
    th = re.findall(r"(?m)(?:^|\.\s+)There (?:is|are)\b", prose)
    if len(th) > 1: add("there_is_opener", [f"{len(th)} (max 1)"])
    # emoji
    em2 = EMOJI.findall(markup)
    if em2: add("emoji", [f"{len(em2)} found: "+ " ".join(dict.fromkeys(em2))[:30]])
    # FAQ heading
    if re.search(r"(?i)frequently asked questions", raw): add("faq_heading", ["'Frequently Asked Questions'"])
    # long lists (6+ consecutive bullets / <li>)
    runs = re.findall(r"(?m)^\s*[-*]\s+.+(?:\n\s*[-*]\s+.+){5,}", raw)
    lis = len(re.findall(r"(?is)<li\b", raw))
    if runs: add("long_list", [f"{len(runs)} list(s) with 6+ bullets"])
    return hits

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    quiet = "--quiet" in flags
    if not args:
        print(__doc__); sys.exit(2)
    files = []
    for p in args:
        if os.path.isdir(p):
            for root,_,fs in os.walk(p):
                if "node_modules" in root or "/.git" in root: continue
                for f in fs:
                    if os.path.splitext(f)[1].lower() in EXTS: files.append(os.path.join(root,f))
        elif os.path.isfile(p): files.append(p)
    if not files: print("no scannable files found"); sys.exit(2)

    total_hard = 0; total_soft = 0; rows = []
    for fp in sorted(files):
        try: raw = open(fp, encoding="utf-8", errors="replace").read()
        except Exception as e: print(f"skip {fp}: {e}"); continue
        is_html = fp.lower().endswith((".html",".htm"))
        hits = scan_text(raw, is_html)
        hardn = sum(1 for c in hits if hard(c))
        softn = len(hits) - hardn
        total_hard += hardn; total_soft += softn
        rows.append((fp, hits, hardn, softn))
        if quiet: continue
        if not hits:
            print(f"\n✓ CLEAN  {fp}"); continue
        print(f"\n{'✗ FAIL' if hardn else '⚠ WARN'}  {fp}   [{hardn} hard, {softn} soft]")
        for cat, items in hits.items():
            mark = "HARD" if hard(cat) else "soft"
            shown = items if isinstance(items, list) else [str(items)]
            print(f"   [{mark}] {cat}: " + (", ".join(map(str, shown))[:160] if shown else ""))

    clean = sum(1 for _,h,_,_ in rows if not h)
    print(f"\n{'='*60}\nSCANNED {len(rows)} file(s): {clean} clean, "
          f"{sum(1 for _,_,hd,_ in rows if hd)} with HARD fails, "
          f"{total_hard} hard / {total_soft} soft violations total.")
    if total_hard:
        print("RESULT: FAIL - hard AI-formatting tells present. Not deploy-clean.")
        sys.exit(1)
    if total_soft:
        print("RESULT: WARN - soft tells present. Review before deploy.")
        sys.exit(0 if "--strict" not in flags else 1)
    print("RESULT: PASS - no AI-formatting tells detected. Deploy-clean.")
    sys.exit(0)

if __name__ == "__main__":
    main()
