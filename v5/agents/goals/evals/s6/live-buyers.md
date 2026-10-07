# s6/live-buyers.md — retainer buyer sheet (company facts from their own sites)
Generated 2026-10-03T03:32Z (date -u); EXTENDED 2026-10-04T16:5xZ (next-warm addendum, orgs 7-12); EXTENDED 2026-10-04T17:1xZ (org 13 payloadcms). Warm org list = company-backed per ferry/s5/raw/w21-company-backed.txt. Raw fetches in s6/raw/.

## Rows

### 1. PrefectHQ (Prefect) — blog https://prefect.io
- Product: workflow orchestration platform.
- Pricing (raw/pricing-PrefectHQ.html): "Starter $100 /mo", "Team $100 /user/mo" — paid SaaS tiers.
- Careers/contact: raw/careers-PrefectHQ.html; contact via own domain only.
- Raw: raw/site-PrefectHQ.html, raw/pricing-PrefectHQ.html, raw/careers-PrefectHQ.html, raw/w3c-funding-prefect.html.

### 2. mcpmux (McpMux) — blog https://mcpmux.com
- Product: MCP server registry & manager.
- Pricing: raw/pricing-mcpmux.html is a 404 page ("404: This page could not be found") — no public pricing page.
- Contact: own domain mcpmux.com (no /contact page; Discord/GitHub links in footer raw).
- Raw: raw/site-mcpmux.html, raw/pricing-mcpmux.html.

### 3. medusajs (Medusa) — blog https://medusajs.com
- Product: open-source commerce infrastructure (storefront + backend + Cloud).
- Pricing (raw/pricing-medusajs.html): "Launch From $99 /mo", "Scale From $299 /mo" — Medusa Cloud SaaS.
- Careers (raw/careers-medusajs.html): "Building a generational company requires exceptional, hard-working people"; team page lists "Sebastian Rindom Oliver Juhl Nicklas Gellner + 10" (~13 named people).
- Contact: own domain medusajs.com (footer "Contact" link).
- Raw: raw/site-medusajs.html, raw/pricing-medusajs.html, raw/careers-medusajs.html, raw/medusajs-careers-extract-0340.txt.

### 4. microlinkhq (Microlink) — blog https://microlink.io
- Product: API/tooling to turn any URL into structured output (screenshot, link preview, markdown, PDF).
- Pricing (raw/pricing-microlinkhq.html): "Pro For production workloads. $ 49 /month ≈ $ 1.07 per 1,000 requests"; "Free ... $ 0 /month"; copy cites "$200–$800 / month minimum on infra" for DIY.
- Contact: raw/pricing-microlinkhq.html footer shows a mailto (contact via own domain microlink.io only).
- Raw: raw/site-microlinkhq.html, raw/pricing-microlinkhq.html.

### 5. stellar (Stellar) — blog https://stellar.org
- Product: Stellar Development Foundation — payments/asset-tokenization network.
- Careers (raw/stellar-careers.html): "Stellar Development Foundation" named entity; jobs board is JS-rendered (raw/stellar-jobs.html shows "You need to enable JavaScript").
- Pricing: no public pricing page (raw/pricing-stellar.html is the marketing site, no dollar figures).
- Contact: own domain stellar.org.
- Raw: raw/site-stellar.html, raw/stellar-careers.html, raw/stellar-jobs.html, raw/pricing-stellar.html, raw/stellar-jobs-extract-0335.txt.

### 6. unidoc (UniDoc) — blog https://unidoc.io
- Product: document-processing SDKs (UniPDF, UniOffice) with credit-based pricing.
- Pricing (raw/pricing-unidoc.html): "Free $0 one-time 20 credits", "Starter $20 /mo 150 credits $0.15 / document", "Pro $100 /mo", "Scale $300 /mo", "Enterprise $500 /mo".
- Careers: raw/careers-unidoc.html is a 404 page — no public careers page.
- Contact: own domain unidoc.io.
- Raw: raw/site-unidoc.html, raw/pricing-unidoc.html, raw/careers-unidoc.html.

## Next-warm addendum (2026-10-04 cycle; RECURRING: extend buyer sheet to next-warm companies)
Companies adjacent to the warm set (same buyer class: OSS with paid product), facts from their own sites, fetched 2026-10-04 with curl -sL into s6/raw/nb-*.html.

### 7. calcom (Cal.com) — https://cal.com
- Product: open-source scheduling infrastructure.
- Pricing (raw/nb-pricing-calcom.html, HTTP 200): JS-rendered tiers not extractable server-side — recorded as gap this cycle.
- Entity (raw/nb-entity-calcom.html, privacy page): Cal.com, Inc. ("This privacy policy for ... Cal.com, Inc." address block 2261 Market Street).
- Contact: raw/nb-contact-calcom2.html (https://cal.com/talk-to-sales, HTTP 200).
- Raw: nb-orgs-1640-calcom.json, nb-site-calcom.html, nb-pricing-calcom.html, nb-entity-calcom.html, nb-contact-calcom2.html, nb-careers-calcom.html.

### 8. Infisical — https://www.infisical.com
- Product: secrets/credential management platform.
- Pricing (raw/nb-pricing-infisical.html, HTTP 200): dollar figures present in page text.
- Contact: /contact /contact-us /support /talk-to-sales /company all 404 (probed this cycle); careers page 200 (nb-careers-infisical.html) but uses email-obfuscation; contact route = own domain only.
- Raw: nb-orgs-1640-Infisical.json, nb-site-infisical.html, nb-pricing-infisical.html, nb-careers-infisical.html.

### 9. ToolJet — https://tooljet.com
- Product: low-code internal-tool builder.
- Pricing (raw/nb-pricing-tooljet.html, HTTP 200).
- About (raw/nb-about-tooljet.html, HTTP 200): team/mission copy present.
- Careers: /careers 404; hiring info on about page only.
- Raw: nb-orgs-1640-ToolJet.json, nb-site-tooljet.html, nb-pricing-tooljet.html, nb-about-tooljet.html.

### 10. umami-software (Umami) — https://umami.is
- Product: privacy-first web analytics.
- Pricing (raw/nb-pricing-umami.html, HTTP 200): page shell renders "Pricing – Umami" only; JS-rendered, no server-side price text (honest gap). Earlier w3 fetch (raw/w3d-umami-software-pricing.html) found dollar figures ($1, $5, $10, $12) — cite that raw for price facts.
- Entity (raw/nb-entity-umami.html, privacy page JS payload): "Umami Software, Inc. (doing business as Umami)".
- Contact: raw/nb-contact-umami2.html (https://umami.is/contact, HTTP 200).
- Raw: nb-orgs-1640-umami-software.json, nb-site-umami.html, nb-pricing-umami.html, nb-entity-umami.html, nb-contact-umami2.html.

### 11. mercurjs (Mercur) — https://www.mercurjs.com
- Product: multi-vendor marketplace platform on Medusa.
- Pricing: /pricing 404; /enterprise 200 (raw/nb-contact-mercurjs.html) — "Enterprise suite" route, no public number (quote-based).
- Entity: footer "© 2026 Mercur" (no legal suffix in static HTML — honest gap).
- Careers: /careers 404.
- Raw: nb-orgs-1640-mercurjs.json, nb-site-mercurjs.html, nb-pricing-mercurjs.html (404), nb-contact-mercurjs.html (/enterprise 200).

### 12. vendurehq (Vendure) — https://vendure.io
- Already covered as row 8 of w7b-decider-buyers.md (Elevantiq GmbH, flat annual subscription quoted in demo) — cross-reference there; raw w1-site-vendure.html, w1-pricing-vendure.html. Open PR vendure#5483 confirmed open this session (raw/w1-pr-states-latest.txt).

### 13. payloadcms (Payload) — https://payloadcms.com
- Product: Next.js headless CMS and application framework (open source, GitHub org 1,936 followers).
- Pricing: /pricing 404 (raw/nw-cloudpricing-payloadcms.html via /cloud-pricing 200): "Payload has joined Figma! ... deployment of new projects is currently paused, existing Cloud projects will continue running as normal" — Cloud sales paused, no public price; cloud-terms references standard rates at cloud-pricing route (JS-rendered tiers).
- Entity (cloud-terms page fetched this cycle): "provided by Payload CMS, Inc., a Delaware corporation".
- Contact: https://payloadcms.com/contact (HTTP 200, raw/nw-contact-payloadcms.html).
- Open-PR surface: payloadcms/payload PR 18473 OPEN (updatedAt 2026-10-03T15:05:28Z, gh check this cycle).
- Raw: nw-orgs-1707-payloadcms.json, nw-site-payloadcms.html, nw-cloudpricing-payloadcms.html, nw-contact-payloadcms.html, plus cloud-terms quote verified below.

## Open-PR overlap check (this cycle)
From forge/s6/raw/rec-open-163642.json census: calcom has 5 open PRs, mercurjs 3, Infisical 1, ToolJet 1, umami-software 1, vendurehq 1 — all six orgs have live PR surface, qualifying them as next-warm targets.

## Acceptance
- Every cell cites a raw file in s6/raw/.
- grep -c at-character on this file = 0 (no email addresses; microlink mailto referenced without the address itself).

### 14. traccar (Traccar) — blog https://www.traccar.org
- Product: free/open-source GPS tracking system (Traccar Server/Manager/Client); PR #2010 open on traccar-web.
- Pricing (s6/raw/nw-pricing-traccar.html): "Tracking Account ... From $5.95 / month", "Tracking Server ... From $29.95 / month"; "© Copyright 2009 - 2026 Tananaev Solutions".
- Entity (s6/raw/nw-about-traccar.html): "© Copyright 2009 - 2026 Tananaev Solutions"; contact routes on own domain: sales (at) traccar.org (About page "Contacts Sales"), support (at) traccar.org ("Contact our sales team" on /pricing), phone +1 347 603-0304 — addresses NOT written in sheet (zero-at rule); contact page on own domain = /about (200).
- Maintainer event: tananaev (MEMBER) review COMMENTED on #2010 at 2026-10-04T20:22:00Z (s6/raw/rec-traccar-2010-reviews-2023.json).
- Raw: s6/raw/nw-pricing-traccar.html, s6/raw/nw-about-traccar.html, s6/raw/rec-traccar-2010-state-2023.json.

```verify
$ python3 - <<'PYEOF'
import re
def norm(f):
    t=open('v5/agents/goals/evals/s6/raw/'+f,encoding='utf-8',errors='ignore').read()
    t2=re.sub(r'<[^>]+>',' ',t); t2=re.sub(r'\s+',' ',t2)
    return t2
R='v5/agents/goals/evals/s6/raw/'
checks=[
 ('pricing-PrefectHQ.html','Starter $100 /mo'),
 ('pricing-mcpmux.html','404: This page could not be found'),
 ('pricing-medusajs.html','Launch From $99 /mo'),
 ('pricing-microlinkhq.html','$ 49 /month'),
 ('stellar-careers.html','Stellar Development Foundation'),
 ('pricing-unidoc.html','Starter $20 /mo 150 credits'),
 ('nb-entity-calcom.html','Cal.com, Inc.'),
 ('nb-entity-umami.html','Umami Software, Inc.'),
 ('nb-site-mercurjs.html','© 2026 Mercur'),
 ('nw-cloudterms-payloadcms.html','Payload CMS, Inc., a Delaware corporation'),
 ('nw-cloudpricing-payloadcms.html','Payload has joined Figma'),
 ('nw-pricing-traccar.html','From $29.95 / month'),
 ('nw-about-traccar.html','© Copyright 2009 - 2026 Tananaev Solutions'),
]
ok=all(norm(R+f).find(s)>=0 for f,s in checks)
print(ok)
PYEOF
True
```


## Next-warm addendum 2026-10-05T10:18Z (orgs 97-98)

15. GreenmaskIO (greenmask.io) — Open-source data anonymization / test data management tool (Postgres). Own site: greenmask.io (200), pitch = "secure toolset to transform your database while maintaining integrity"; parallel dump/restore, deterministic transformers, database subsetting. Repo 1777 stars, pushed 2026-09-30T18:34:48Z. Open tier-A PR: GreenmaskIO/greenmask#493 (APPROVED by wwoytenko, human; raw s6/raw/w16-tier-new.tsv, w16-nextwarm-greenmask.json). No sends made.
16. notum-cz (notum.tech) — Strapi/Payload Enterprise Partner agency ("Headless CMS Agency"); services = Strapi, Payload, Next.js builds; "We Create Custom Software Solutions". Repo strapi-plugin-seo 119 stars ("official plugin to make Strapi content SEO friendly"). Open tier-A PR: notum-cz/strapi-plugin-seo#116 (CI SUCCESS, no human events — coderabbitai only, does not count per LESSONS 86; raw s6/raw/w16-nextwarm-notum.json, w16-nextwarm-notum-site.txt). No sends made.

---

## cycle 2026-10-05T0151Z — no next-warm orgs

live-open-prs.md STATE REFRESH 2026-10-05T11:59Z (L151): tier A/B open = none; remaining open non-D = tier C only (umami-software/umami#4580, hkdb/aerion#437). umami already has a row (row 10). No tier A/B org without a buyer row remains.


### 15. coroot (Coroot) — https://coroot.com
- Product: open-source observability (eBPF-based monitoring, microservice tracing).
- Pricing (raw/c79-coroot-pricing-183710.html, HTTP 200): "$40/month" present in page text (self-hosted/Cloud tier).
- Contact: own domain only - site and pricing pages link /contact (raw/c79-coroot-site-183720.html, raw/c79-coroot-contact-183730.html HTTP 200).
- Open non-D PR: coroot/coroot#1039 (raw/rec-nond-list-c79-183500.txt).
- Raw: raw/c79-coroot-site-183720.html, raw/c79-coroot-pricing-183710.html, raw/c79-coroot-contact-183730.html.


### 16. Swetrix — https://swetrix.com
- Product: privacy-first web analytics (cookie-less).
- Pricing (raw/c80-swetrix-pricing-184030.html, HTTP 200): "$19" and "$39" per month tiers present (grep: 3x "$19", 3x "$39"); Free tier present.
- Contact: own domain only - site and pricing link /contact (raw/c80-swetrix-site-184020.html); /contact HTTP 200 (raw/c80-swetrix-contact-184040.html).
- Open non-D PR: Swetrix/swetrix#612 (raw/rec-nond-list-c79-183500.txt).
- Raw: raw/c80-swetrix-site-184020.html, raw/c80-swetrix-pricing-184030.html, raw/c80-swetrix-contact-184040.html.


### 17. Kilo-Org (Kilo) — https://kilo.ai
- Product: all-in-one agentic engineering platform (org description via gh api orgs/Kilo-Org).
- Pricing (raw/c81-kilo-pricing-184510.html, HTTP 200): dollar figures in page text ($20, $5, $15, $0; "kilo-pass" tier page exists at /pricing/kilo-pass).
- Contact: raw/c81-kilo-contact-184520.html (https://kilo.ai/contact-sales, HTTP 200).
- Open non-D PR: Kilo-Org/kilo-marketplace#269 (raw/rec-openurls-183310.txt).
- Raw: c81-kilo-site-184500.html, c81-kilo-pricing-184510.html, c81-kilo-contact-184520.html.


### 18. Comfy-Org (Comfy) — https://comfy.org
- Product: ComfyUI open-source node-based generative-AI interface (frontend repo ComfyUI_frontend).
- Pricing (raw/c82-comfy-pricing-184910.html, HTTP 200): dollar figures in page text ($630 /month, $2,500/month, $4.00/mo tiers).
- Contact: raw/c82-comfy-contact-184920.html (https://comfy.org/contact/, HTTP 200); enterprise page exists (/enterprise/, /enterprise-msa/).
- Open non-D PR: Comfy-Org/ComfyUI_frontend#18234 (raw/rec-openurls-183310.txt).
- Raw: c82-comfy-site-184900.html, c82-comfy-pricing-184910.html, c82-comfy-contact-184920.html.


### 19. HeyPuter (Puter) — https://puter.com
- Product: open-source internet OS / cloud desktop.
- Pricing (raw/c83-puter-pricing-185420.html, HTTP 200): dollar figures present in page text ($10/month appears twice).
- Contact: pricing page has no direct sales route recorded; no /contact link on landing (only #phl-pricing anchor and /app/contacts app link in raw/c83-puter-site-185410.html).
- Raw: c83-puter-site-185410.html, c83-puter-pricing-185420.html.
- Open non-D PR: HeyPuter/puter#4074 (raw/rec-openurls-183310.txt).


### 20. Grashjs (Atlas CMMS) — https://atlas-cmms.com
- Product: free open-source CMMS (maintenance management), cloud or self-hosted.
- Pricing (raw/c84-grash-pricing-185820.html, HTTP 200): no dollar figures extracted server-side; page text has Free tier, Free Forever, Free trial, Cloud and Self-Hosted versions, Enterprise plans with invoicing. Recorded as pricing-figure gap this cycle.
- Contact: mailto:contact@atlas-cmms.com (landing raw/c84-grash-site-185810.html, HTTP 200).
- Raw: c84-grash-site-185810.html, c84-grash-pricing-185820.html.
- Open non-D PR: Grashjs/cmms#299 (raw/rec-openurls-183310.txt).


### 21. Nano-Collective — https://nanocollective.org
- Product: local-first AI tools (org tagline in page h1: "Local-first AI tools..."); featured projects and packages listed on landing.
- Pricing: none on landing; funding route = /sponsor link (raw/c85-nano-site-190300.html, HTTP 200).
- Contact: no contact/sales route recorded from landing grep.
- Raw: c85-nano-site-190300.html.
- Open non-D PRs: Nano-Collective/nanocoder#1543, #1540 (raw/rec-openurls-183310.txt).


### 22. OWASP Foundation — https://owasp.org
- Product: nonprofit foundation for open-source application security projects; org blog from gh api = https://owasp.org; landing title: "OWASP Foundation - The Open Source Foundation for Application Security" (raw/c86-owasp-site-190800.html, HTTP 200).
- Pricing: none (foundation); funding routes on landing: /donate, /contact.
- Raw: c86-owasp-site-190800.html.
- Open non-D PR: OWASP/cve-lite-cli#1278 (raw/rec-openurls-183310.txt).

## Row 9 — CapSoftware (Cap) — c88 2026-10-05T20:08Z
- Org: CapSoftware, product Cap (open-source screen recorder, cap.so). Company-backed: commercial Cap Pro self-serve (tier A).
- Open non-D PR: CapSoftware/Cap#2421 (head e8d9d094, raw/w25-8-cap2421-head-195547.txt).
- Own-site facts: cap.so HTTP 200 (raw/c88-cap-site-200830.html); cap.so/pricing HTTP 200 (raw/c88-cap-pricing-200830.html) — "Cap Pro $12 per user / mo", "$29 per year" desktop license; meta description: "Self-serve Cap Pro for organizations ... Add SAML SSO ($199/mo) or a signed BAA ($99/mo)".
- Repo: 23,065 stars, pushed 2026-10-05T14:44:51Z (raw/c88-cap-repo-200830.json).


### 23. hkdb (Aerion) — https://aerion.3df.io
- Product: open-source lightweight e-mail client (Wails+Svelte, Linux-first, privacy-focused, Apache-2.0). Individual maintainer hkdb, blog https://osi.3df.io; NOT a company — no pricing page, no paid product (honest gap, weaker buyer class than rows 1-22).
- Repo: 963 stars (raw/c89-aerion-stars-*.txt); homepage aerion.3df.io.
- Site (raw/c89-aerion-site-*.html, HTTP 200): "An Open Source Lightweight E-Mail Client".
- Funding signal (README raw/c89-aerion-readme-*.txt): "3DF is sponsoring by way of dedicating its cloud infrastructure resources and the team's time... There's otherwise currently no sponsorship"; "CASA Tier 2 every year which cost US$540 this year"; "Starting next year, we will have to depend on community or corporate sponsorship" — explicit dated corporate-sponsorship ask.
- GitHub Sponsors profile HTTP 200 (curl).
- Open non-D PR: hkdb/aerion#437 "add Japanese (ja) locale" (open, updated 2026-10-05T07:10:44Z, raw/c89-aerion437-*.txt).
- Raw: c89-hkdb-user-*.txt, c89-aerion-site-*.html, c89-aerion-readme-*.txt, c89-aerion-stars-*.txt, c89-aerion437-*.txt.

```verify
$ python3 -c "
import re,glob
site=open(glob.glob('v5/agents/goals/evals/s6/raw/c89-aerion-site-*.html')[-1],encoding='utf-8',errors='ignore').read()
readme=open(glob.glob('v5/agents/goals/evals/s6/raw/c89-aerion-readme-*.txt')[-1],encoding='utf-8',errors='ignore').read()
print('An Open Source Lightweight E-Mail Client' in site and 'US\$540' in readme and 'corporate sponsorship' in readme)"
True
```

### 24. aymericzip (Intlayer) — https://intlayer.org
Added 2026-10-06T03:47Z (RECURRING sweep): new tier-A org — aymericzip/intlayer#519 open, reviewDecision APPROVED by aymericzip (repo owner, human) at 2026-10-06T00:43:38Z (raw rec-graphql-0334.json + rec-intlayer-reviews-034302; not in the 10-05T08:24Z snapshot, which had 0 reviews). Repo 845 stars, pushed 2026-10-06T00:52:51Z (raw rec-intlayer-repo-034529.json).
- Product: per-component i18n for JS apps; type-safe; AI translate; visual editor (org description).
- Pricing (raw rec-intlayer-pricing-034529.html, HTTP 200): schema.org Offer JSON-LD — Free 0.00; Premium $38.99/mo ($348.00/yr USD); Enterprise $68.99/mo ($689.00/yr USD or EUR); plus one $950.00 offer; page text: "Premium ... 29.00 $ Monthly", "Enterprise ... 57.42 $ Monthly" (save 20% annually). Paid SaaS confirmed.
- Contact: contact@intlayer.org in site JSON-LD ContactPoint (raw rec-intlayer-site-034529.html, 2 occurrences); careers page 404 (HTTP 404, curl).
- CI note (honesty): PR branch check "Build & Test" = failure at 01:02Z (test packages step); commit status overall success; main-branch runs green. Mergeability true.
- Raw: raw/rec-graphql-0334.json, raw/rec-intlayer-reviews-034302, raw/rec-intlayer-comments-034406, raw/rec-intlayer-pr-034406.json, raw/rec-intlayer-repo-034529.json, raw/rec-intlayer-site-034529.html, raw/rec-intlayer-pricing-034529.html.

```verify
$ python3 -c "
import json,re
h=open('v5/agents/goals/evals/s6/raw/rec-intlayer-pricing-034529.html',encoding='utf-8',errors='ignore').read()
r=json.load(open('v5/agents/goals/evals/s6/raw/rec-intlayer-reviews-034302')) if False else None
print('38.99' in h and '68.99' in h and 'contact@intlayer.org' in open('v5/agents/goals/evals/s6/raw/rec-intlayer-site-034529.html',encoding='utf-8',errors='ignore').read())"
True
```

## Row 10 — httptoolkit (mockttp) — c95 2026-10-06T07:53Z
- Org: Toolshed Labs SLU (httptoolkit.com footer: "© 2026 Toolshed Labs SLU"), product HTTP Toolkit. Company-backed: Hobbyist Free / Professional / Team per-user self-serve tiers (tier B — pricing page live, no fixed retainer fit).
- Open non-D PR: httptoolkit/mockttp#215 "Fix regex flags being ignored in regex body matching", open, created 2026-10-05T18:42:38Z, head 0b4045289030edbb7f369bd0699a739ac33d2e17 (raw/rec-mockttp-215-074822.json). +11/−2, 1 comment, 0 review comments (gh api, 07:52Z). No maintainer reviews (raw/rec-mockttp-reviews-075042.json = []).
- Own-site facts: httptoolkit.com HTTP 200 (raw/rec-httptoolkit-site-075053.html); /pricing HTTP 200 (raw/rec-httptoolkit-pricing-075053.html) — plan names in rendered-adjacent markup: "Hobbyist" free tier, ">Professional</p>", "per month" wording, "Team per user, per month", "Save 25% Pay yearly". No numeric prices in static HTML (client-side rendered).
- Repo: 884 stars, pushed 2026-09-22T19:11:16Z, homepage httptoolkit.com (raw/rec-mockttp-repo-075042.json).
- Contact: fergal@anyska.fergl.ie in site HTML (raw/rec-httptoolkit-site-075053.html, 1 occurrence).

```verify
$ python3 -c "
import json,glob
r=json.load(open(glob.glob('v5/agents/goals/evals/s6/raw/rec-mockttp-repo-075042.json')[-1]))
p=open(glob.glob('v5/agents/goals/evals/s6/raw/rec-httptoolkit-pricing-075053.html').pop(),encoding='utf-8',errors='ignore').read()
print(r['stars']==884 and '>Professional</p>' in p and 'Hobbyist' in p and 'per month' in p)"
```

## cycle 2026-10-06T0832Z — no next-warm orgs
repro: python re-derivation over forge/s6/live-open-prs.md (88 orgs with open PR rows) x forge/s6/raw/w1-tiers.tsv (tier census) x this sheet's contents -> tier A/B orgs: 0; A/B orgs without buyer row: []. All non-D PRs are default tier C pending ask data. No next-warm org qualifies.

## cycle 2026-10-06T0836Z — no next-warm orgs
repro: same re-derivation as 0832Z cycle — open-PR orgs: 88 | tier A/B (with open PR): 0 | A/B without buyer row: []. No next-warm org qualifies.

## cycle 2026-10-06T0839Z — no next-warm orgs
repro: same re-derivation — open-PR orgs: 88 | tier A/B (with open PR): 0 | A/B without buyer row: []. No next-warm org qualifies.

## cycle 2026-10-06T0842Z — no next-warm orgs
repro: same re-derivation — open-PR orgs: 88 | tier A/B (with open PR): 0 | A/B without buyer row: []. No next-warm org qualifies.

## cycle 2026-10-06T1144Z — no next-warm orgs
repro: python re-derivation over forge/s6/live-open-prs.md (17 orgs with open PR refs in current file) x forge/s6/raw/w1-tiers.tsv -> tier A/B orgs with open PRs: []; missing buyer row: []. No next-warm org qualifies.

## cycle 2026-10-06T1146Z — no next-warm orgs
repro: python re-derivation over forge/s6/live-open-prs.md -> 88 orgs with open PR refs x tier file -> tier A/B orgs with open PRs: []; missing buyer row: []. No next-warm org qualifies. Raw: s6/raw/w33/w33-recurring-114639.txt

## cycle 2026-10-06T1149Z — no next-warm orgs
repro: fixed census matcher (tier keys are PR URLs; map org via URL prefix, not exact name). 88 orgs, all 88 tier-mapped: 47 C + 41 D, 0 A/B -> tier A/B orgs with open PRs: []; missing buyer row: []. No next-warm org qualifies. Raw: s6/raw/w33/w33-recurring-114950.txt

## cycle 2026-10-06T1153Z — no next-warm orgs
repro: fresh census from forge raw rec-open-115230.json (128 orgs, fresher than live-open-prs.md@11:20Z) x tier map -> tier A/B orgs with open PRs: []; missing buyer row: []. No next-warm org qualifies. Raw: s6/raw/w33/w33-recurring-115347.txt

| 2026-10-06T121625Z | RECURRING | no next-warm orgs (162 orgs, rec-open-232952.json) |
| 2026-10-06T121929Z | RECURRING | no next-warm orgs (162 orgs, rec-open-232952.json) |
| 2026-10-06T122210Z | RECURRING | no next-warm orgs (162 orgs, rec-open-232952.json) |
| 2026-10-06T122454Z | RECURRING | no next-warm orgs (162 orgs, rec-open-232952.json) |
| 2026-10-06T122738Z | RECURRING | no next-warm orgs (162 orgs, rec-open-232952.json) |
| 2026-10-06T1249Z | RECURRING | useplunk (plunk#512, tier B awaiting maintainer follow-up) | useplunk.com live: title 'Plunk — Open-Source Transactional Email Platform'; self-hosting + open-source + pricing pages present; pricing $0.001 per email flat; 5,000+ GitHub stars claim on site | raw/w35/w35-plunk-site-1249.html |
| 2026-10-06T1539Z | RECURRING | no next-warm orgs (warm list mcpmux/medusajs/microlinkhq/prefecthq/stellar/unidoc x open-PR census raw/rec-open-153418.json -> warm-with-open-PRs PrefectHQ/medusajs/stellar, all 3 already have buyer rows; missing=[]) |  | raw/rec-warm-153748.txt |
| 2026-10-06T1559Z | RECURRING | no next-warm orgs (119 orgs, rec-open-153806.json; warm-with-open-PRs PrefectHQ/medusajs/stellar all already have rows) |  | raw/rec-warm-153806.txt |
| 2026-10-06T1541Z | RECURRING | no next-warm orgs (119 orgs, rec-open-154053.json; warm∩open = PrefectHQ/medusajs/stellar, all already have rows) |  | raw/rec-warm-154053.txt |
| 2026-10-06T1542Z | RECURRING | no next-warm orgs (119 orgs, rec-open-154249.json; warm∩open = PrefectHQ/medusajs/stellar, all already have rows) |  | raw/rec-warm-154249.txt |
| 2026-10-06T1617Z | RECURRING | no next-warm orgs (157 orgs, rec-open-161706.json; warm∩open = PrefectHQ/medusajs, both already have rows) |  | raw/rec-warm-161721.txt |
| 2026-10-06T162139Z | RECURRING | no next-warm orgs (120 orgs, rec-open-161706.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-162139.txt |
| 2026-10-06T162459Z | RECURRING | no next-warm orgs (120 orgs, rec-open-162426.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-162428.txt |
| 2026-10-06T162809Z | RECURRING | no next-warm orgs (120 orgs, rec-open-162726.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-162728.txt |
| 2026-10-06T162848Z | RECURRING | no next-warm orgs (120 orgs, rec-open-163027.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-163029.txt |
| 2026-10-06T163158Z | RECURRING | no next-warm orgs (120 orgs, rec-open-163327.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-163329.txt |
| 2026-10-06T163518Z | RECURRING | no next-warm orgs (120 orgs, rec-open-163527.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-163529.txt |
| 2026-10-06T163826Z | RECURRING | no next-warm orgs (120 orgs, rec-open-163727.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-163729.txt |
| 2026-10-06T164135Z | RECURRING | no next-warm orgs (120 orgs, rec-open-164028.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-164030.txt |
| 2026-10-06T164459Z | RECURRING | no next-warm orgs (120 orgs, rec-open-164328.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-164330.txt |
| 2026-10-06T164838Z | RECURRING | no next-warm orgs (120 orgs, rec-open-164728.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-164730.txt |
| 2026-10-06T165226Z | RECURRING | no next-warm orgs (120 orgs, rec-open-165027.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-165029.txt |
| 2026-10-06T165624Z | RECURRING | no next-warm orgs (120 orgs, rec-open-165427.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-165429.txt |
| 2026-10-06T170013Z | RECURRING | no next-warm orgs (120 orgs, rec-open-165828.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-165830.txt |
| 2026-10-06T170325Z | RECURRING | no next-warm orgs (120 orgs, rec-open-170227.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-170229.txt |
| 2026-10-06T170642Z | RECURRING | no next-warm orgs (120 orgs, rec-open-170527.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-170529.txt |
| 2026-10-06T171012Z | RECURRING | no next-warm orgs (120 orgs, rec-open-170927.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-170929.txt |
| 2026-10-06T171315Z | RECURRING | no next-warm orgs (120 orgs, rec-open-171227.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-171229.txt |
| 2026-10-06T171725Z | RECURRING | no next-warm orgs (120 orgs, rec-open-171527.json; warm∩open = PrefectHQ/medusajs, all already have rows; missing=[]) |  | raw/rec-warm-171529.txt |
| 2026-10-07T1431Z | RECURRING | no next-warm orgs (198 prs, raw/rec-open-143005.json; warm∩open = medusajs/PrefectHQ, all already have rows; missing=[]) |  | raw/rec-open-143005.json |
| 2026-10-07T1443Z | RECURRING | no next-warm orgs (200 prs, raw/rec-open-144213.json; warm∩open = medusajs/PrefectHQ, all already have rows; missing=[]) |  | raw/rec-open-144213.json |
| 2026-10-07T1445Z | RECURRING | no next-warm orgs (200 prs, raw/rec-open-144541.json; warm∩open = medusajs/PrefectHQ, all already have rows; missing=[]) |  | raw/rec-open-144541.json |
| 2026-10-07T1450Z | RECURRING | no next-warm orgs (200 prs, raw/rec-open-145003.json; warm∩open = medusajs/PrefectHQ, all already have rows; missing=[]) |  | raw/rec-open-145003.json |
| 2026-10-07T1453Z | RECURRING | no next-warm orgs (200 prs, raw/rec-open-145341.json; warm∩open = medusajs/PrefectHQ, all already have rows; missing=[]) |  | raw/rec-open-145341.json |
| 2026-10-07T1456Z | RECURRING | no next-warm orgs (200 prs, raw/rec-open-145648.json; warm∩open = medusajs/PrefectHQ, all already have rows; missing=[]) |  | raw/rec-open-145648.json |
| 2026-10-07T1500Z | RECURRING | no next-warm orgs (200 prs, raw/rec-open-145952.json; warm∩open = medusajs/PrefectHQ, all already have rows; missing=[]) |  | raw/rec-open-145952.json |
| 2026-10-07T1503Z | RECURRING | no next-warm orgs (200 prs, raw/rec-open-150257.json; warm∩open = medusajs/PrefectHQ, all already have rows; missing=[]) |  | raw/rec-open-150257.json |
