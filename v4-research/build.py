import json, math, html, os, shutil
M = json.load(open("model.json"))
op, B, lanes, comb, v3, exp, r3 = M["op"], M["B"], M["lanes"], M["combined"], M["v3"], M["expensify"], M["rule3"]
pct = lambda x, d=0: f"{100*x:.{d}f}%"
L = {l["key"]: l for l in lanes}

# ---------- charts ----------
def chart_n50():
    rows = sorted(M["routes"], key=lambda r: r["N50"])
    W, H, left, top, rh = 860, 30 + 30 * len(rows) + 40, 300, 20, 30
    xmin, xmax = math.log10(2), math.log10(3000)
    def X(v): return left + (math.log10(v) - xmin) / (xmax - xmin) * (W - left - 30)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Touches needed for a 50 percent chance of one paying client, by route, log scale">']
    for g in (3, 10, 30, 100, 300, 1000):
        x = X(g); s.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{H-30}" class="grid"/><text x="{x:.1f}" y="{H-12}" class="tick" text-anchor="middle">{g}</text>')
    for i, r in enumerate(rows):
        y = top + i * rh + rh / 2
        warm = "Warm" in r["name"] or "agency (mid)" in r["name"] or "Upwork" in r["name"]
        cls = "s3" if "Warm" in r["name"] else ("s2" if ("agency" in r["name"] or "Upwork" in r["name"]) else "s1")
        x = X(r["N50"])
        s.append(f'<line x1="{left}" y1="{y:.1f}" x2="{x:.1f}" y2="{y:.1f}" class="bar {cls}"/>')
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" class="dot {cls}"><title>{html.escape(r["name"])}: p = {100*r["p"]:.2f}% per touch, {r["N50"]:.0f} touches for 50%, {r["N90"]:.0f} for 90%</title></circle>')
        s.append(f'<text x="{left-8}" y="{y+4:.1f}" class="lbl" text-anchor="end">{html.escape(r["name"])}</text>')
        s.append(f'<text x="{x+9:.1f}" y="{y+4:.1f}" class="val">{r["N50"]:.0f}</text>')
    s.append(f'<text x="{left}" y="{H-12}" class="tick">touches for a 50% chance of one client (log scale)</text>')
    s.append('</svg>')
    return "\n".join(s)

def chart_lanes():
    keys = [l for l in lanes] + [None]
    W, H, left, top = 860, 300, 60, 20
    n = len(lanes) + 1
    gw = (W - left - 20) / n
    def Y(p): return top + (1 - p) * (H - top - 60)
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Probability of at least one paying client in 90 days per lane and combined, low, mid and high cases">']
    for g in (0, .25, .5, .75, 1):
        s.append(f'<line x1="{left}" y1="{Y(g):.1f}" x2="{W-20}" y2="{Y(g):.1f}" class="grid"/><text x="{left-8}" y="{Y(g)+4:.1f}" class="tick" text-anchor="end">{int(g*100)}%</text>')
    items = [(l["key"], l["low"]["P"], l["mid"]["P"], l["high"]["P"]) for l in lanes] + [("All v4", comb["low"], comb["mid"], comb["high"])]
    bw = gw / 4.2
    for i, (k, lo, mi, hi) in enumerate(items):
        x0 = left + i * gw + gw * 0.12
        for j, (v, cls) in enumerate(((lo, "s1"), (mi, "s2"), (hi, "s3"))):
            x = x0 + j * (bw + 2)
            s.append(f'<rect x="{x:.1f}" y="{Y(v):.1f}" width="{bw:.1f}" height="{Y(0)-Y(v):.1f}" rx="3" class="fill {cls}"><title>{k} {["low","mid","high"][j]}: {100*v:.1f}%</title></rect>')
            s.append(f'<text x="{x+bw/2:.1f}" y="{Y(v)-4:.1f}" class="val" text-anchor="middle">{100*v:.0f}</text>')
        s.append(f'<text x="{x0+1.5*bw+2:.1f}" y="{H-32}" class="lbl" text-anchor="middle">{k}</text>')
    s.append(f'<text x="{left}" y="{H-10}" class="tick">lanes A to F and all v4 lanes combined; bars are low, mid, high case; percent chance of at least one paying client by day 90</text>')
    s.append('</svg>')
    return "\n".join(s)

def chart_queue():
    W, H = 860, 120
    tot, aw = op["external_open"], op["open_awesome"]
    med = op["medusa_open"]; other = tot - aw - med
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Composition of the 119 open external pull requests">']
    x = 20; y = 30; h = 34; scale = (W - 40) / tot
    for v, cls, name in ((aw, "s2", "awesome-list PRs"), (med, "s3", "Medusa"), (other, "s1", "everything else")):
        w = v * scale
        s.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w-2,0):.1f}" height="{h}" rx="3" class="fill {cls}"><title>{name}: {v} of {tot}</title></rect>')
        s.append(f'<text x="{x+w/2:.1f}" y="{y+h+22}" class="lbl" text-anchor="middle">{name} {v} ({100*v/tot:.0f}%)</text>')
        x += w
    s.append(f'<text x="20" y="18" class="tick">{tot} open external PRs by the operator on 2026-09-24 (gh search, is:open, not own repos)</text>')
    s.append('</svg>')
    return "\n".join(s)

def lane_table():
    out = []
    for l in lanes:
        out.append(f'<tr><td class="k">{l["key"]}</td><td>{html.escape(l["name"])}</td><td class="num">{l["touches"]}</td><td class="num">{l["hours"]} h</td>'
                   f'<td class="num">{pct(l["low"]["P"],1)}</td><td class="num">{pct(l["mid"]["P"],1)}</td><td class="num">{pct(l["high"]["P"],1)}</td>'
                   f'<td class="src">{html.escape(l["src"])}</td></tr>')
    out.append(f'<tr class="total"><td></td><td>All lanes combined, 1 minus the product of (1 minus P) across lanes; lanes treated as independent</td><td class="num"></td><td class="num">{M["hours_total"]} h</td>'
               f'<td class="num">{pct(comb["low"],1)}</td><td class="num">{pct(comb["mid"],1)}</td><td class="num">{pct(comb["high"],1)}</td><td class="src">arithmetic, model.py</td></tr>')
    return "\n".join(out)

def route_table():
    out = []
    for r in sorted(M["routes"], key=lambda r: r["N50"]):
        out.append(f'<tr><td>{html.escape(r["name"])}</td><td class="num">{100*r["p"]:.2f}%</td><td class="num">{r["N50"]:.0f}</td><td class="num">{r["N90"]:.0f}</td><td class="src">{html.escape(r["src"])}</td></tr>')
    return "\n".join(out)

r3rows = "".join(f'<tr><td class="num">{n}</td><td class="num">{100*v:.1f}%</td></tr>' for n, v in r3.items())

ag = op["agencies"]
agrows = "".join(f'<tr><td>{k}</td><td class="num">{v}</td></tr>' for k, v in ag.items())

T = open("template.html").read()
vals = {
 "OPEN": op["external_open"], "AW": op["open_awesome"], "AWPCT": op["open_awesome_pct"], "MERGED": op["external_merged"],
 "COMB_LOW": pct(comb["low"]), "COMB_MID": pct(comb["mid"]), "COMB_HIGH": pct(comb["high"]),
 "V3_NOW": pct(v3["P_now"]), "V3_PLAN": pct(v3["P_plan"]), "V3_BELKINS": pct(v3["P_plan_belkins"]), "V3_PLATFORM": pct(v3["P_plan_platform"]),
 "A_MID": pct(L["A"]["mid"]["P"]), "A_HIGH": pct(L["A"]["high"]["P"]), "A_LOW": pct(L["A"]["low"]["P"]),
 "C_LOW": pct(L["C"]["low"]["P"]), "C_MID": pct(L["C"]["mid"]["P"]), "C_HIGH": pct(L["C"]["high"]["P"]),
 "E_MID": pct(L["E"]["mid"]["P"]), "F_MID": pct(L["F"]["mid"]["P"]), "F_LOW": pct(L["F"]["low"]["P"]), "F_HIGH": pct(L["F"]["high"]["P"]),
 "EXP_LOW": pct(exp["low"]), "EXP_MID": pct(exp["mid"]), "EXP_HIGH": pct(exp["high"]),
 "AGENCIES": op["agencies_total"], "HOURS": M["hours_total"],
 "CHART_N50": chart_n50(), "CHART_LANES": chart_lanes(), "CHART_QUEUE": chart_queue(),
 "LANE_TABLE": lane_table(), "ROUTE_TABLE": route_table(), "R3ROWS": r3rows, "AGROWS": agrows,
 "WARM_MID_P": f'{100*L["A"]["mid"]["p"]:.1f}%', "COLD_PLAT_P": f'{100*B["platform"]*0.10:.2f}%',
 "MULT_LO": f'{(B["hinge_survive"]*0.40*0.15)/(B["platform"]*0.10):.0f}', "MULT_HI": f'{(0.60*0.30)/(B["belkins"]*0.10):.0f}',
}
for k, v in vals.items():
    T = T.replace("{{" + k + "}}", str(v))
assert "{{" not in T, [l for l in T.splitlines() if "{{" in l][:3]
out = os.path.expanduser("~/oss-pipeline/WHITEHERO-V4-PLAN.html")
open(out, "w").write(T)
shutil.copy(out, os.path.expanduser("~/Desktop/WHITEHERO-V4-PLAN.html"))
shutil.copy(out, "WHITEHERO-V4-PLAN.html")
print(out, len(T))
