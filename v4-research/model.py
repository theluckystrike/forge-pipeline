"""WhiteHERO v4 model. Every input tagged with provenance. Output: model.json"""
import json, math, csv
def P1(p, n): return 1 - (1 - p) ** n
def N(q, p): return math.log(1 - q) / math.log(1 - p)

rows = list(csv.reader(open("r/open_prs.tsv"), delimiter="\t"))
aw = sum(1 for r in rows if "awesome" in r[1].lower())
op = {"external_merged": 128, "external_open": len(rows), "open_awesome": aw,
      "open_awesome_pct": round(100*aw/len(rows), 1),
      "medusa_prs": 10, "medusa_merged": 5, "medusa_open": 5, "medusa_open_approved": 1,
      "v3_targets": 1277, "v3_budget_pass": 746, "v3_audits": 213, "v3_drafts": 9, "v3_sent": 0,
      "agencies": {"Medusa Experts": 29, "Vendure partners": 21, "Twenty partners": 26,
                   "Directus agencies": 53, "Payload partners": 36, "Saleor partners": 13, "Strapi partners": 29}}
op["agencies_total"] = sum(op["agencies"].values())

# base rates (r/05-base-rates.md and r/01-*.md, fetched 2026-09-24)
B = {"belkins": 0.0045, "platform": 0.0343, "hunter": 0.045, "woodpecker_adv": 0.17,
     "li_note": 0.030, "li_accept": 0.285, "li_msg": 0.104, "op_li": 0.056,
     "hinge_survive": 0.481, "upwork_lo": 0.06, "upwork_hi": 0.20}

# per-touch p by route, for the N50 chart
routes = [
 ("Cold email, agency-measured reply 0.45% x 10% close", B["belkins"]*0.10, "Belkins 2025, n=7,530,489; close analyst"),
 ("Cold email, platform reply 3.43% x 10%", B["platform"]*0.10, "Instantly/Woodpecker 2026; any-reply incl. declines"),
 ("Cold email, v3 plan inputs 5.6% x 25%", B["op_li"]*0.25, "operator LinkedIn n=36; close analyst prior"),
 ("LinkedIn connection note 3.0% x 10%", B["li_note"]*0.10, "Expandi 2026, n=13.2M requests"),
 ("LinkedIn message to accepted connection 10.4% x 15%", B["li_msg"]*0.15, "Expandi 2026, n=6.73M messages"),
 ("Credentialed pitch to product-specialist agency (mid)", B["op_li"]*0.20, "operator LinkedIn 5.6% x 20% close, analyst"),
 ("Upwork proposal, established profile 6%", B["upwork_lo"], "GigRadar 2026, vendor claim"),
 ("Warm ask to a maintainer who merged you (mid)", B["hinge_survive"]*0.50*0.25, "Hinge 48.1% survive (n=523); reply, close analyst"),
 ("Warm ask, high", 0.60*0.30, "analyst"),
]
route_rows = [{"name": n, "p": p, "N50": N(0.5, p), "N90": N(0.9, p), "src": s} for n, p, s in routes]

# v4 lanes: (key, name, touches, (p_low, p_mid, p_high) or direct P triple, hours, provenance)
lanes = [
 ("A", "Medusa anchor: finish 5 open PRs, 12 docs/i18n PRs to the DX lead's domain, then one written ask", 2,
  (B["hinge_survive"]*0.40*0.15, B["hinge_survive"]*0.50*0.25, 0.60*0.30), None, 11,
  "warm-touch p: Hinge 48.1% x reply 40/50/60% x close 15/25/30% (reply and close are analyst priors)"),
 ("B", "Vendure partner track: dashboard translations, free partner registration, lead routing by contribution points", 1,
  None, (0.02, 0.08, 0.20), 15,
  "inbound lead arrival is unpublished; P(>=1 paid lead in 90 d) is an analyst prior, replaced by the partner portal's lead count"),
 ("C", "Credentialed subcontract pitch to product-specialist agencies listed in vendor directories", 120,
  (B["platform"]*0.10, B["op_li"]*0.20, B["li_msg"]*0.25), None, 16,
  "reply: platform 3.43% / operator 5.6% / LinkedIn-message 10.4%; close 10/20/25% analyst priors"),
 ("D", "Twenty certified-partner listing after one shipped self-implementation", 1,
  None, (0.02, 0.06, 0.15), 9,
  "vendor hand-matches briefs within 48 h to 26 partners; brief volume unpublished; analyst prior"),
 ("E", "Fix-then-contact: company-affiliated issue reporters with a first-person production complaint", 20,
  (B["platform"]*0.10, B["li_msg"]*0.20, B["woodpecker_adv"]*0.25), None, 14,
  "measured supply: 20 strong leads in 1,834 sampled open issues across 20 repos; reply 3.43/10.4/17%, close 10/20/25% analyst"),
 ("F", "v3 cold audit email, capped at 80 sends after warm lanes", 80,
  (B["belkins"]*0.10, B["platform"]*0.10, B["op_li"]*0.25), None, 7,
  "as v3 L1, at measured 2025-2026 reply rates"),
]
lane_rows = []
for key, name, n, pp, PP, hours, src in lanes:
    r = {"key": key, "name": name, "touches": n, "hours": hours, "src": src}
    for i, lvl in enumerate(("low", "mid", "high")):
        if pp: r[lvl] = {"p": pp[i], "P": P1(pp[i], n)}
        else:  r[lvl] = {"p": None, "P": PP[i]}
    lane_rows.append(r)
combined = {}
for lvl in ("low", "mid", "high"):
    q = 1.0
    for r in lane_rows: q *= (1 - r[lvl]["P"])
    combined[lvl] = 1 - q
# Expensify floor, shown separately (paid work, not a relationship)
exp = {"open": 30, "closed30d": 16, "proposals": 40,
       "low": P1(0.02, 40), "mid": P1(0.053, 40), "high": P1(0.08, 40),
       "src": "gh search 2026-09-24: 30 open, 16 closed since 2026-08-25; assignment odds 5.3% from v3 E16 (1 of 19 proposal authors), now competing with Expensify's own MelvinBot"}
v3 = {"p_mid": 0.0045, "sends_now": 30, "sends_plan": 160,
      "P_now": P1(0.0045, 30), "P_plan": P1(0.0045, 160),
      "P_plan_belkins": P1(B["belkins"]*0.10, 160), "P_plan_platform": P1(B["platform"]*0.10, 160)}
r3 = {str(n): 3/n for n in (8, 20, 40, 80, 120, 160)}
hours_total = sum(l[5] for l in lanes)
out = {"op": op, "B": B, "routes": route_rows, "lanes": lane_rows, "combined": combined,
       "expensify": exp, "v3": v3, "rule3": r3, "hours_total": hours_total}
json.dump(out, open("model.json", "w"), indent=1)
print(json.dumps({"combined": combined, "v3": v3, "hours": hours_total, "agencies": op["agencies_total"]}, indent=1))
for r in lane_rows: print(r["key"], [round(r[l]["P"],3) for l in ("low","mid","high")])
for r in route_rows: print(round(r["N50"],1), r["name"])
