# 07 Maintainer succession: adopt/co-maintain an under-maintained package and get paid

Date: 2026-09-24. Method: direct fetch (curl/WebFetch) of primary pages plus gh CLI. Every quoted string is verbatim from the fetched page. Items marked "unverified" were not fetchable.

## 1. Tidelift (now Sonar) lifter program

Status 2026 (measured from fetched pages, 2026-09-24):
- https://tidelift.com/about/lifter now 301-redirects to https://www.sonarsource.com/open-source-maintainers/ (live, footer "© 2026 SonarSource Sàrl"; embedded CMS timestamps 2025-05-05 and 2025-06-04). The page still has a package-search intake: "See if your package is eligible for income by finding your package:" linking to https://tidelift.com/lifter/search?q= . https://tidelift.com/lifter/apply and https://tidelift.com/lifter return HTTP 200 but are a JS app ("Tidelift requires JavaScript"), so whether applications are currently being approved is unverified. No page fetched says "closed to new lifters"; no page fetched says "open" either.
- Sonar acquisition press release (https://www.sonarsource.com/company/press-releases/sonar-to-acquire-tidelift/, no date in body, page live): "The Tidelift offering will continue to be available – there are no immediate planned changes to the current Tidelift product. Tidelift customers and maintainer partners will not experience any disruption to their current experiences." and "Additional details will be provided in Q1 2025."
- Vendor claim on the same release: "Paid open source maintainers are 55% more likely to implement critical security and maintenance practices than unpaid maintainers."

How lifters are paid (support article "How we pay lifters", Updated December 04, 2023, fetched via Wayback snapshot 2025-03-01 because support.tidelift.com returns 403 to non-browser clients; snapshots exist through 2025-12-31):
- "Tidelift pays maintainers income based on a number of factors, including subscriber usage and strategic importance of a package to the overall health and resilience of the open source software supply chain."
- "To calculate income based on subscriber usage, we analyze each of the software bills of materials (SBOMs) our customers have uploaded and distribute income to maintainers based on the projects subscribers use."
- "On the third business day of the month, we analyze the uploaded SBOMs for all of our subscriptions for the preceding month to allocate the income for packages they use."
- Weight: "A package containing a large framework gets a larger share than one containing a 2-line function. Currently, the weight is based primarily on code size with some adjustments."
- "Packages receive income based on how many subscribers use their package."
- Co-maintainers: "By default, the first maintainer for a package configures the bank account for 100% of the package's earnings, but on request we can split it up among co-maintainers or move bank account responsibility to a different maintainer." Split requires each co-maintainer to sign the lifter agreement; payout via Hyperwallet; sanctions screening applies ("Any countries or banks that have been sanctioned will be blocked").

Eligibility / onboarding ("Getting started with lifting", Updated May 30, 2023, Wayback 2025-10-16):
- "If you're not already a lifter, please apply to become a lifter at https://tidelift.com/about/lifter."
- Applicant must be the publisher: "you'll need to upload your package to the appropriate platform repository (Maven, npm, RubyGems, etc.)" and the package is found "via your username on the appropriate platform (npm, rubygems, etc.)". Then "LIFT YOUR PACKAGE" -> "we will process your request within 3-5 business days."
- Implication (my inference, not a quote): a new co-maintainer must first hold publish rights on the registry before Tidelift can match the package to them.

Published totals or averages: none found on any fetched page. Only statements: "While we do pay some maintainers six figure incomes, we always want to pay more money to more maintainers." (xz post, April 2, 2024, https://www.sonarsource.com/blog/xz-tidelift-and-paying-the-maintainers/) and "all of the 40+ countries where we support maintainers." (same). The all-time total paid to lifters is unverified.

Succession precedent (same xz post): "Sometimes, for perfectly good reasons, a maintainer wants to stop working on their project. When this happens, we help find trusted maintainers from our network interested in getting paid to continue the work. We've done this, for example, with SockJS and minimist." This is the one mechanism where a non-founder gets paid for adoption, and it is invitation-based ("from our network").

Tidelift's stated policy against paying non-maintainers ("Paying maintainers: the HOWTO", April 15, 2023, https://www.sonarsource.com/blog/paying-maintainers-the-howto/): "it's important to pay, as much as possible, the actual maintainers, not people who say they'll help out." and "If you pay someone who isn't the maintainer to do work, congratulations, you've just made the maintainer's life [harder]". Pay is tied to tasks: "enabling two-factor authentication, creating a discoverable security policy, and providing fixed releases to address vulnerabilities." Pilot result (vendor claim): "the paid maintainers improved their scores by 57%. Those maintainers who joined the pilot ended up with an average scorecard score of 7.2 out of 10, compared to 3.3 out of 10".

Assessment: a NEW maintainer can only enter Tidelift by (a) obtaining publish rights on a package that Tidelift subscribers already use, then applying, or (b) being picked from Tidelift's network for a handoff. Income is proportional to subscriber SBOM usage and code weight; no per-package figure is published.

## 2. HeroDevs (Never-Ending Support) and the Open Source Sustainability Fund

There is no public "maintainer partner program" page: https://www.herodevs.com/maintainers returns 404; https://www.herodevs.com/partners is a reseller/advisory directory. The maintainer-facing offers are (a) the Open Source Sustainability Fund and (b) bespoke NES partnerships with project teams/foundations (Vue 2, Nuxt, Vuetify, ESLint, Express via OpenJS, Node.js, Drupal 7), which are negotiated with the existing project, not with outside individuals.

Fund page https://www.herodevs.com/sustainability-fund (live 2026-09-24, "© 2026"):
- "Grab your slice of our $20 million Open Source Sustainability Fund"
- Eligibility: "You are a maintainer of open-source projects under an OSI-approved license." / "Versions of your project are approaching or are already past official EOL." / "You're ready to keep users secure, compliant, and CVE-free!" / "Must be a developer tool."
- Amount: "Grants range from $2,500 to $15,000."
- Apply: "You can submit an application here." (Google Form: https://docs.google.com/forms/d/e/1FAIpQLSczQp6Wtlbbvdw2rgU7NgtEq9PuADyy0FLCoHOtlGTKis9fRA/viewform)
- Process: "When you apply, a member of our team will reach out and let you know your application is received and under review. If approved, we will contact you to begin the process of criteria review and implementation of best practices."
- EOL versions: "HeroDevs does offer other types of partnerships that focus solely on versions that have gone end-of-life. If you are interested in partnerships outside of the Fund, please contact us to learn more!"

Press release https://www.herodevs.com/blog-posts/herodevs-launches-20-million-sustainability-fund-for-open-source-creators-to-secure-end-of-life-software (June 23, 2025):
- "Accepted applicants of The Open Source Sustainability Fund will receive between $2,500 and $250,000 in donations. To be accepted, applicants must demonstrate strong community adoption and traction, show their commitment to following security best practices when announcing and conducting EOL motions for their project, and agree to the Sustainability Fund's requirements."
- "Applications will officially open on July 22, 2025."
- Vendor claim on past payouts: "Since 2021, HeroDevs has donated over $4 million in total and in 2024 donated over $2 million—all given to project creators and maintainers."
- Discrepancy: the FAQ on the fund page says $2,500-$15,000; the press release says $2,500-$250,000. Both are vendor statements; number of grants awarded to date is not published (unverified).

NES partnership mechanics (OpenJS post, May 21, 2024): "HeroDevs will donate a portion of all proceeds from the sale of its services to the OpenJS Foundation and its open source projects for future innovation and development." The percentage is not published (unverified). Express NES post: "HeroDevs has been able to collaborate with maintainers and community members who expressed a clear demand for continued support of end-of-life software."

Assessment for a new maintainer: the Fund requires you to already be "a maintainer" of a project with "strong community adoption and traction" that is at/near EOL, and it is a grant with best-practices homework, not a retainer. Payment size floor is $2,500. NES revenue-share partnerships go to project owners/foundations.

## 3. thanks.dev

Verifiable (fetched 2026-09-24):
- https://thanks.dev/ returns 200 but is a JS shell; every subpage tried (/docs, /faq, /about, /pricing, /blog, /how-it-works, /dependents) returns HTTP 403 to non-browser clients. Only the meta description is readable: "We're passionate about making open source sustainable. Scan your dependancy tree to better understand which open source projects need funding the most. Maintainers can also register their projects to become eligible for funding."
- GitHub org is `thnxdev` (not `thanks-dev`): created 2020-10-08, blog https://www.thanks.dev, 6 public repos. Repo `thnxdev/thanks` (7 stars, last push 2024-06-12) README: "This shell script can be used to upload a repositories manifest files to thanks.dev as part of a CI/CD pipeline" with "--type (go.list,pom.xml,package.json) [required]". So the ingest path is NOT JS-only: Go (go.list), Java/Maven (pom.xml) and npm (package.json) manifests are accepted. PyPI is not in that list (the claim that it is JS-only is false; the claim that it is npm+Go+Maven only is supported by this script). Issue thnxdev/issues#10 (2024-11-01) "Add .NET support" is open.
- `thnxdev/utils` README describes "mass-gh-sponsor: used to set up monthly GH sponsorships for all dependencies" and an API at "https://api.thanks.dev" (payment rails appear to be GitHub Sponsors on the donor side). Issue #20 (2025-10-28): "api.thanks.dev SSL certificate expired on October 27th" indicates thin operations. Most recent public activity in the issue tracker: #21, 2025-11-10.
- Payout amounts, fee, number of funded maintainers: not fetchable; unverified.

Assessment: a dependency-graph distribution of donor money; a new co-maintainer cannot "adopt" a package into it, only a repo with a FUNDING.yml/registered maintainer receives it. Not a 90-day revenue path.

## 4. Package abandonment data (with n)

| Source | n / window | Measured statement (verbatim) | Type |
|---|---|---|---|
| Zahan et al., "What are Weak Links in the npm Supply Chain?", ICSE-SEIP 2022, https://arxiv.org/abs/2112.10165 (Submitted 19 Dec 2021; PDF https://arxiv.org/pdf/2112.10165) | "we analyzed the metadata of 1.63 million JavaScript npm packages"; survey "responded to by 470 npm package developers" | Definition: "We considered a package inactive if the package's last modification time in the package.json file is past two years." Result: "We found 58.7% of packages and 44.3% of maintainers are inactive in the npm registry." Popular packages: "W3: 38% of popular packages were inactive, and 560 of them were deprecated. 645 popular packages did not have any active maintainers. An inactive package exposed 422 packages on average to higher supply chain risk." Threat model names the adoption route explicitly: "Ownership transfer: An attacker can show enthusiasm to maintain popular abandoned packages and transfer the ownership of a package". | measured (academic), data as of 2021 |
| Black Duck OSSRA 2026 (report published 2026; audit window Nov 2024 to Oct 2025), https://www.blackduck.com/resources/analyst-reports/open-source-security-risk-analysis.html and https://www.blackduck.com/blog/open-source-trends-ossra-report.html | "the 947 codebases submitted to Black Duck between November 2024 and October 2025 entail the analysis of nearly 3,000 individual projects" across "17 industries" | "Ninety-three percent of the codebases we audited contain components with no development activity in over two years." Also: "92% of codebases containing components four or more years out-of-date". "Organizations face a choice: fork the project and maintain it themselves, find an alternative and refactor, or accept the risk." | measured (vendor audit sample; M&A-skewed) |
| Black Duck OSSRA 2025 (Feb 2025) | requested by task; the 2025 edition's percent could not be extracted from the fetched press page (https://news.blackduck.com/2025-02-25-Black-Duck-Report returned only boilerplate). Unverified. | | |
| Tidelift 2024 Maintainer Impact Report (PDF, https://www.sonarsource.com/the-2024-tidelift-maintainer-impact-report.pdf; https://tidelift.com/open-source-maintainer-survey-2024 redirects there) | "For the most recent survey in 2024, over 400 maintainers participated"; item n's: "n=437 (2024); n=326 (2023)" for pay status; "n=350 (2024); n=265 (2023)" for quitting | "Sixty percent of maintainers report they are unpaid hobbyists, and only 12% of maintainers consider themselves professionals who earn most or all of their income from their maintenance work." Quit question: "22% Yes, I have quit ... 38% Yes, I have considered quitting" i.e. "60% of maintainers have quit or considered quitting". Sonar summary page adds "almost half of maintainers surveyed said they were a solo maintainer." Succession pain quote: "in the end, you're so busy you don't even have time to try to find co-maintainers." | measured (self-selected survey) |
| Sonatype State of the Software Supply Chain 2024 (10th annual), https://www.sonatype.com/state-of-the-software-supply-chain/2024/introduction | registry-wide analysis; no abandonment percentage in fetched sections | "80% of application dependencies remain un-upgraded for over a year, even though 95% of these vulnerable versions have safer alternatives readily available." "0.5% of OSS components have no available update (No Path Forward)". | measured (vendor telemetry) |
| Sonatype 2026 (11th) https://www.sonatype.com/state-of-the-software-supply-chain/2026/software-infrastructure-growth | 2025 calendar year | "2025 saw 9.8 trillion downloads across Maven Central, PyPI, npm and NuGet, but the majority of registry traffic today is not driven by new applications or meaningful reuse. It's driven by transitive dependency sprawl, unused or abandoned packages, and unsustainable tooling patterns." Vulnerability section: "Dependence on EOL and abandoned components locks in permanent risk". No percentage of abandoned packages published in fetched sections. A 2025-edition page under /2025/ returns 404 (the 2025 report is now labelled 10th/2024 or replaced). | vendor claim (no n for "abandoned") |
| ecosyste.ms packages API, https://packages.ecosyste.ms/api/v1/registries/pypi.org (updated_at 2026-09-24) | registry-wide | pypi.org: "packages_count":937127, "maintainers_count":403047, "funded_packages_count":60629 (6.5% of PyPI packages carry funding metadata). npmjs.org endpoint returned HTTP 402 (rate-limited) at fetch time; ecosyste.ms publishes no "abandoned" percentage via this endpoint. | measured (open data) |

Takeaway: abandonment is common at the package level (58.7% of npm packages inactive >2y in 2021; 38% of popular ones) and near-universal at the consumer level (93% of audited codebases contain a >2y-inactive component). Supply of adoptable packages is not the constraint; the constraint is the money mechanism.

## 5. Mechanics: registry name transfer policies

npm (https://docs.npmjs.com/policies/disputes, fetched 2026-09-24, no revision date on page):
- "npm follows GitHub's Username Policy. This means that usernames, organization names, and package names are available on a first-come, first-served basis, and are intended for immediate and active use."
- "npm does not resolve squatting claims on demand. We do not transfer package, organization, or username ownership simply because another user wants the name. If you believe a name infringes a trademark or other intellectual property right you own, please follow the formal name dispute process on GitHub - that is the only path we act on."
- "Package names are considered squatted if the package has no genuine function."
- There is NO abandonment criterion and NO adoption/transfer route on the current npm policy page. The Wayback snapshot of 2023-04-02 already lacks the older "email the owner, wait N weeks" procedure. Consequence: on npm, succession is only possible by (1) the existing owner adding you as a maintainer (`npm owner add`), or (2) a fork under a new name (with the dependents problem that PEP 541 also names).

PyPI, PEP 541 "Package Index Name Retention" (https://peps.python.org/pep-0541/, Final; policy in force):
- Reachability: "the maintainers will try to do so at least three times ... The maintainers stop trying to reach the user after six weeks."
- Abandonment: "A project is considered abandoned when ALL of the following are met: owner not reachable (see Reachability above); no releases within the past twelve months; and no activity from the owner on the project's home page (or no home page listed)."
- Transfer to a new maintainer: "If a candidate appears willing to continue maintenance on an abandoned project, ownership of the name is transferred when ALL of the following are met: the project has been determined abandoned by the rules described above; the candidate is able to demonstrate their own failed attempts to contact the existing owner; the candidate is able to demonstrate improvements made on the candidate's own fork of the project; the candidate is able to demonstrate why a fork under a different name is not an acceptable workaround; and the maintainers of the Package Index don't have any additional reservations."
- "Under no circumstances will a name be reassigned against the wishes of a reachable owner."
- Timing implication (my inference): minimum ~6 weeks of documented contact attempts plus PyPI admin queue; PEP 541 requests are filed as issues at github.com/pypi/support and the backlog is long (backlog size not fetched; unverified).

## 6. Open "maintainer wanted" issues on GitHub, last 180 days (created >= 2026-03-28), fetched 2026-09-24 via gh api search/issues

Counts (is:issue is:open, phrase in title or body, total_count as returned):
- "looking for maintainers": 269
- "looking for maintainer": 251 (overlaps the above)
- "seeking maintainers": 40
- "looking for a new maintainer": 20
- "new maintainer wanted": 9
Pooled (first four queries, 100/page, sort=reactions): 261 unique issues in 237 unique repos. After filtering to issues whose TITLE contains maintainer/adopt/deprecate/archive/take-over wording: 96 issues. Most of the raw hits are body-text false positives (e.g., microsoft/vscode, pytorch, grafana). The search API ignores closed issues, so posts already filled or abandoned are excluded.

Top 20 title-filtered issues by repo stars (stars from gh api repos/{o}/{r}; downloads from api.npmjs.org last-month or pypistats.org recent; "not found" = no registry package with the repo name, typically an app, not a library):

| Stars | Issue | Created | Title | Monthly downloads | Lang | Caveat |
|---|---|---|---|---|---|---|
| 24,128 | [Delgan/loguru](https://github.com/Delgan/loguru/issues/1492) | 2026-07-03 | Looking for more maintainers? | pypi loguru: 64,877,404/mo | Python | asked by a user, not the maintainer |
| 8,980 | [kubernetes/autoscaler](https://github.com/kubernetes/autoscaler/issues/9675) | 2026-05-21 | Addon-resizer looking for a maintainer, is considered for deprecation | (Go) n/a | Go |  |
| 8,285 | [tinyauthapp/tinyauth](https://github.com/tinyauthapp/tinyauth/issues/755) | 2026-04-02 | Tinyauth is looking for more maintainers | (Go) n/a | Go |  |
| 7,722 | [Axorax/awesome-free-apps](https://github.com/Axorax/awesome-free-apps/issues/127) | 2026-04-21 | ‼️ Looking for maintainers / help ‼️ | no package.json name | JavaScript |  |
| 5,490 | [tobychui/zoraxy](https://github.com/tobychui/zoraxy/issues/1174) | 2026-05-13 | Looking for a new Docker maintainer | no package.json name | HTML |  |
| 4,022 | [clauderic/react-infinite-calendar](https://github.com/clauderic/react-infinite-calendar/issues/260) | 2026-07-30 | Is the maintainer opportunity for React Infinite Calendar still open? | npm react-infinite-calendar: 25,964/mo | JavaScript | asked by an applicant; repo last push 2024-06-29 |
| 2,953 | [spliit-app/spliit](https://github.com/spliit-app/spliit/issues/542) | 2026-08-08 | Would you like to become a Spliit maintainer? | npm spliit2: not found | TypeScript |  |
| 2,160 | [Rongronggg9/RSS-to-Telegram-Bot](https://github.com/Rongronggg9/RSS-to-Telegram-Bot/issues/747) | 2026-04-14 | Call for New Maintainers | pypi RSS-to-Telegram-Bot: not found | Python |  |
| 2,142 | [amll-dev/applemusic-like-lyrics](https://github.com/amll-dev/applemusic-like-lyrics/issues/597) | 2026-08-25 | 招募维护者 / Looking for Maintainers | npm applemusic-like-lyrics: not found | TypeScript |  |
| 1,771 | [Netflix/lemur](https://github.com/Netflix/lemur/issues/5427) | 2026-04-21 | Looking for a New Maintainer | pypi lemur: 421/mo | Python | opened by a non-Netflix user |
| 1,683 | [tickernelz/opencode-mem](https://github.com/tickernelz/opencode-mem/issues/79) | 2026-04-01 | [Maintainer Wanted] New Leadership Needed for opencode-mem | npm opencode-mem: 8,427/mo | TypeScript |  |
| 1,379 | [LargeModGames/spotatui](https://github.com/LargeModGames/spotatui/issues/340) | 2026-07-05 | Looking for co-maintainers | (Rust) n/a | Rust |  |
| 1,244 | [HemmeligOrg/Hemmelig.app](https://github.com/HemmeligOrg/Hemmelig.app/issues/536) | 2026-05-15 | Looking for maintainers | npm hemmelig-app: not found | TypeScript |  |
| 1,225 | [conan-io/conan-center-index](https://github.com/conan-io/conan-center-index/issues/30324) | 2026-06-04 | [question] Is Conan seeking/accepting community maintainers for PR rev | pypi conan-center-index: not found | Python | question by a user |
| 1,007 | [nartc/mapper](https://github.com/nartc/mapper/issues/631) | 2026-06-22 | Proposal: Add maintainers to the project | npm mapper: 52/mo | TypeScript | proposal by a contributor |
| 932 | [angular-split/angular-split](https://github.com/angular-split/angular-split/issues/537) | 2026-07-12 | Call for Maintainers: Keeping `angular-split` future-proof | npm angular-split: 434,392/mo | TypeScript |  |
| 881 | [ManiMatter/decluttarr](https://github.com/ManiMatter/decluttarr/issues/344) | 2026-04-18 | [ 🚨 Pinned 🚨]: LOOKING FOR MAINTAINERS / CONTRIBUTORS to triage issues | pypi decluttarr: not found | Python |  |
| 852 | [python-poetry/tomlkit](https://github.com/python-poetry/tomlkit/issues/574) | 2026-07-28 | Looking for a co-maintainer | pypi tomlkit: 443,923,094/mo | Python |  |
| 723 | [ishikota/PyPokerEngine](https://github.com/ishikota/PyPokerEngine/issues/84) | 2026-06-17 | Looking for Maintainers / Contributors from Modern Poker AI Community | pypi PyPokerEngine: 592/mo | Python |  |
| 693 | [nodejs/TSC](https://github.com/nodejs/TSC/issues/1853) | 2026-04-29 | Proposal: Core subsystem Code Owner teams + Collaborator → Maintainer | npm tsc: 2,950,635/mo | JavaScript | governance proposal, not a vacancy |
Caveats on the table: "npm tsc" (nodejs/TSC) and "npm mapper" (nartc/mapper, real package is @automapper/*) are name collisions, not the repo's package. Of the 20, only 4 are library packages with meaningful download volume where the maintainer themself is recruiting: python-poetry/tomlkit (443.9M/mo, "Looking for a co-maintainer", opened by maintainer frostming), angular-split (434k/mo, opened by maintainer Jefiozie), opencode-mem (8.4k/mo), react-infinite-calendar (26k/mo, but the repo's last push is 2024-06-29 and the issue is from an applicant, so the owner may be unreachable). The rest are self-hosted apps, Go/Rust binaries, or awesome-lists that have no registry income path.

What this measures: supply of vacancies is roughly 100-270 per 180 days across all of GitHub; the number that are (a) library packages with enterprise usage and (b) posted by a reachable owner is on the order of 5-10 per 180 days. None of the 20 issues mentions payment.

## 7. Comparables with published numbers

| Person | Mechanism | Published number (verbatim) | Source, date |
|---|---|---|---|
| Filippo Valsorda (Geomys) | Annual retainers with companies for maintenance of Go crypto projects; no hourly, no deliverables | "I now have six amazing clients, and I'm making an amount of money equivalent to my Google total compensation package" ... "All tiers are in the five-figures range (USD, yearly)." ... "After spending the past four months recruiting clients" | https://words.filippo.io/full-time-maintainer/ (2023-02-02) |
| Filippo Valsorda (Geomys, firm) | Portfolio retainer; Associate Maintainers get revenue share | "I have signed four more major clients, and lost only one." ... "Clients still pay a fixed monthly retainer to ensure the professional maintenance of the whole portfolio" ... "Associate Maintainers get a stable, guaranteed income—significantly higher than what GitHub Sponsors generates—and a cut of future retainer revenue growth. There's no formula, we negotiate" ... "We'll grow slowly and organically, by recruiting Associate Maintainers when it makes sense" | https://words.filippo.io/geomys/ (2024-07-08) |
| Filippo Valsorda (thesis post) | Invoice an LLC, not donations | "When is the last time you've seen a GitHub Sponsors recipient making more than $1,000/month?" ... "no company pays their law firm on Patreon" ... "you can easily incorporate a pass-through US LLC and open a business account for it even if you're not a US citizen" | https://words.filippo.io/professional-maintainers/ (2021-12-11) |
| Caleb Porzio | Sponsorware (gate a package behind sponsorship until N sponsors) | "Before the email went out, I had 23 sponsors and was making $573/mo from GitHub Sponsors." ... "By the next evening, I hit 75 sponsors and was now making $1560/mo" ... "I've since grown to 101 sponsors and am generating $2633/mo" | https://calebporzio.com/sponsorware |
| Caleb Porzio | Sponsors-only screencasts + $14/mo tier | "I've grown my annual GitHub sponsors revenue to $112,680/yr." ... "535 people to give me at least $14/mo." ... "Here's exactly what I did that took me from ~$40k to >$100k in ~3 months" | https://calebporzio.com/i-just-hit-dollar-100000yr-on-github-sponsors-heres-how-i-did-it (page date printed as "January 11th, 2019") |
| Caleb Porzio | Cumulative | "As of this morning, I've made over a million dollars on GitHub sponsors." ... "Within 2 years I had made a GitHub sponsors account and ramped it up to $100k/yr." ... PayPal cutoff: "The number was around $4k/mo." | https://calebporzio.com/i-just-cracked-1-million-on-github-sponsors-heres-my-playbook |
| Evan You (Vue, early) | Patreon monthly pledges | Patreon page JSON fields: 2016-09-14 snapshot "patron_count": 105, "pledge_sum": 704611 (Patreon reports cents, i.e. $7,046/month); 2017-06-03 snapshot "patron_count": 153, "pledge_sum": 1013221 ($10,132/month). | Wayback captures of https://www.patreon.com/evanyou (measured from archived page data) |
| Sindre Sorhus | GitHub Sponsors | Sponsors page shows "2 billion downloads a month" and "Current sponsors 189" (public count only; income not published, unverified) | https://github.com/sponsors/sindresorhus (fetched 2026-09-24) |
| Feross Aboukhadijeh | Post-install terminal ads (funding experiment, 2019) | Ended after ~1 week: "Since it seems clear this isn't going to be the solution that saves us all, I'm ending the experiment. (In fact, it's already been paused since Saturday when the initial two sponsors backed out.)" Dollar amounts: not on the recap page; unverified. | https://feross.org/funding-experiment-recap/ (2019-08-28) |
| Anthony Fu | GitHub Sponsors + Open Collective, forwards to dependencies | No personal income figure published in fetched posts; the ecosystem fund page lists individual forwarded grants of "$150", "$250", "$300", "$500" per recipient. Tax note: "the tax I have to pay here in France is roughly 41%". Open Collective page blocked (403 Cloudflare); totals unverified. | https://antfu.me/posts/sponsorship-forwarding ; https://antfu.me/posts/ecosystem-sponsorship-forwarding |

Common pattern: every comparable with a number above $1k/month either (a) sold a retainer/invoice to companies from a pre-existing network (Valsorda: "companies ... that I could reach through my network"), or (b) sold gated content/screencasts (Porzio), or (c) had a top-of-funnel framework with 100k+ users (You). None got there by adopting someone else's package.

## Ranking: money reachable in 90 days for a NEW maintainer (no prior audience, no registry ownership today)

| Rank | Mechanism | Money reachable by day 90 | Probability of >$0 in 90 days | Why |
|---|---|---|---|---|
| 1 | Become co-maintainer with npm/PyPI publish rights on a package already inside enterprise SBOMs, then apply to Tidelift as a lifter (or have the existing lifter split income) | Unknown per-package; Tidelift says "some maintainers six figure incomes" but publishes no distribution; realistic first payout unknown. Lag: publish rights + "3-5 business days" approval + monthly cycle ("third business day of the month") | Low (est. 5-10%): requires an owner to grant rights (the only npm route, since npm "does not transfer package ... ownership simply because another user wants the name"), the package must already be used by Tidelift subscribers, and Tidelift's 2026 intake status is unverified | Only mechanism that pays for maintenance itself, monthly, without selling |
| 2 | HeroDevs Open Source Sustainability Fund grant | "$2,500 to $15,000" (FAQ) or up to "$250,000" (press release) | Low (est. 5%): requires "maintainer of open-source projects" with "strong community adoption and traction" and EOL versions; review pipeline timing unpublished; it is a grant after best-practices work, so cash likely lands after 90 days | One application form, no sales |
| 3 | Direct retainer (Valsorda model) sold to companies that depend on a package you now co-maintain | "five-figures range (USD, yearly)" per client if it closes | Very low in 90 days for a new maintainer (est. 2-5%): Valsorda took "four months recruiting clients" with a Google-cryptography reputation and existing network | Highest ceiling, slowest and most reputation-dependent |
| 4 | GitHub Sponsors / Open Collective on an adopted package | Typically under $1,000/month (Valsorda: "When is the last time you've seen a GitHub Sponsors recipient making more than $1,000/month?"); Porzio's $573/mo baseline came with a Laravel audience | Medium for >$0 (est. 20-30%), very low for >$500/mo | Fastest to set up, lowest yield |
| 5 | thanks.dev dependency distribution | Unpublished; unverified | Very low | Passive, tied to donors scanning trees; no adoption route |
| 6 | PyPI PEP 541 name takeover then monetize | $0 within 90 days: six weeks of contact attempts plus admin queue precede ownership; then any of the above | Near zero for money in 90 days | Legal succession path exists on PyPI only; npm has none |

Bottom line for the operator (theluckystrike): the succession route does not produce a paying client in 90 days on its own. Its only near-term cash path is the Tidelift income share, which needs an existing owner to add you (the merge history shows 56-66% PR acceptance in small repos, so obtaining `npm owner add` on a sub-1k-star package is plausible, but those packages are rarely inside enterprise SBOMs). The best use of this route is as a credential builder: co-maintainer status on a package like tomlkit (443.9M downloads/mo, maintainer openly asking for a co-maintainer on 2026-07-28) or angular-split (434k/mo, "Call for Maintainers" 2026-07-12) is the kind of "legibly and recognizably experts" signal Valsorda says retainers are sold on. Treat it as a 6-12 month asset, not a 90-day revenue line.

## Sources

| URL | Supports | Quoted text | Fetched |
|---|---|---|---|
| https://www.sonarsource.com/open-source-maintainers/ (redirect target of https://tidelift.com/about/lifter) | Tidelift intake still live | "See if your package is eligible for income by finding your package:" | 2026-09-24 |
| https://support.tidelift.com/hc/en-us/articles/4406294816916-How-we-pay-lifters (Wayback 2025-03-01; live URL returns 403) | Payment formula | "On the third business day of the month, we analyze the uploaded SBOMs ... to allocate the income for packages they use." | 2026-09-24 |
| https://support.tidelift.com/hc/en-us/articles/13652028594580-Getting-started-with-lifting (Wayback 2025-10-16) | Application steps, publish rights | "we will process your request within 3-5 business days." | 2026-09-24 |
| https://support.tidelift.com/hc/en-us/articles/4406294842772-What-is-lifting (Wayback 2025-06) | Lifter tasks | "'Lifting' a package means agreeing to take ownership of these responsibilities." | 2026-09-24 |
| https://www.sonarsource.com/blog/xz-tidelift-and-paying-the-maintainers/ (April 2, 2024) | Succession precedent, six-figure claim | "We've done this, for example, with SockJS and minimist." | 2026-09-24 |
| https://www.sonarsource.com/blog/paying-maintainers-the-howto/ (April 15, 2023) | Pay-the-maintainer-not-helpers policy | "it's important to pay, as much as possible, the actual maintainers, not people who say they'll help out." | 2026-09-24 |
| https://www.sonarsource.com/company/press-releases/sonar-to-acquire-tidelift/ | Acquisition continuity | "there are no immediate planned changes to the current Tidelift product." | 2026-09-24 |
| https://www.herodevs.com/sustainability-fund | Fund eligibility and amount | "Grants range from $2,500 to $15,000." | 2026-09-24 |
| https://www.herodevs.com/blog-posts/herodevs-launches-20-million-sustainability-fund-for-open-source-creators-to-secure-end-of-life-software (June 23, 2025) | Fund range, past donations | "Accepted applicants ... will receive between $2,500 and $250,000 in donations." / "Since 2021, HeroDevs has donated over $4 million" | 2026-09-24 |
| https://www.herodevs.com/become-a-partner | APEX partner program is reseller-oriented | "earning 10% of first-year ACV when the deal closes through distribution." | 2026-09-24 |
| https://www.herodevs.com/blog-posts/herodevs-joins-openjs-foundations-ecosystem-sustainability-program-as-first-partner (May 21, 2024) | NES revenue share to foundation | "HeroDevs will donate a portion of all proceeds from the sale of its services to the OpenJS Foundation" | 2026-09-24 |
| https://thanks.dev/ (meta description; subpages 403) | thanks.dev purpose | "Maintainers can also register their projects to become eligible for funding." | 2026-09-24 |
| https://github.com/thnxdev/thanks (README via gh api) | Supported manifests | "--type (go.list,pom.xml,package.json) [required]" | 2026-09-24 |
| https://github.com/thnxdev/issues (issues via gh api) | Ops signal | "#20 2025-10-28 api.thanks.dev SSL certificate expired on October 27th" | 2026-09-24 |
| https://arxiv.org/abs/2112.10165 and https://arxiv.org/pdf/2112.10165 | npm inactivity rates | "We found 58.7% of packages and 44.3% of maintainers are inactive in the npm registry." | 2026-09-24 |
| https://www.blackduck.com/resources/analyst-reports/open-source-security-risk-analysis.html (OSSRA 2026) | Zombie components | "Ninety-three percent of the codebases we audited contain components with no development activity in over two years." / "947 codebases submitted to Black Duck between November 2024 and October 2025" | 2026-09-24 |
| https://www.sonarsource.com/the-2024-tidelift-maintainer-impact-report.pdf | Survey n and pay/quit rates | "n=437 (2024); n=326 (2023)" / "Sixty percent of maintainers report they are unpaid hobbyists" / "22% Yes, I have quit" | 2026-09-24 |
| https://www.sonatype.com/state-of-the-software-supply-chain/2024/introduction | Un-upgraded dependencies | "80% of application dependencies remain un-upgraded for over a year" | 2026-09-24 |
| https://www.sonatype.com/state-of-the-software-supply-chain/2026/software-infrastructure-growth | Abandoned packages (no n) | "It's driven by transitive dependency sprawl, unused or abandoned packages, and unsustainable tooling patterns." | 2026-09-24 |
| https://packages.ecosyste.ms/api/v1/registries/pypi.org | Registry counts | "packages_count":937127 ... "funded_packages_count":60629 | 2026-09-24 |
| https://docs.npmjs.com/policies/disputes | No abandonment transfer on npm | "We do not transfer package, organization, or username ownership simply because another user wants the name." | 2026-09-24 |
| https://peps.python.org/pep-0541/ | PyPI abandonment and transfer criteria | "no releases within the past twelve months" / "The maintainers stop trying to reach the user after six weeks." | 2026-09-24 |
| gh api search/issues (queries listed in section 6) | Vacancy counts | total_count 269 / 40 / 9 / 20 | 2026-09-24 |
| https://pypistats.org/api/packages/tomlkit/recent ; /loguru/recent ; https://api.npmjs.org/downloads/point/last-month/angular-split | Downloads | "last_month":443923094 ; "last_month":64877404 ; 434,392 | 2026-09-24 |
| https://words.filippo.io/full-time-maintainer/ (2023-02-02) | Retainer numbers | "I now have six amazing clients" / "All tiers are in the five-figures range (USD, yearly)." | 2026-09-24 |
| https://words.filippo.io/geomys/ (2024-07-08) | Firm model, associates | "I have signed four more major clients, and lost only one." | 2026-09-24 |
| https://words.filippo.io/professional-maintainers/ (2021-12-11) | Sponsors ceiling | "When is the last time you've seen a GitHub Sponsors recipient making more than $1,000/month?" | 2026-09-24 |
| https://calebporzio.com/sponsorware | Sponsorware numbers | "from $573 to $1560" | 2026-09-24 |
| https://calebporzio.com/i-just-hit-dollar-100000yr-on-github-sponsors-heres-how-i-did-it | $112k/yr | "I've grown my annual GitHub sponsors revenue to $112,680/yr." | 2026-09-24 |
| https://calebporzio.com/i-just-cracked-1-million-on-github-sponsors-heres-my-playbook | Cumulative $1M | "I've made over a million dollars on GitHub sponsors." | 2026-09-24 |
| Wayback https://www.patreon.com/evanyou (2016-09-14, 2017-06-03) | Early Vue Patreon | "patron_count": 105 / "pledge_sum": 704611 ; "patron_count": 153 / "pledge_sum": 1013221 | 2026-09-24 |
| https://github.com/sponsors/sindresorhus | Sponsor count only | "Current sponsors 189" | 2026-09-24 |
| https://feross.org/funding-experiment-recap/ (2019-08-28) | Experiment ended | "I'm ending the experiment." | 2026-09-24 |
| https://antfu.me/posts/sponsorship-forwarding ; https://antfu.me/posts/ecosystem-sponsorship-forwarding | Forwarding model, no income figure | "the tax I have to pay here in France is roughly 41%" | 2026-09-24 |

Unverified / not fetchable: Tidelift all-time payout total and 2026 approval status; HeroDevs number of grants awarded and NES revenue-share percentage; thanks.dev payout data; Black Duck OSSRA 2025 (Feb 2025) exact percentage; Sonatype 2025-edition abandonment percentage; Sindre Sorhus, Feross, Anthony Fu income figures; PEP 541 queue length. WebSearch was unavailable in this session (budget exhausted), so all sources were fetched directly.
