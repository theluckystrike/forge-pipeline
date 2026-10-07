# MCP-Servers Monetization/Distribution Sprint — Orchestrator Intel Brief

STATUS: complete (evidence-backed, 2026-10-07)
Estate: mcp.zovo.one storefront + Worker billing, GitHub monorepo theluckystrike/mcp-servers, /Users/mike/mcp-servers

## 1. Platform analysis file — COULD NOT READ
`/Users/mike/Desktop/platform-analysis-2026/index.html` does not exist from this terminal's view:
- read_file: "File not found"
- `head -c 2000` on the path: "No such file or directory"
- `ls /Users/mike/Desktop/`: "Operation not permitted" (Desktop is TCC-protected for this shell)
- mdfind for "platform-analysis-2026": no results (spotlight may also be blocked).
Its findings survive in summary form inside STRATEGY-S128.md: platform-analysis-2026
scored the platform 91/100, MCP capture ratio 1.17 vs Chrome 0.033, zero publish
friction, NO protocol billing rail → monetize via hosted Pro tiers + marketplace
checkout rails (mcp-marketplace.io handles Stripe + license keys). Treat that as the
canonical platform thesis; re-reading the raw HTML requires human Desktop access.

## 2. Current KPIs (data/kpi.json, 2026-09-29)
- Registry entries at latest version: **56 / 149** (dashboard "Biggest wins" cites an
  older 97–100 figure; use 56 as current).
- Registry findable share: 50 / 60 %.
- Distribution surfaces live: **17 / 74** (distribution.json 2026-09-28: 74 surfaces
  tracked, 144 total submissions; 12 published + 3 live PRs + 7 submitted awaiting
  review + 6 PRs open; 5 blocked, 3 dead, several human-gated).
- Google impressions storefront (28d): **0 / 1** — zero across 99+ days; single most
  important organic number.
- Named by blind assistant: **0 / 18** buyer questions (R7: 1/18 organic retrieval;
  whitespace queries q6 quotes, q10 spreadsheet-from-chat, q14 delivery schedule,
  q16 no-install usage, q17 SMB accounting roundup, q18 paid MCP discovery).
- Recommendation citation share: 2 / 18.
- Googlebot 2/237 URLs; ClaudeBot 34/237; sitemap cut to 96 (from 237) on 09-07.
- Traffic: 6,181 human storefront requests/7d (met); GitHub visitors 71/200; npm
  weekly downloads **0** (token expired, human-gated).
- Activation: 135 anonymous tokens (met), 1,005 hosted tenants with data (met),
  first-prompt tool reach 98/95 (met).
- Monetization: 97 human checkout sessions, **3 paid** ($38 via /pricing founding
  tier — REAL humans, confirmed R7 fact-check 2026-09-29), 894 lic:* keys minted in
  REMOTE_DATA (the "0 minted" KPI is stale/wrong), 2 Pro tenants (target 20),
  1 upgrade click/7d. Click data heavily contaminated by automation: 77.9% of
  upgrade clicks carry a src no live page emits (conversion_r1). **The funnel works;
  the constraint is traffic, not conversion.**

## 3. What's been done (strategy docs)
- **STRATEGY-42** (09-18): organic disruption — 42 per-server landing pages at
  /mcp/<slug>/, content-derived ETag worker fix, Glama badge re-probe, blind R7,
  off-listing channel placement. Thesis: "listings produce listings, not ranks";
  winning surfaces are vendor blogs, Reddit, YouTube, per-server pages ranking.
- **STRATEGY-S128** (09-21): platform thesis (no billing rail → hosted Pro +
  marketplace); batches: 3 new servers (price-tracker, time-tracker,
  backlink-checker), directory re-probes, llms.txt/SEO organic batch, checkout
  leak diagnosis, traffic re-measure. mcp-marketplace.io creator account created,
  **email verify HUMAN-GATED**.
- **SPEC-S129**: checkout conversion sprint — Stripe deep-dive, hostile-buyer audit
  of /buy/* pages, fix ~15 unpaid sessions/day leak, click→paid ≥2% goal.
- **STRATEGY-S131** (09-23): "listings saturated; retrieval is not." Levers:
  (1) registry name-variant multiplication (purchase-requisition pattern = 4 tokens
  per codebase, from data/token_demand_r1.json), (2) whitespace content pages
  answering the 6 R7 queries, (3) surface sweep re-probes. Deploys require
  node --test green; registry publishes require uploaded mcpb asset.
- **S142_DIRECTORY_WAVE2_RESULT** (COMPLETE): PR #109 to
  Sagargupta16/awesome-mcp-servers (OPEN, mergeable after rebase) adding pdf-merger,
  backlink-checker, pomodoro-timer (+invoice via dedicated repo). Skipped dead-intake
  lists; jaw9c/awesome-remote-mcp-servers skipped (we are local npm, not remote).

## 4. Key blocker knowledge
- awesome-mcp-servers (punkpeye) rejects multi-server PRs (PR 13473 closed); one
  server per PR, but repo backlog ~2,220 open PRs — low merge odds.
- Glama: only 1 of 13 repos indexed (mcp-statement-of-account); 12 probe 404; one
  badge line per README only when indexed (SVG >4000B).
- npm publish token expired — human-gated.
- mcp-marketplace.io email verification — human-gated.
- No MCP payment primitive: SEP-2007 (payment/x402) closed dormant 2026-06-24,
  revivable; MCP spec 2026-07-28 has zero payment fields; only merged payment-relevant
  feature is URL-mode elicitation (SEP-1036). x402 v2.0 (@x402/mcp 2.25.0) is the only
  live no-account rail but: no mainstream client settles 402, requires self-custody
  wallet, market median $0.01/call vs our $19 lifetime — verdict: NOT viable now
  (agent_payments_r1).
- Checkout probe protocol: Chrome UA + header `x-mcp-probe: 1` (else 303 scripted-ua
  guard and click-counter contamination).

## 5. Dashboard conventions (DASHBOARD.html, 45.7KB)
- Single static file, `:root` CSS vars, light+dark via prefers-color-scheme, max-width
  1180px `.wrap`, 13px system font, tabular-nums.
- Header h1 + meta line; sections: Blind test score (latest run), Distribution
  surfaces live, Hosted endpoints, **KPI table (data/kpi.json)**, Biggest wins,
  Next actions, Session log (scroll-wrap table: at | note).
- Pills: .pill-ok/-bad/-pending/-measured with status colors; .num right-aligned mono
  for numbers; h2 uppercase muted with border.
- Update pattern: KPI table rows generated from kpi.json cats/values; "Next actions"
  lists unmet KPIs with why-text; Session log gets a new timestamped row per round.

## 6. Recommended sprint priorities (evidence-ranked)
1. **Traffic, not conversion** — funnel proven (3 real paid). Whitespace content
   pages (S131 T2) for q6/q10/q14/q16/q17/q18 + per-server /mcp/ pages are the
   highest-leverage organic assets; resubmit sitemap+IndexNow after deploy.
2. **Registry entry completion** 56→149 (variant-name multiplication from
   token_demand_r1.json) — proven 4-tokens-per-codebase pattern.
3. **Surface flips** — 7 new submissions entered review ~09-28 (2-week review
   window ≈ mid-Oct: recheck now); re-probe pending/blocked surfaces.
4. **Fix the KPI instrumentation** — license-keys-minted KPI reads 0 but 894 exist
   in REMOTE_DATA; upgrade-click counter contaminated by automation. Correct data
   before judging new sprints.
5. **Pro tenants 2/20** — push /pricing founding tier; it's the only proven
   revenue path (both real payments came from it).
Human-gated items to hand to operator: npm token refresh, mcp-marketplace.io email
verify, glama indexing escalation.

budget: 7 of 30 used, next: none — brief is complete and shippable.

## 7. Reconciliation with 2026-10-07 session (bf177289)
The KPI block above is the 09-29 kpi.json snapshot — today's verified figures supersede:
- Checkout: 46/54 servers live Stripe (bundle $39 / individual $19); zero 503s; counter guard verified exact-once.
- Organic: GSC 28d mcp.zovo.one 0 clicks / 22 imps / 2 indexed pages; sitemap 237 URLs (cut-to-96 happened 09-07, since restored); IndexNow re-pinged 200 with corrected key db6dbf5c....
- Dist R30: ExMapo #24 + Albertchamberlain #75 OPEN+MERGEABLE (item 6.3 surface re-probe remains valid).
- Priorities 6.1-6.5 stand; today's adds: user 2-command unblock (mcp-publisher login github, npm login) covers 6's npm-token human gate.
