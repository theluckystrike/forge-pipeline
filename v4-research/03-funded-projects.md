# 03. Funded OSS projects that pay non-core contributors (fetched 2026-09-24)

All figures below were fetched on 2026-09-24. Open Collective (OC) figures come from Wayback Machine snapshots of opencollective.com pages (snapshot date given per row), because every direct route to opencollective.com and api.opencollective.com was blocked (see Access log). "Latest 10 expenses" means the 10 most recent expenses embedded in the archived expenses page; a full 12-month expense ledger was not obtainable, so 12-month totals are marked unverified.

## 0. Bottom line (ranked for a non-core contributor who wants money soon)

| Rank | Project | Money on hand (OC balance, snapshot) | Pays non-core? (published) | Amount | Openness to a new contributor | Time to first payment |
|---|---|---|---|---|---|---|
| 1 | ESLint | $111,952.48 (2026-09-23); est. annual budget $140,196.59 | Yes, standing policy, no application | "at least $100 to every outside contributor who has made a non-trivial contribution"; pool = "10% of our monthly income" (income "$9,220.15 each month" on 2026-09-24) | Highest: TSC emails you; measured June 2025 pool: 9 payees, $100 to $1,200 each, $3,508.34 total | Contribution in month M, paid 10th-14th of M+1 (June 2025 pool invoices paid 2025-07-10 to 07-14) |
| 2 | Biome | $38,307.43 (2026-08-30); 12-mo received $33,237.13 | Yes, Project-Funded Bounties: "100% of the pledged amount will go to the contributor" | Per-issue; only 1 open S-Funding issue today (#1274, opened 2023-12-21); community bounties "currently halted" | Medium: task must be pre-approved; maintainer merge required | On merge ("A task is only completed when a Biome maintainer merges the pull request") |
| 3 | webpack | $92,721.39 (2026-09-16); est. annual budget $180,203.31; 12-mo received $130,032.97 | Policy text only: "$50/hour ... payouts when crossing the threshold of $300" | $50/h (goal text) | Unverified: expenses page snapshot contained no ledger; cannot confirm payouts occur | Unverified |
| 4 | Zig (ZSF, not OC) | 2024 spend $520,748.91, of which $306,362.09 contributor pay | Contractors only, by invitation: "provide opportunity for unpaid volunteers to become contractors" | "$60/hour" | Low-medium: no application form; must first be a sustained volunteer | Unpublished |
| 5 | Rust Foundation Maintainers Fund | Amount unpublished (AWS + Rust Leadership Council funding) | Long-term maintainers only; "open call for applications" when funded | Full-time MiR contracts, 12 months (Cargo MiR, 2026-09-22) | Low: "dedicated contracts for long-term maintainers" | Months |
| 6 | Astro | $231,036.25 (2026-08-21); est. annual $420,065.56; 12-mo received $351,439.56 | Core only: "Core Maintainer Stipend ... available to all core maintainers" | "$50 per hour ... maximum of $1000 each month"; also ad hoc invoices ("Astro Maintenance, June 2026" $438.70; docs $6,120) | Medium: "Astro can pay out to anyone" but stipend requires core status | Monthly invoices, paid 1st-2nd of next month |
| 7 | Vite | $77,355.54 (2026-09-21); est. annual $119,685.50 | Core only: "Core Team Member Stipend ... available to all core team members" | "$50 USD per hour ... maximum of $3000 USD each month" | Medium-low: need core-team status; 3 payees May-Sep 2026 | Monthly |
| 8 | Homebrew | $160,812.60 (2026-09-18); est. annual $102,076.09 | Maintainers only | "The stipend is US$300/month", invoiced quarterly as US$900 | Low: must become a maintainer (governance activity thresholds) | Quarterly (Jan/Apr/Jul/Oct) |
| 9 | curl | $107,916.75 (2026-09-13); est. annual $90,592.86 | No published non-core policy; pays named maintainers ("curl maintenance" $6,870-10,000 invoices, 6 payees in latest 10) | ad hoc | Low; "There is no bug bounty" | n/a |
| 10 | Babel, Vue, Svelte, Servo, Prettier, Rollup, Mocha | Babel $196,846.87; Vue $42,726.37; Svelte $94,223.57; Servo $75,922.86; Prettier $72,270.02; Rollup $55,303.11; Mocha $70,898.70 | No: each pays 1-3 named maintainers | Babel $6,000 + $3,000/mo; Vue $7,000-8,000/mo to 1 person; Svelte $2,040-3,860 per half-month to 1 person; Servo $5,662-6,697/mo to 1 person; Prettier $1,000-1,250/mo; Rollup $218-902/mo; Mocha $137.50-3,200 | Very low (closed circle) | n/a |
| 11 | Godot, Blender, Django, PSF, Sequoia, Matrix, Mastodon, Ghost, Ladybird, Lichess, Bevy | Not on OC or not needed | Contractors/employees chosen from existing contributors or by invitation | Godot "10 contractors ... roughly 40,000 USD per month"; Django Fellows = "paid contractors"; Sequoia "by invitation only" | Very low for a newcomer | Months |
| 12 | Jest, Storybook, Solid, Jellyfin, Mastodon OC, Tailwind OC, Nuxt | Jest $103,131.83 (budget $9,799); Storybook $13,127.70; Solid $20,282.32; Jellyfin $36,817.52; Mastodon $24,127.56; Tailwind -$10,000; Nuxt no snapshot | No contributor-pay policy found; expenses are hosting/CI/travel | none | n/a | n/a |

Bounty boards (section 3): every non-Algora board checked is dead, pivoted, or empty as of 2026-09-24. Tolgee: 0 open bounty issues (last closed 2025-05-22). Polar: issue funding sunset April 2025. IssueHunt: now a Japanese security bug-bounty platform. Gitcoin: bounties site gone; grants are for projects. ossbounties.com: parked. boss.dev: JS shell, no data. Algora: /bounties returns 404; homepage is a recruiting product.

Implication for the operator: the only place where an unknown outside contributor is paid by published rule, without applying, is ESLint ($100+ per non-trivial merged contribution, ~$900-3,500 pool per month). Everything else pays insiders. The realistic path elsewhere is "sustained contributor -> invited contractor" (Zig, Godot, Blender, Rust MiR), which is measured in months.

## 1. Open Collective data

### Access log (what worked, what did not)
- api.opencollective.com/graphql/v2: GET returned a CSRF error asking for a content-type header; POST with `Content-Type: application/json` and browser UA returned HTTP 403 Cloudflare "Just a moment..." challenge. WebFetch tool: 403. r.jina.ai proxy: 403 (Cloudflare page relayed).
- opencollective.com/{slug}.json, /{slug}, /{slug}/expenses, /{slug}/transactions.json, /{slug}/badge.svg, api.opencollective.com/v1/collectives/{slug}: all 403 Cloudflare.
- img.shields.io/opencollective/all/{slug}.json: works, but exposes only backer counts (eslint 567; webpack backers 2.1k).
- web.archive.org/web/2026id_/https://opencollective.com/{slug}: WORKS. Page snapshots embed the Apollo cache with `balance`, `yearlyBudget`, `totalAmountReceived(periodInMonths:12)`, `goals`; expenses snapshots embed the latest 10 expenses (status, amount, payee ref, description). 2026 snapshots are gzip-encoded. Several fetches timed out (HTTP 000) on the first pass and succeeded on retry. No snapshot existed for: eslint.json, babel.json, nuxt/nuxtjs (2026), godotengine, vitejs (slug is `vite`), astro (slug is `astrodotbuild`), mocha (slug is `mochajs`). Not OC-hosted or no slug: blender, bevy, deno, ladybird, zig/ziglang, rust-foundation, lichess, ghost, matrix, tailwindcss (exists, dormant).
- An earlier proxy fetch on 2026-09-24 20:49 (saved as oc/jina_eslint_expenses.md) captured ESLint's live paid-invoice page 1.

### Per-collective figures (USD; snapshot date in brackets)

| Slug | Balance | Est. annual budget (yearlyBudget) | Received last 12 mo | Latest 10 expenses in snapshot (date of snapshot): paid count / total / distinct payees / nature |
|---|---|---|---|---|
| eslint | $111,952.48 (2026-09-23) | $140,196.59 | unverified | (2025-07-20) 10 paid / $4,643.20 / 10 payees; 9 x "Contributor Pool - June 2025" ($100, $136.97, $171.37, $200, $300, $300, $500, $600, $1,200 = $3,508.34) + 1 health-insurance receipt. Live page 1 (2026-09-24): 10 paid invoices, page total $11,510.14, incl. 2 x $100 "Contributor Pool - August 2026" (Dongkyu Lee paid 2026-09-09, Kyle paid 2026-09-05) and 8 "Maintenance and Development - August 2026" invoices ($340 to $2,800.40) from team members |
| webpack | $92,721.39 (2026-09-16) | $180,203.31 | $130,032.97 | (2026-02-09) expenses ledger not present in snapshot (client-rendered); unverified |
| babel | $196,846.87 (2026-09-16) | $257,109.99 | unverified | (2025-11-11) 9 paid / $42,000 / 2 payees; "$6,000 Babel development and support (month)" + "$3,000 Babel Engineering Support" monthly |
| vuejs | $42,726.37 (2026-08-27) | $201,919.00 | $143,819.62 | (2025-10-02) 10 paid / $59,118.99 / 3 payees; "Vue.js contribution (month)" $7,000-8,000 to one individual, $1,000 to a second, $12,000 one-off |
| vite | $77,355.54 (2026-09-21) | $119,685.50 | $112,580.50 | (2026-09-21) 10 paid / $16,450 / 3 payees; "Maintenance and Development for Vite in August 2026" $1,200-3,000; "Core team stipend for June" $1,000 |
| astrodotbuild | $231,036.25 (2026-08-21) | $420,065.56 | $351,439.56 | (2026-08-01) 8 paid / $12,558.70 / 6 payees; "Core Maintainer Stipend - June 2026" $1,000 x4; "Astro Maintenance, June 2026" $438.70; docs/Starlight maintenance $6,120 |
| svelte | $94,223.57 (2026-09-13) | $20,423.28 | $19,088.28 | (2026-08-01) 9 paid / $18,043.70 / 2 payees; one individual invoices "Maintenance and Development" per half-month $2,040-3,860 |
| solid | $20,282.32 (2026-09-23) | $26,699.00 | $18,803.00 | expenses snapshot not retrievable |
| storybook | $13,127.70 (2026-09-13) | $19,819.00 | $20,003.09 | (2026-05-11) 10 paid / $28,175.42 / 2 payees; all "CI/DB" reimbursements $2,195-5,030/mo |
| mochajs | $70,898.70 (2026-09-06) | $30,157.87 | $19,832.28 | (2025-02-13) 9 paid / $9,447.50 / 2 payees; "Maintenance and Development" $137.50-3,200 |
| jest | $103,131.83 (2026-07-28) | $9,799.00 | $10,581.44 | expenses snapshot not retrievable |
| rollup | $55,303.11 (2026-09-23) | $16,361.00 | $16,930.25 | (2025-04-21) 10 paid / $5,492.73 / 1 payee; "Rollup maintenance and feature development (month)" $218-902 |
| biome | $38,307.43 (2026-08-30) | $33,237.13 | $33,237.13 | (2026-08-01) 10 paid / $10,509.67 / 8 payees; 6 x $1,000 "Maintenance work from 1 January 2026 to 31 March 2026"; docs $1,500 + $660; 2 travel receipts |
| tailwindcss | -$10,000.00 (2026-08-31) | $0.00 | n/a | no expenses; dormant collective |
| mastodon | $24,127.56 (2026-09-13) | $7,557.04 | $7,375.04 | (2026-05-09) 8 paid / $13,125 / 3 payees; sporadic ("Mastodon 4.0 Documentation" $6,475 in 2022, illustrations pending 2026) |
| homebrew | $160,812.60 (2026-09-18) | $102,076.09 | unverified | (2026-09-07) 10 paid / $6,300.77 / 8 payees; 4 x $900 "Maintainer Stipend, April-June 2026", 1 x $1,800; rest cloud charges |
| curl | $107,916.75 (2026-09-13) | $90,592.86 | $87,822.86 | (2026-04-03) 10 paid / $106,049.19 / 6 payees; "curl maintenance" $10,000 x3, $6,870.75, $6,990.76; laptop $35,793; hosting $13,200 |
| jellyfin | $36,817.52 (2026-09-15) | $26,720.10 | $24,755.90 | (2026-08-31) 10 paid / $4,088.38 / 2 vendors; DigitalOcean + Patreon charges only |
| servo | $75,922.86 (2026-09-16) | $88,936.37 | $79,100.68 | (2026-04-18) 10 paid / $33,459.37 / 2 payees; one individual "(month) project work" $5,662-6,697.44; Hetzner $404/mo |
| prettier | $72,270.02 (2026-09-14) | $52,035.16 | $52,347.32 | (2025-02-13) 9 paid / 2 payees; "Development and maintenance (month)" $1,000-1,250 and $2,500-4,500 per quarter; one invoice shown as ¥439,785 (= $3,031.01) |
| nuxt / nuxtjs | no 2026 Wayback snapshot (FUNDING.yml: `open_collective: nuxtjs`) | unverified | unverified | unverified |
| godotengine | Wayback 404; Godot funds via godot.foundation, not OC | n/a | n/a | n/a |
| blender, bevy, deno, ladybird, zig, rust-foundation, lichess, ghost, matrix | no OC snapshot; not OC-funded (own foundations/companies) | n/a | n/a | n/a |

## 2. Published contributor-pay policies

| Project | Pays non-core contributors? | Amount | Eligibility (verbatim) | Source |
|---|---|---|---|---|
| ESLint | YES | "$100" minimum per contributor per month from a pool; team "$80.00 USD/hour for TSC members and Reviewers and $50.00 USD/hour for committers ... maximum of 40 hours per month" | "We set aside 10% of our monthly income to pay outside contributors who have made significant contributions to the project. Contributions include submitting code, writing documentation, answering questions in our Discord server, and more. This money is allocated each month by the TSC." and "The contributors don't need to apply ahead of time or ask for permission; if you make a significant contribution, you'll get an email from the TSC letting you know how to collect your payment." | https://eslint.org/donate/ ; https://eslint.org/blog/2022/02/paying-contributors-sponsoring-projects/ |
| Astro | No (core only); anyone can be reimbursed | "$50 per hour contributed, with a maximum of $1000 each month" | "A stipend of up to $1000 per calendar month is available to all core maintainers." ; "Open Participation. Anyone can request reimbursement for funds spent helping the Astro project and Astro can pay out to anyone." | https://github.com/withastro/.github/blob/main/FUNDING.md (Last Updated: 03-30-2023) |
| Vite | No (core only) | "$50 USD per hour contributed, with a maximum of $3000 USD each month" | "A stipend of up to $3000 USD per calendar month is available to all core team members." | https://github.com/vitejs/.github/blob/main/FUNDING.md |
| Homebrew | No (maintainers only) | "The stipend is US$300/month." | "Maintainers will not receive the stipend for months where they are doing paid project work."; "Each quarter, the Project Leader will notify maintainers whose contributions in the preceding quarter were insufficient for the stipend." | https://github.com/Homebrew/brew/blob/HEAD/docs/Maintainer-Stipends-and-Grants.md (last_review_date 2026-07-18) |
| Biome | YES for pre-approved funded issues | Project-funded: "100% of the pledged amount will go to the contributor completing the task"; community-funded: "Biome reserves 30% of the payment amount, meaning contributors receive 70%" | "Community-Funded Bounties (currently halted)"; "Bounties cannot be opened for bug fixes"; "Implementation of the task funded by Biome must advance our roadmap"; "A task is only completed when a Biome maintainer merges the pull request that closes the task." Contractors: "There's no limit on the amount of compensation and rate; however, the funds can only be paid via Open Collective." Fund allocation: "Other usage of funds has yet to be decided." | https://github.com/biomejs/biome/blob/main/GOVERNANCE.md |
| webpack | Policy text only (OC goal) | "$50/hour" | "This yearly budget is needed to pay the current amount of github contributions with a rate of $50/hour. Contributors will start receiving payouts when crossing the threshold of $300." (goal amounts $255,000 to $1,000,000/yr; current budget $180,203) | Wayback snapshot of https://opencollective.com/webpack (2026-09-16) |
| Zig (ZSF) | Contractors by invitation | "$60/hour" | "Direct compensation to contributors working on Zig at a rate of $60/hour." ; "we also want to provide opportunity for unpaid volunteers to become contractors who can earn a living with their contributions." 2024: "$306,362.09" contributor pay of "$520,748.91" total; "spend 92% of our money in 2024 paying contributors for their time." | https://ziglang.org/news/2025-financials/ ; https://ziglang.org/zsf/ |
| Rust Foundation | Long-term maintainers, open call when funded | Full-time contract | "Funds contributed to the RFMF go exclusively to Rust maintainers, through a combination of existing programs and a new Maintainer in Residence program - dedicated contracts for long-term maintainers ... When funding is available, the Funding Team puts out an open call for applications". 2026-09-22: "hire a full-time maintainer to work on Cargo for (at least) the next 12 months." | https://rustfoundation.org/media/help-fund-the-people-who-build-rust/ ; https://rustfoundation.org/media/announcing-a-maintainer-in-residence-scott-schafer-for-the-cargo-team/ |
| Babel | No (salaried core) | 2021: "$6,000 per month" temporary rate; OC goal "3 maintainers ... $333,333" | "The goal is to pay Henry, Junliang and Nicolo a salary as maintainers." | https://babeljs.io/blog/2021/05/10/funding-update ; OC snapshot |
| Vue | No published policy; OC shows 1-3 payees | $7,000-8,000/mo to one individual | none published; sponsor page lists tiers only | https://vuejs.org/sponsor/ ; OC snapshot |
| Svelte, Prettier, Rollup, Mocha, Servo | No published non-core policy; pay 1-2 named maintainers via monthly invoices | see table 1 | Servo: jdm "would work part-time on improving the Servo contributor experience, entirely funded by the monthly donations on OpenCollective and GitHub" | https://servo.org/blog/2026/09/15/one-year-of-sponsorship/ ; OC snapshots |
| Storybook, Jest, Solid, Nuxt, Tailwind, Node.js | No policy; READMEs/FUNDING.yml only link to OC/sponsors | none | Node README lists per-maintainer GitHub Sponsors links only | raw READMEs / FUNDING.yml fetched |
| Django (DSF) | Fellows are contractors | unpublished | "The Django Fellowship program ... paid contractors are engaged to manage some of the administrative and community management tasks"; 2026 fundraising: "$238,304.61 donated of a $500,000.00 USD goal for 2026" | https://www.djangoproject.com/fundraising/ |
| PSF | No open DiR call in 2026 | n/a | 2026-04-13 post "Reflecting on Five Years as the PSF's First CPython Developer in Residence"; blog label search returns "No posts with label developer in residence" | https://pyfound.blogspot.com/feeds/posts/default?q=residence |
| Blender | Grants to named developers; no application route on page | unpublished | Page lists "Full time grants" and "Part time grants" by name for each half-year (Jan-Jun 2026: 31 full-time, 8 part-time, 8 "New grants") | https://fund.blender.org/grants/ |
| Godot | Contractors chosen from contributors; no postings | "10 contractors (some part-time, some full-time) for a total cost of roughly 40,000 USD per month" (2023) | "We typically do not make public job postings, we identify individuals who are already knowledgeable about Godot, have experience in areas that need more contributions, and work well with other contributors." | https://godotengine.org/article/funding-breakdown-and-hiring-process/ |
| Ghost | Employees only | n/a | "We use our revenue to hire amazing developers"; "open source contributors from all over the world who graciously volunteer their time" | https://ghost.org/about/ |
| Matrix | Foundation staff under contract | n/a | "most of our staffers are employees of Element, working under a contract with, and funded by, the Foundation." | https://matrix.org/foundation/about/ |
| Mastodon | Employees | n/a | 2024 report: "grew our team from three to over six full-time employees."; Patreon "€248,531" | https://joinmastodon.org/reports/Mastodon%20Annual%20Report%202024.pdf |
| Home Assistant (OHF) | No open jobs | n/a | Ashby job board API: `{"jobs":[],"apiVersion":"1"}` | https://api.ashbyhq.com/posting-api/job-board/openhomefoundation |
| Ladybird | No | n/a | "Our team size is stable for now. We will revisit hiring as the project's needs evolve." | https://ladybird.org/ |
| Bevy | Maintainers only | n/a | "Hiring Maintainers ... Our bar for maintainership is high." | https://bevy.org/donate/ |
| Deno, Bun | Companies; no bounty labels | n/a | oven-sh/bun has no bounty label; denoland CONTRIBUTING has no pay text | gh API label lists |
| Lichess | One full-time developer | n/a | "Then we pay a full-time developer: thibault, the founder of Lichess." | https://lichess.org/patron |
| curl | No | n/a | "There is no bug bounty and the curl project never offers rewards for reported vulnerabilities." ; "The best way to sponsor this project is to allow a paid engineer or two to spend work hours on curl." | https://curl.se/docs/bugbounty.html ; https://curl.se/sponsors.html |
| Sequoia OSS Fellowship | Invitation only | "stipend to cover their living expenses for 6 to 12 months" | "Consideration for the Sequoia Open Source Fellowship is by invitation only; we aim to support established creators" | https://www.sequoiacap.com/article/sequoia-open-source-fellowship/ |

## 3. Paid-issue boards other than Algora (live status 2026-09-24)

| Board | Status | Evidence |
|---|---|---|
| Biome bounties | 1 open funded issue | gh search `repo:biomejs/biome label:S-Funding is:open` total=1 (#1274 "Tailwind class sorting lint rule", opened 2023-12-21); 3 closed (2024-2025). No "bounty" label. GOVERNANCE: "Community-Funded Bounties (currently halted)". |
| Tolgee | 0 open | labels "💎 Bounty" (5 issues, all closed, last 2025-05-22) and "🙋 Bounty claim" (5 PRs, all closed). No bounty page on tolgee.io. |
| Polar | Issue funding sunset | polarsource/polar#5219 (2025-03-10) "Issue Funding: Replace pledge form with sunset announcement until April 2nd"; #5222 "Issue Funding: Remove from codebase after April 2nd". polar.sh homepage is a billing product ("3.80% + 40c per transaction"). |
| IssueHunt | Pivoted | issuehunt.io: "#1 Bug Bounty Platform in Japan"; "Company will pay on triage or once the issue has been fixed." (security VDP, not OSS issues) |
| Gitcoin bounties | Gone | bounties.gitcoin.co: DNS failure; gitcoin.co/bounties: 404; gitcoin.co/program: "Gitcoin Grants is a seasonal initiative empowering early-stage builders" (project grants, "3,715 Projects Raised Funds") |
| BOSS (boss.dev) | Unverifiable | Page title "boss, github with bounties"; React shell, no server-rendered data |
| ossbounties.com | Parked | Title "ossbounties.com - ossbounties Resources and Information." |
| Rust Foundation | Not a bounty board | Maintainers Fund / MiR (see section 2); rustfoundation.org/grants redirects to /project-support/ with no grant call text rendered |
| Ruby Central | No bounty program found | rubycentral.org/news: only "RubyConf Scholars and Guides", "local meetup grants"; nothing on developer pay; unverified |
| Sequoia OSS Fellowship | Not a board; invitation only | see section 2 |
| Algora (for reference) | /bounties 404 | algora.io homepage: "Hire the top 1% open source engineers"; embedded widget "No open bounties. Create bounties by commenting /bounty $1000 on GitHub issues" |
| GitHub "bounty" label sweep (earlier run, gh/bounty_label_recent.txt) | Noise | Most recent "bounty"-labelled issues on 2026-09-24 are ~60 from one repo, OphirPay/OphirPay (Stellar wallet), plus a game mod; no established OSS project |

## 4. Access notes / caveats
- All OC balances are point-in-time archive snapshots (dates given), not today's live values.
- "Latest 10 expenses" understates monthly volume for busy collectives (ESLint pays ~12 team invoices per month plus the pool; June 2025 pool alone had 9 payees).
- Currency: Prettier's ¥439,785 line is JPY (displayed as $3,031.01 USD on the page).
- webpack's contributor payout scheme is only evidenced by OC goal text; no ledger was retrievable.
- No WebSearch was available (session budget exhausted); everything here is from direct fetches, gh API, and Wayback.

## Sources

| URL | Supports | Quoted text | Fetched |
|---|---|---|---|
| https://eslint.org/donate/ | ESLint pool policy, income | "currently 134 companies, organizations, and individuals donating $9,220.15 each month" ; "We set aside 10% of our monthly income to pay outside contributors" ; "$80.00 USD/hour for TSC members and Reviewers and $50.00 USD/hour for committers" | 2026-09-24 |
| https://eslint.org/blog/2022/02/paying-contributors-sponsoring-projects/ | ESLint minimum and no-application rule | "awards at least $100 to every outside contributor who has made a non-trivial contribution" ; "The contributors don't need to apply ahead of time" ; "In 2021, we awarded over $6,000 to outside contributors" | 2026-09-24 |
| https://opencollective.com/eslint/expenses?type=INVOICE&status=PAID (proxy capture 20:49) | ESLint Aug 2026 pool payouts | "Contributor Pool - August 2026 ... $100.00 USD Paid" (x2); "Page Total:$11,510.14 USD" | 2026-09-24 |
| https://web.archive.org/web/20260923183636id_/https://opencollective.com/eslint | ESLint balance | balance 11195248, yearlyBudget 14019659 (cents) | 2026-09-24 |
| https://web.archive.org/web/20250720163706id_/https://opencollective.com/eslint/expenses | June 2025 pool payees | 9 x "Contributor Pool - June 2025" PAID | 2026-09-24 |
| https://web.archive.org/web/20260916203115id_/https://opencollective.com/webpack | webpack balance and goal text | "pay the current amount of github contributions with a rate of $50/hour. Contributors will start receiving payouts when crossing the threshold of $300." | 2026-09-24 |
| https://web.archive.org/web/20260916185858id_/https://opencollective.com/babel ; .../20251111041056id_/https://opencollective.com/babel/expenses | Babel balance, payees | "The goal is to pay Henry, Jùnliàng and Nicolò a salary as maintainers." | 2026-09-24 |
| https://web.archive.org/web/20260827042000id_/https://opencollective.com/vuejs ; .../20251002210714id_/.../vuejs/expenses | Vue figures | "Vue.js contribution (September 2025)" $8,000 | 2026-09-24 |
| https://web.archive.org/web/20260921124724id_/https://opencollective.com/vite ; .../20260921124711id_/.../vite/expenses | Vite figures | "Core team stipend for June" $1,000 | 2026-09-24 |
| https://web.archive.org/web/20260821233625id_/https://opencollective.com/astrodotbuild ; .../20260801121317id_/.../astrodotbuild/expenses | Astro figures | "Core Maintainer Stipend - June 2026" $1,000 | 2026-09-24 |
| https://web.archive.org/web/20260913034325id_/https://opencollective.com/svelte ; .../20260801124619id_/.../svelte/expenses | Svelte figures | "Maintenance and Development (16/07/2026-31/07/2026)" $3,860 | 2026-09-24 |
| https://web.archive.org/web/20260923180546id_/https://opencollective.com/solid | Solid figures | balance 2028232 | 2026-09-24 |
| https://web.archive.org/web/20260913051351id_/https://opencollective.com/storybook ; .../20260511144936id_/.../storybook/expenses | Storybook figures | "CI/DB Apr 26" $3,126.98 | 2026-09-24 |
| https://web.archive.org/web/20260906010913id_/https://opencollective.com/mochajs ; .../20250213135303id_/.../mochajs/expenses | Mocha figures | "Maintenance and Development - October 2024" $1,200 | 2026-09-24 |
| https://web.archive.org/web/20260728044246id_/https://opencollective.com/jest | Jest figures | balance 10313183, yearlyBudget 979900 | 2026-09-24 |
| https://web.archive.org/web/20260923175318id_/https://opencollective.com/rollup ; .../20250421111443id_/.../rollup/expenses | Rollup figures | "Rollup maintenance and feature development December 2024" $254 | 2026-09-24 |
| https://web.archive.org/web/20260830165423id_/https://opencollective.com/biome ; .../20260801121334id_/.../biome/expenses | Biome figures | "Maintenance work from 1 January 2026 to 31 March 2026" $1,000 (x5) | 2026-09-24 |
| https://web.archive.org/web/20260831232830id_/https://opencollective.com/tailwindcss | Tailwind OC dormant | balance -1000000, yearlyBudget 0 | 2026-09-24 |
| https://web.archive.org/web/20260913190803id_/https://opencollective.com/mastodon ; .../20260509213738id_/.../mastodon/expenses | Mastodon OC | "Mastodon 4.0 Documentation" $6,475 | 2026-09-24 |
| https://web.archive.org/web/20260918082146id_/https://opencollective.com/homebrew ; .../20260907183959id_/.../homebrew/expenses | Homebrew figures | "Homebrew Maintainer Stipend, April–June 2026" $900 | 2026-09-24 |
| https://web.archive.org/web/20260913145049id_/https://opencollective.com/curl ; .../20260403120546id_/.../curl/expenses | curl figures | "curl maintenance" $10,000 | 2026-09-24 |
| https://web.archive.org/web/20260915014718id_/https://opencollective.com/jellyfin ; .../20260831234146id_/.../jellyfin/expenses | Jellyfin figures | "Virtual Card charge: DIGITALOCEAN.COM" $825.68 | 2026-09-24 |
| https://web.archive.org/web/20260916062046id_/https://opencollective.com/servo ; .../20260418043906id_/.../servo/expenses | Servo figures | "March 2026 project work" $6,673 | 2026-09-24 |
| https://web.archive.org/web/20260914002000id_/https://opencollective.com/prettier ; .../20250213162545id_/.../prettier/expenses | Prettier figures | "Development and maintenance (January 2025)" $1,250; "¥439,785" | 2026-09-24 |
| https://github.com/withastro/.github/blob/main/FUNDING.md | Astro stipend | "$50 per hour contributed, with a maximum of $1000 each month" | 2026-09-24 |
| https://github.com/vitejs/.github/blob/main/FUNDING.md | Vite stipend | "$50 USD per hour contributed, with a maximum of $3000 USD each month" | 2026-09-24 |
| https://github.com/Homebrew/brew/blob/HEAD/docs/Maintainer-Stipends-and-Grants.md | Homebrew stipend | "The stipend is US$300/month." | 2026-09-24 |
| https://github.com/biomejs/biome/blob/main/GOVERNANCE.md | Biome bounties | "100% of the pledged amount will go to the contributor completing the task" ; "Community-Funded Bounties (currently halted)" | 2026-09-24 |
| https://ziglang.org/news/2025-financials/ | Zig rate and totals | "Direct compensation to contributors working on Zig at a rate of $60/hour." ; "$306,362.09" ; "$520,748.91" | 2026-09-24 |
| https://ziglang.org/zsf/ | Zig volunteer-to-contractor | "provide opportunity for unpaid volunteers to become contractors who can earn a living with their contributions" | 2026-09-24 |
| https://rustfoundation.org/media/help-fund-the-people-who-build-rust/ | RFMF rules | "Funds contributed to the RFMF go exclusively to Rust maintainers ... open call for applications" | 2026-09-24 |
| https://rustfoundation.org/media/announcing-a-maintainer-in-residence-scott-schafer-for-the-cargo-team/ | MiR hire | "hire a full-time maintainer to work on Cargo for (at least) the next 12 months" (September 22, 2026) | 2026-09-24 |
| https://babeljs.io/blog/2021/05/10/funding-update | Babel salaries | "paid a temporary rate of $6,000 per month" | 2026-09-24 |
| https://servo.org/blog/2026/09/15/one-year-of-sponsorship/ | Servo funded role | "work part-time on improving the Servo contributor experience, entirely funded by the monthly donations on OpenCollective and GitHub" | 2026-09-24 |
| https://www.djangoproject.com/fundraising/ | Django fellows | "paid contractors are engaged" ; "$238,304.61 donated of a $500,000.00 USD goal for 2026" | 2026-09-24 |
| https://pyfound.blogspot.com/feeds/posts/default?q=residence&alt=rss | PSF DiR | "Reflecting on Five Years as the PSF's First CPython Developer in Residence" (2026-04-13) | 2026-09-24 |
| https://fund.blender.org/grants/ | Blender grants by name | "Full time grants: ..." (January - June 2026 list) | 2026-09-24 |
| https://godotengine.org/article/funding-breakdown-and-hiring-process/ | Godot hiring | "We typically do not make public job postings" ; "10 contractors ... roughly 40,000 USD per month" | 2026-09-24 |
| https://ghost.org/about/ | Ghost employs | "We use our revenue to hire amazing developers" | 2026-09-24 |
| https://matrix.org/foundation/about/ | Matrix staffing | "most of our staffers are employees of Element, working under a contract with, and funded by, the Foundation." | 2026-09-24 |
| https://joinmastodon.org/reports/Mastodon%20Annual%20Report%202024.pdf | Mastodon staff | "grew our team from three to over six full-time employees." | 2026-09-24 |
| https://api.ashbyhq.com/posting-api/job-board/openhomefoundation | OHF no jobs | {"jobs":[],"apiVersion":"1"} | 2026-09-24 |
| https://ladybird.org/ | Ladybird hiring | "Our team size is stable for now." | 2026-09-24 |
| https://bevy.org/donate/ | Bevy | "Hiring Maintainers ... Our bar for maintainership is high." | 2026-09-24 |
| https://lichess.org/patron | Lichess | "Then we pay a full-time developer: thibault" | 2026-09-24 |
| https://curl.se/docs/bugbounty.html ; https://curl.se/sponsors.html | curl | "There is no bug bounty" ; "allow a paid engineer or two to spend work hours on curl" | 2026-09-24 |
| https://www.sequoiacap.com/article/sequoia-open-source-fellowship/ | Sequoia | "by invitation only" ; "stipend to cover their living expenses for 6 to 12 months" | 2026-09-24 |
| gh api search/issues (biomejs/biome label:S-Funding) | Biome open funded issues | total=1 open, 3 closed | 2026-09-24 |
| gh api search/issues (tolgee/tolgee-platform label:"💎 Bounty") | Tolgee bounties | 5 closed, 0 open | 2026-09-24 |
| https://github.com/polarsource/polar/issues/5219 ; /issues/5222 | Polar sunset | "Issue Funding: Replace pledge form with sunset announcement until April 2nd" ; "Remove from codebase after April 2nd" | 2026-09-24 |
| https://issuehunt.io/ | IssueHunt pivot | "#1 Bug Bounty Platform in Japan" | 2026-09-24 |
| https://gitcoin.co/program ; https://gitcoin.co/bounties (404) ; bounties.gitcoin.co (DNS fail) | Gitcoin | "Gitcoin Grants is a seasonal initiative empowering early-stage builders" | 2026-09-24 |
| https://ossbounties.com/ | Parked | "ossbounties.com - ossbounties Resources and Information." | 2026-09-24 |
| https://www.boss.dev/ | Unverifiable | title "boss, github with bounties" | 2026-09-24 |
| https://algora.io/ ; https://algora.io/bounties (404) | Algora status | "Hire the top 1% open source engineers" ; "No open bounties" | 2026-09-24 |
| https://img.shields.io/opencollective/all/eslint.json | Backer count only | {"value":"567"} | 2026-09-24 |
