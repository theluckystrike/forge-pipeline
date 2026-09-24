#!/usr/bin/env python3
"""WhiteHERO v3 dashboard generator.

Reads ~/oss-pipeline/state/kpi.db (read only) and writes ~/oss-pipeline/WHITEHERO-DASHBOARD.html:
  - plan section 12 weekly metrics, each computed with the exact SQL printed in the plan
  - lane funnel counts (targets, B>=0.4, audited, drafted, sent, replied, paid)
  - contributions by status, days to the Medusa fuse, last watcher summary, generated-at time
Copying to ~/Desktop is a separate step done by the caller (never write code under Desktop).
"""
import html, os, re, sqlite3, sys
from datetime import date, datetime, timezone

PIPE = os.path.expanduser("~/oss-pipeline")
DB = f"{PIPE}/state/kpi.db"
OUT = f"{PIPE}/WHITEHERO-DASHBOARD.html"
WATCH_LOG = f"{PIPE}/state/watch.log"
FUSE = date(2026, 10, 7)

# (metric, target, red flag, exact SQL from plan section 12, tables the SQL reads)
METRICS = [
    ("Qualified targets (B >= 0.4) added", "100+", "under 40",
     "select count(*) from targets where B>=0.4 and discovered_at>date('now','-7 day')", ["targets"]),
    ("Audits with evidence dirs", "40+", "under 20",
     "select count(*) from audits where created_at > date('now','-7 day')", ["audits"]),
    ("L1 sends / reply rate", "40 per week / 5%+",
     "under 3% after 80 sends (rewrite) or after 320 (kill), per the section 5 gate",
     "select count(*), round(100.0*sum(replied)/count(*),1) from outreach where lane='L1'", ["outreach"]),
    ("Signed retainers (cumulative)", "1 by day 67 (midpoint of the 52 to 82 window), 3 by day 90", "0 at day 82",
     "select count(*) from deals where status='paid' and lane='L1'", ["deals"]),
    ("Proof-PR merge rate on qualified targets", "50%+", "under 30%",
     "select avg(status='MERGED') from contributions where target_qualified=1", ["contributions"]),
    ("Client-repo PR merge rate", "68%+", "under 50%",
     "select sum(merged_prs)*1.0/sum(delivered_prs) from deals where status='paid'", ["deals"]),
    ("Expensify assignment rate", "5%+", "under 3% after 40",
     "select avg(assigned) from proposals where posted_at is not null", ["proposals"]),
    ('Public "automated" or "spam" callouts', "0", "1",
     'watch.sh greps PR comments for "bot|automated|spam|AI-generated"', []),
    ("Cash collected (cumulative)", "on the base curve", "below conservative at day 60",
     "select sum(paid_usd) from deals", ["deals"]),
    ("Operator hours / $ per hour", "under 80 h, $100/h+", "under $35/h at day 60",
     "select (select sum(paid_usd) from deals where paid_at > date('now','-30 day')) / "
     "(select sum(hours) from hours where week > date('now','-30 day'))", ["deals", "hours"]),
]
LANES = [("L1", "Owner-side maintenance retainer"), ("L2", "Locale parity and add-i18n sale"),
         ("L3", "Expensify Help Wanted proposals"), ("L4", "Codebase-licensing referral"),
         ("L5", "Contribution-as-marketing packs")]

def esc(x): return html.escape(str(x), quote=True)

def fmt(v):
    if v is None: return None
    if isinstance(v, float): return f"{v:.3f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))
    return str(v)

def main():
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=30)
    q = lambda sql, a=(): con.execute(sql, a).fetchall()
    tables = {r[0] for r in q("select name from sqlite_master where type='table'")}
    counts = {t: q(f"select count(*) from {t}")[0][0] for t in sorted(tables)}
    now_utc = datetime.now(timezone.utc)
    days_to_fuse = (FUSE - date.today()).days

    # watcher log: red flag lines and last summary
    wl = open(WATCH_LOG).read().splitlines() if os.path.exists(WATCH_LOG) else []
    red_human = [l for l in wl if "RED FLAG" in l and "[bot-author]" not in l]
    red_bot = [l for l in wl if "RED FLAG [bot-author]" in l]
    summaries = [l for l in wl if " SUMMARY " in l]

    rows = []
    for name, target, flag, sql, deps in METRICS:
        if not deps:
            if not summaries:
                val, note = "no data yet", "watch.sh has not run"
            else:
                val = str(len(red_human))
                note = f"{len(red_bot)} bot-author matches logged separately; source state/watch.log"
        elif any(counts.get(t, 0) == 0 for t in deps):
            empty = [t for t in deps if counts.get(t, 0) == 0]
            val, note = "no data yet", "empty table: " + ", ".join(empty)
        else:
            r = q(sql)[0]
            parts = [fmt(x) for x in r]
            if all(p is None for p in parts):
                val, note = "no data yet", "query returned NULL (no matching rows)"
            else:
                val = " / ".join("NULL" if p is None else p for p in parts)
                if "reply" in name: val = f"{parts[0]} sends / {parts[1] or 0}%"
                note = ""
        rows.append((name, target, flag, sql, val, note))

    # lane funnel
    B_ALL = q("select count(*), sum(B>=0.4) from targets")[0]
    AUD_ALL = q("select count(distinct target_id) from audits")[0][0]
    funnel = [("All lanes (shared discovery pool)", B_ALL[0], B_ALL[1] or 0, AUD_ALL, "", "", "", "")]
    for code, label in LANES:
        if code == "L3":
            p = q("select count(*), sum(posted_at is not null), sum(assigned), sum(paid_usd>0), sum(paid_usd) from proposals")[0]
            funnel.append((f"{code} {label}", "n/a", "n/a", "n/a", p[0], p[1] or 0, p[2] or 0,
                           f"{p[3] or 0} (${p[4] or 0:,.0f})"))
            continue
        t = q("select count(distinct o.target_id), count(distinct case when t.B>=0.4 then o.target_id end), "
              "count(distinct a.target_id) from outreach o left join targets t on t.id=o.target_id "
              "left join audits a on a.target_id=o.target_id where o.lane=?", (code,))[0]
        o = q("select count(*), sum(sent_at is not null), sum(replied) from outreach where lane=?", (code,))[0]
        d = q("select count(*), sum(paid_usd) from deals where lane=? and status='paid'", (code,))[0]
        funnel.append((f"{code} {label}", t[0], t[1], t[2], o[0], o[1] or 0, o[2] or 0,
                       f"{d[0]} (${d[1] or 0:,.0f})"))

    contrib = q("select upper(status), count(*) from contributions group by upper(status) order by 2 desc")
    raw_lower = q("select count(*) from contributions where status<>upper(status)")[0][0]
    con.close()

    # ---------- HTML ----------
    css = """:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--ink:#c9d1d9;--ink2:#8b949e;--blue:#58a6ff;--green:#3fb950;--amber:#d29922;--red:#f85149}
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;background:var(--bg);color:var(--ink);max-width:1180px;margin:0 auto;padding:24px 16px 60px;line-height:1.5;font-size:15px}
h1{color:var(--blue);border-bottom:1px solid var(--line);padding-bottom:8px;font-size:26px;margin:8px 0 6px}
h2{color:#7ee787;margin-top:34px;font-size:20px;border-bottom:1px solid var(--line);padding-bottom:4px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:16px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px}
.kpi .v{display:block;font-size:26px;color:var(--blue);font-variant-numeric:tabular-nums;font-weight:600}
.kpi .v.warn{color:var(--amber)}
.kpi span{font-size:12px;color:var(--ink2)}
.tw{overflow-x:auto;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:var(--panel);color:var(--blue);white-space:nowrap}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.nd{color:var(--ink2);font-style:italic}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;background:#1f242c;padding:1px 5px;border-radius:4px;word-break:break-word}
pre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;background:#0b0e13;border:1px solid var(--line);border-radius:6px;padding:10px 12px;white-space:pre-wrap;word-break:break-word}
.small{font-size:12.5px;color:var(--ink2)}
"""
    h = ["<!DOCTYPE html>", '<html lang="en"><head><meta charset="utf-8">',
         '<meta name="viewport" content="width=device-width, initial-scale=1">',
         "<title>WhiteHERO v3 Dashboard</title>", f"<style>{css}</style></head><body>",
         "<h1>WhiteHERO v3 dashboard</h1>",
         f'<p class="small">Generated at {esc(now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"))} by bin/dashboard.py from state/kpi.db. '
         "Every value below is computed from the database at generation time.</p>"]
    total_c = sum(c for _, c in contrib)
    merged_c = dict(contrib).get("MERGED", 0); open_c = dict(contrib).get("OPEN", 0)
    h.append('<div class="kpis">')
    for v, lab, cls in [(days_to_fuse, "days to the Medusa fuse (2026-10-07)", "warn" if days_to_fuse <= 14 else ""),
                        (counts.get("targets", 0), "targets in the pool", ""),
                        (counts.get("audits", 0), "audits written", ""),
                        (counts.get("outreach", 0), "outreach rows", ""),
                        (counts.get("deals", 0), "deals", ""),
                        (f"{merged_c} / {total_c}", "contributions merged / total", ""),
                        (open_c, "contributions still open", "")]:
        h.append(f'<div class="kpi"><span class="v {cls}">{esc(v)}</span><span>{esc(lab)}</span></div>')
    h.append("</div>")

    h.append("<h2>Weekly metrics and red flags (plan section 12)</h2>")
    h.append('<div class="tw"><table><tr><th>Metric</th><th>Target from week 3</th><th>Red flag</th>'
             "<th>Current value</th><th>SQL (exact, from the plan)</th></tr>")
    for name, target, flag, sql, val, note in rows:
        cls = "nd" if val == "no data yet" else "n"
        cell = esc(val) + (f'<br><span class="small">{esc(note)}</span>' if note else "")
        h.append(f"<tr><td>{esc(name)}</td><td>{esc(target)}</td><td>{esc(flag)}</td>"
                 f'<td class="{cls}">{cell}</td><td><code>{esc(sql)}</code></td></tr>')
    h.append("</table></div>")

    h.append("<h2>Lane funnel</h2>")
    h.append('<p class="small">Targets carry no lane until outreach names one, so the first row is the shared pool. '
             "Lane rows count targets that have an outreach row for that lane. L3 reads the proposals table "
             "(drafted, posted, assigned, paid).</p>")
    h.append('<div class="tw"><table><tr><th>Lane</th><th>Targets</th><th>B &gt;= 0.4</th><th>Audited</th>'
             "<th>Drafted</th><th>Sent</th><th>Replied</th><th>Paid</th></tr>")
    for r in funnel:
        h.append("<tr><td>" + esc(r[0]) + "</td>" + "".join(f'<td class="n">{esc(x)}</td>' for x in r[1:]) + "</tr>")
    h.append("</table></div>")

    h.append("<h2>Contributions by status</h2>")
    h.append('<div class="tw"><table><tr><th>Status</th><th>Rows</th></tr>')
    for st, c in contrib:
        h.append(f'<tr><td>{esc(st)}</td><td class="n">{c}</td></tr>')
    h.append(f'<tr><td>Total</td><td class="n">{total_c}</td></tr></table></div>')
    if raw_lower:
        h.append(f'<p class="small">{raw_lower} rows store the status in lower case and are grouped with the upper case value.</p>')

    h.append("<h2>Watcher</h2>")
    h.append(f"<p>Medusa fuse: {days_to_fuse} days remain until 2026-10-07. No human review by then means stop.</p>")
    h.append(f"<p>Red flag lines in state/watch.log: {len(red_human)} from human authors, {len(red_bot)} from bot authors.</p>")
    last = summaries[-1] if summaries else "watch.sh has not written a summary yet"
    h.append(f"<pre>{esc(last)}</pre>")

    h.append("<h2>Table row counts</h2>")
    h.append('<div class="tw"><table><tr><th>Table</th><th>Rows</th></tr>')
    for t, c in counts.items():
        h.append(f'<tr><td>{esc(t)}</td><td class="n">{c}</td></tr>')
    h.append("</table></div>")
    h.append("</body></html>\n")
    page = "\n".join(h)
    bad = [c for c in page if c == "—"]
    if bad or " -- " in page:
        sys.exit("refusing to write: em-dash or double hyphen in output")
    tmp = OUT + ".tmp"
    open(tmp, "w").write(page)
    os.replace(tmp, OUT)
    print(f"wrote {OUT} ({len(page.encode())} bytes)")
    for name, target, flag, sql, val, note in rows:
        print(f"  {name}: {val}" + (f" [{note}]" if note else ""))
    for r in funnel:
        print("  funnel " + " | ".join(str(x) for x in r))
    print("  contributions " + ", ".join(f"{s}={c}" for s, c in contrib))
    print(f"  days_to_fuse={days_to_fuse}")

if __name__ == "__main__":
    main()
