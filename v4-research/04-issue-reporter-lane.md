# 04. Company-affiliated issue reporter lane: measured with GitHub data

Date of measurement: 2026-09-24 (18 repo samples fetched earlier the same day by the previous run, file mtimes 20:46-20:50 machine-local time; cal.diy and vendurehq samples and all 1058 author profiles fetched 16:20-17:30 UTC). Account used: gh CLI authenticated as theluckystrike. All calls read-only. Budget: $0 (GitHub REST API via gh, core rate limit 5000/h).

## 1. Question

How many open issues in 20 commercial OSS product repos are filed by people who work at a company that deploys the product, and how many of those are actionable as paid-work leads for an external contributor?

## 2. Method (exact commands)

Repos (20): medusajs/medusa, strapi/strapi, n8n-io/n8n, directus/directus, payloadcms/payload, supabase/supabase, RocketChat/Rocket.Chat, mattermost/mattermost, appwrite/appwrite, calcom/cal.com (renamed on GitHub to calcom/cal.diy), langgenius/dify, Infisical/infisical, hoppscotch/hoppscotch, ToolJet/ToolJet, baptisteArno/typebot.io, twentyhq/twenty, formbricks/formbricks, documenso/documenso, saleor/saleor, vendure-ecommerce/vendure (renamed to vendurehq/vendure).

Step 1, issue sample. The task specified `gh api "repos/{o}/{r}/issues?state=open&per_page=100"`. That endpoint mixes PRs into the 100 items (for calcom/cal.diy it returned only 20 real issues out of 100 items, for vendurehq/vendure 41). To get 100 real issues per repo the earlier run used the search endpoint instead, which also returns the exact total of open issues:

```
gh api "search/issues?q=repo:$R+is:issue+is:open&sort=created&order=desc&per_page=100" \
  --jq '{total:.total_count, items:[.items[] | select(.pull_request == null) | {repo, number, html_url, title, created_at, updated_at, author_association, comments, login:.user.login, user_type:.user.type, labels:[.labels[].name], body:(.body // "")}]}' > issues/{o}_{r}.json
```
Sample = the 100 most recently created open issues (all open issues where the repo has fewer than 100). Files: `r/issues/*.json` (script `r/fetch_issues2.sh`; cal.diy and vendurehq refetched under the new names on 2026-09-24 ~16:40 UTC, stored at the old file names).

Step 2, author profiles. Unique human authors per repo in order of appearance, capped at 60 per repo (script `r/fetch_users.sh`, `r/fetch_users2.sh`):
```
gh api users/$LOGIN --jq '{login, name, company, blog, email, bio, location, hireable, public_repos, followers, created_at, type}' > users/$LOGIN.json
```
1058 profiles fetched, 0 errors, 2 s pause every 10 calls. Authors beyond the per-repo cap are counted as "unfetched" (230 issues).

Step 3, classification (script `r/analyze.py`, run against the saved JSON):
- maintainer: `author_association` in MEMBER, OWNER, COLLABORATOR.
- vendor staff: not a maintainer by association, but `company` field or email domain names the vendor (e.g. company "@saleor" on saleor/saleor). Added after the first pass showed 32 such issues; they are not external leads.
- operator: login theluckystrike (13 sampled issues are the operator's own locale-parity issues in medusa and hoppscotch). Excluded from leads.
- company-affiliated external: `company` field non-empty, OR `blog` is a domain that is not a code host, social network, or personal page (regex list in analyze.py, plus the login/name not appearing in the host), OR `bio` matches `CTO|CEO|COO|founder|co-founder|engineer at|developer at|engineer @|developer @|working at|work at|lead at|architect at|head of`.
- anonymous: profile fetched, none of the above.
- Deployer phrases, case-insensitive, in title+body: "in production", "our company", "we use", "our team", "self-hosted", "self hosted", "enterprise", "our customers", "our store", "our instance". A second, stricter metric ("strong first-person phrase") drops "self-hosted", "self hosted" and "enterprise", because those three are issue-template dropdown values in 6 of the repos (see caveat 1).
- Age = days between created_at and 2026-09-24 16:30 UTC. Labels matched case-insensitively on substrings "help wanted"/"help-wanted", "good first issue"/"good-first-issue", "bug".
- Leads = company-affiliated external author AND at least one deployer phrase; ranked strong-phrase first, then company field present, then help-wanted/good-first-issue label, then recency. Top 40 written to `r/04-issue-reporters.csv`.

## 3. Results per repo

n = issues sampled (100 or all open). "open issues (search total)" is GitHub's exact count of open issues excluding PRs at fetch time. Percentages are of n.

| repo | open issues (search total) | sampled | maintainer (assoc.) | vendor staff (company field) | operator (theluckystrike) | company-affil. ext. | anonymous | unfetched/bot | any deployer phrase | strong first-person phrase | median age (d) | help wanted | good first issue | bug label | ext. co-affil. reporters (unique) | leads (co-affil + signal) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| medusajs/medusa | 61 | 61 | 0% | 0 | 7 | 16% | 72% | 0 | 10% | 8% | 17 | 33% | 11% | 89% | 10 | 2 |
| strapi/strapi | 221 | 100 | 7% | 6 | 0 | 24% | 45% | 18 | 13% | 11% | 54 | 0% | 0% | 88% | 18 | 3 |
| n8n-io/n8n | 405 | 100 | 0% | 0 | 0 | 14% | 57% | 29 | 77% | 6% | 11 | 0% | 0% | 0% | 13 | 12 |
| directus/directus | 352 | 100 | 15% | 0 | 0 | 26% | 57% | 2 | 78% | 1% | 110 | 0% | 0% | 55% | 19 | 23 |
| payloadcms/payload | 459 | 100 | 2% | 0 | 0 | 25% | 51% | 22 | 8% | 7% | 31 | 0% | 0% | 45% | 18 | 1 |
| supabase/supabase | 298 | 100 | 1% | 0 | 0 | 13% | 56% | 30 | 9% | 3% | 37 | 1% | 1% | 52% | 13 | 0 |
| RocketChat/Rocket.Chat | 2536 | 100 | 2% | 0 | 0 | 16% | 50% | 32 | 10% | 4% | 31 | 0% | 0% | 72% | 12 | 1 |
| mattermost/mattermost | 607 | 100 | 0% | 2 | 0 | 21% | 42% | 35 | 12% | 2% | 80 | 0% | 0% | 53% | 19 | 0 |
| appwrite/appwrite | 364 | 100 | 4% | 0 | 0 | 17% | 56% | 23 | 30% | 5% | 96 | 0% | 0% | 2% | 14 | 11 |
| calcom/cal.diy | 1135 | 100 | 1% | 0 | 0 | 22% | 65% | 12 | 16% | 5% | 52 | 0% | 0% | 38% | 19 | 6 |
| langgenius/dify | 415 | 100 | 3% | 4 | 0 | 17% | 67% | 9 | 60% | 1% | 7 | 0% | 0% | 27% | 10 | 10 |
| Infisical/infisical | 262 | 100 | 1% | 0 | 0 | 23% | 53% | 23 | 50% | 1% | 130 | 0% | 0% | 1% | 21 | 15 |
| hoppscotch/hoppscotch | 585 | 100 | 0% | 0 | 6 | 23% | 51% | 20 | 33% | 0% | 72 | 0% | 0% | 44% | 22 | 9 |
| ToolJet/ToolJet | 558 | 100 | 54% | 1 | 0 | 10% | 35% | 0 | 2% | 0% | 78 | 0% | 1% | 49% | 7 | 0 |
| baptisteArno/typebot.io | 15 | 15 | 33% | 0 | 0 | 27% | 40% | 0 | 27% | 0% | 83 | 0% | 7% | 60% | 3 | 1 |
| twentyhq/twenty | 58 | 58 | 9% | 0 | 0 | 19% | 72% | 0 | 31% | 3% | 37 | 0% | 0% | 19% | 10 | 1 |
| formbricks/formbricks | 164 | 100 | 8% | 8 | 0 | 29% | 45% | 10 | 21% | 1% | 352 | 0% | 0% | 51% | 22 | 4 |
| documenso/documenso | 132 | 100 | 3% | 0 | 0 | 24% | 65% | 8 | 23% | 3% | 42 | 0% | 0% | 4% | 18 | 10 |
| saleor/saleor | 195 | 100 | 13% | 11 | 0 | 18% | 56% | 2 | 2% | 1% | 899 | 4% | 3% | 47% | 16 | 0 |
| vendurehq/vendure | 172 | 100 | 26% | 0 | 0 | 35% | 38% | 1 | 9% | 7% | 226 | 0% | 0% | 50% | 20 | 4 |
| **ALL** | | 1834 | 8% | 32 | 13 | 21% | 53% | 276 | 26% | 4% | 55 | 1% | 1% | 41% | 295 | 113 |

Reading the ALL row: of 1834 sampled open issues, 8% are filed by maintainers by association, 32 by vendor staff identified via company field, 13 by the operator himself, 21% (382 issues, 295 unique logins) by externally company-affiliated accounts, 53% by accounts with no company signal, and 276 by unfetched or bot accounts. 26% contain any deployer phrase, but only 4% (73 issues) contain a strong first-person phrase. Only 1% carry help wanted and 1% good first issue. 41% carry a bug label. Median age 55 days. 395 of 1834 (22%) have zero comments.

Other measured facts from the same sample:
- Strong first-person phrases by author class: company-affiliated 20 issues, anonymous 35, maintainer 2. So a company field is present on only 20 of 57 external issues that say "in production"/"we use"/"our ...".
- Company field is non-empty on 317 of 1058 fetched profiles (30%).
- 99 of 1834 issue bodies mention an AI tool or agent (regex: claude|codex|copilot|chatgpt|cursor|ai agent|generated by ai|ai-assisted|opencode|verified by a real human|llm); n8n 21, dify 20, twenty 11. 90 of 1058 author accounts were created in 2026. Three logins look like agent accounts (truecourse-agent, cawil-ai, smitxdhruv-AI); truecourse-agent (created 2026-08-19, company "TrueCourse") filed 10 sampled issues and is lead #10 below.
- Vendor staff not caught by author_association (company field names the vendor): saleor 11 issues, formbricks 8, strapi 6, dify 4, mattermost 2, ToolJet 1.

## 4. Top 40 leads (company-affiliated external reporter with a deployer phrase)

Ranks 1-20 have a strong first-person phrase ("in production", "we use", "our team", "our instance"). Ranks 21-40 only match "self-hosted"/"enterprise", which in most cases is an issue-template field value, not prose. Quoted context is verbatim from the issue body around the first matched phrase. CSV with company field, blog, bio, labels and comment count: `r/04-issue-reporters.csv`.

| # | repo | issue | author | company field | phrase(s) | age d | quoted context |
|---|---|---|---|---|---|---|---|
| 1 | directus/directus | [#28281](https://github.com/directus/directus/issues/28281) | u12206050 | BCC | in production, self-hosted | 1 | "...andbox-license key, however this causes the product_id to change live in production, causing massive outages for a ton of our users "Service Unavailabe" etc.  I..." |
| 2 | strapi/strapi | [#27670](https://github.com/strapi/strapi/issues/27670) | unrevised6419 | @all1ndev | in production | 9 | "...ypeScript toolchain and sources to be present, which is not desirable in production. - **Redundant work.** In CI or scripts that already ran `strapi build`, eve..." |
| 3 | medusajs/medusa | [#16807](https://github.com/medusajs/medusa/issues/16807) | princeparmar | SmartByteLabs | in production | 12 | "...at reference those addresses**, including **completed/paid orders**.  In production we correlated:  1. `DELETE /admin/draft-orders/<draft_id>` from POS/Admin 2...." |
| 4 | appwrite/appwrite | [#13517](https://github.com/appwrite/appwrite/issues/13517) | maciejdudek92 | NEXTLEVEL GROUP | self-hosted, our instance | 16 | "...rallel-max 40 -w '%{http_code}\n' \   / sort / uniq -c ```  Result on our instance, three consecutive runs, two unrelated sites:  ``` 55 200  5 500 ```  To see ..." |
| 5 | strapi/strapi | [#27567](https://github.com/strapi/strapi/issues/27567) | marxtin | @t3n  | in production | 17 | "...serts an additional draft row for every published entry.  This hit us in production during the v4→v5 upgrade. Two pods booted the new image within seconds of ea..." |
| 6 | calcom/cal.diy | [#30044](https://github.com/calcom/cal.diy/issues/30044) | dewet22 | Newton's Tree | in production, self-hosted | 27 | "...so there is nothing at the SMTP layer to alert on either.  I hit this in production on a self-hosted 6.2.0 instance. The trigger was the transient `403 Rate Lim..." |
| 7 | appwrite/appwrite | [#13317](https://github.com/appwrite/appwrite/issues/13317) | imtia33 | @Amplytic-Labs  | our team | 31 | "...u dont want your play slip to be accessible by all the `Employee` in your team. it should be only be you , Hr and owners. so you remove the overall employee cla..." |
| 8 | vendurehq/vendure | [#5166](https://github.com/vendurehq/vendure/issues/5166) | juangadiel | PR3SET | in production | 32 | "...L 17 - Operating System (Windows/macOS/Linux): Linux (Alpine, Docker) in production; Windows 11 for development - Browser (if applicable): N/A — worker process,..." |
| 9 | vendurehq/vendure | [#5165](https://github.com/vendurehq/vendure/issues/5165) | juangadiel | PR3SET | in production | 32 | "... error: Task timed out ```  These two lines repeated every ~5 minutes in production, each one a fresh overlapping execution piling 500ms-interval polling querie..." |
| 10 | documenso/documenso | [#3287](https://github.com/documenso/documenso/issues/3287) | truecourse-agent | TrueCourse | in production, self-hosted | 34 | "...mentStatus.PENDING)`.  The single writer of `DocumentStatus.REJECTED` in production code is `packages/lib/jobs/definitions/internal/seal-document.handler.ts`, w..." |
| 11 | RocketChat/Rocket.Chat | [#41848](https://github.com/RocketChat/Rocket.Chat/issues/41848) | geekgonecrazy | @atomicdotdev | in production, enterprise | 36 | "...nd is never re-attempted, even after a pod restart.  We observed this in production on a video file (`m.video`) sent over federation. Image (`m.image`) attachme..." |
| 12 | strapi/strapi | [#27011](https://github.com/strapi/strapi/issues/27011) | rubek-joshi | Ottr Technology | in production | 72 | "...I am using cloudinary for my uploads. This is an issue that's created in production but not during development. Initially thought it was just a caching issue bu..." |
| 13 | Infisical/infisical | [#7204](https://github.com/Infisical/infisical/issues/7204) | winkelmeyer | Clera | in production | 78 | "...vs. importing existing ones)?  We're running against this exact limit in production, so understanding the failure mode matters for us before relying on the sync..." |
| 14 | appwrite/appwrite | [#12623](https://github.com/appwrite/appwrite/issues/12623) | nighodev | @Tradoo-AI  | in production, we use, self-hosted | 97 | "... The bug itself was triaged and verified by a real human (encountered in production, reproduced, workarounds tested).  ## 🐛 Describe the bug  On self-hosted App..." |
| 15 | vendurehq/vendure | [#4023](https://github.com/vendurehq/vendure/issues/4023) | goran-zdjelar | Bind Technologies | in production | 294 | "...I'm trying to set up Dashboard in production but it does not work. Am I doing something wrong?  If i run `npx vite` it sp..." |
| 16 | formbricks/formbricks | [#5958](https://github.com/formbricks/formbricks/issues/5958) | noahboegli | @swiss-virtual, Ensemble Hospitalier de la Côte | we use | 471 | "...our feature request related to a problem? Please describe.  Currenlty we use webhooks on the responseFinished event to propagate the response data to other tool..." |
| 17 | vendurehq/vendure | [#3557](https://github.com/vendurehq/vendure/issues/3557) | mschipperheyn | Mobile Minds | we use | 490 | "... them in the promotion onActivate / onDeactivate.   A workaround that we use is reading the request from the `RequestContext` in the promotion side effect and c..." |
| 18 | medusajs/medusa | [#16950](https://github.com/medusajs/medusa/issues/16950) | jabarientergalactic |  | in production | 1 | "...a.customers.map(...) call sites)  We've been running this exact patch in production via patch-package for a few weeks without issues, happy to open a PR if that..." |
| 19 | calcom/cal.diy | [#30193](https://github.com/calcom/cal.diy/issues/30193) | gianpaj |  | in production | 5 | "... re-check them on every upgrade, and a key I miss shows up as English in production. For the 40+ languages you already ship, a language code does the job with n..." |
| 20 | payloadcms/payload | [#18086](https://github.com/payloadcms/payload/issues/18086) | amirtabatabaei69 |  | we use | 22 | "...ecause together they make `payload run` unsafe as a CI or build gate. We used it as a pre-deploy migration gate, and the gate could never have failed.  ### 1. T..." |
| 21 | n8n-io/n8n | [#39444](https://github.com/n8n-io/n8n/issues/39444) | hossam-abdelmajeed | @talabat-dhme  | self-hosted, enterprise | 0 | "...`  ## Debug info  ### core  - n8nVersion: 1.123.6 - platform: docker (self-hosted) - nodeJsVersion: 22.21.0 - nodeEnv: production - database: postgres - executi..." |
| 22 | directus/directus | [#28288](https://github.com/directus/directus/issues/28288) | rizz360 | @cc-cdv-lu  | self-hosted | 0 | "...ectus Version  11.17.4, also checked on 12.4.1  ### Hosting Strategy  Self-Hosted (Docker Image)  ### Database  PostgreSQL 13.8 (repro above on sqlite) ..." |
| 23 | langgenius/dify | [#42909](https://github.com/langgenius/dify/issues/42909) | zyileven | tavan | self hosted | 0 | "...component integration test against commit `4c2f022bb2`.  ### Cloud or Self Hosted  Self Hosted (Source). Verification below uses the source frontend with mocked..." |
| 24 | n8n-io/n8n | [#39329](https://github.com/n8n-io/n8n/issues/39329) | danaharrison | Telus | self-hosted | 1 | "...t-timezone: 0.5.48`). Node.js 26.7.0 (image). PostgreSQL, queue mode, self-hosted (Docker/Kubernetes). ..." |
| 25 | n8n-io/n8n | [#39327](https://github.com/n8n-io/n8n/issues/39327) | huseyincenik | @JohnSnowLabs  | self-hosted | 1 | "...TE_VACUUM_ON_STARTUP)  BODY:  **Describe the bug**  On a long-running self-hosted n8n instance (SQLite, default DB), the `database.sqlite-wal` file grows unboun..." |
| 26 | baptisteArno/typebot.io | [#2609](https://github.com/baptisteArno/typebot.io/issues/2609) | damien-list | Vertical-Mail | self-hosted | 1 | "...  Line 1     Line 2  ### Environment  - Typebot version: `[v3.17.2]` (self-hosted) - Browser: `[Firefox 156]` - OS: `[macOS]`..." |
| 27 | n8n-io/n8n | [#39222](https://github.com/n8n-io/n8n/issues/39222) | xangelix | ??? | self-hosted, self hosted, enterprise | 2 | "...ow-up messages or tool continuations when it uses Kimi Code through **Self-hosted or OpenAI-compatible endpoint**.  The endpoint is `https://api.kimi.ai/coding/..." |
| 28 | directus/directus | [#28272](https://github.com/directus/directus/issues/28272) | u12206050 | BCC | self-hosted | 2 | "...ld you created.  ### Directus Version  v12.3.1  ### Hosting Strategy  Self-Hosted (Custom)  ### Database  Mysql..." |
| 29 | hoppscotch/hoppscotch | [#6665](https://github.com/hoppscotch/hoppscotch/issues/6665) | 07prajwal2000 | Fluxify | self-hosted | 2 | "...assets/8114ddf5-d098-46c0-b40b-207308fc239b" />  ### Deployment Type  Self-hosted (on-prem deployment)  ### Version  v2026.8.1..." |
| 30 | documenso/documenso | [#3383](https://github.com/documenso/documenso/issues/3383) | MeyerOppelt | University of South Dakota | self-hosted | 2 | "...ns it off. There is no size check anywhere in the path.  I run 2.18.0 self-hosted against Oracle Cloud Infrastructure Email Delivery, on the `smtp-auth` transpo..." |
| 31 | appwrite/appwrite | [#13808](https://github.com/appwrite/appwrite/issues/13808) | jbdujardin | EIRL JB DUJARDIN | self-hosted | 3 | "...### 👟 Reproduction steps  1. Run a self-hosted Appwrite 2.2.0 with S3-compatible storage:     ```    _APP_STORAGE_DEVICE=s3  ..." |
| 32 | n8n-io/n8n | [#39123](https://github.com/n8n-io/n8n/issues/39123) | ThomasSanson | https://www.education.gouv.fr/ | self-hosted, enterprise | 5 | "...cli/src/load-nodes-and-credentials.ts  ## Environment  * n8n: 2.36.7 (self-hosted) * Deployment: Docker, queue mode (main + workers) * Node: 24 * Database: Post..." |
| 33 | calcom/cal.diy | [#30195](https://github.com/calcom/cal.diy/issues/30195) | arminpkathrein | Kantara Initiative, Bytepark | self-hosted | 5 | "...ct to the dtstart override.  Technical details  - cal.com **v5.9.10** self-hosted (Docker), commit `9f566bc8fc` - **Node.js v20.20.0** - `ical.js` 1.5.0, `tsdav..." |
| 34 | langgenius/dify | [#42446](https://github.com/langgenius/dify/issues/42446) | agarwalpranav0711 | BML Munjal University | self hosted | 6 | "...he required fields.  ### Dify version  1.0.0-dev (main)  ### Cloud or Self Hosted  Self Hosted (Docker)  ### Steps to reproduce  1. Inspect `DatasetSegmentListA..." |
| 35 | hoppscotch/hoppscotch | [#6656](https://github.com/hoppscotch/hoppscotch/issues/6656) | YTKacperSKY | @calimoto-GmbH | self-hosted | 6 | "...tly because the error returned the exit code 0.  ### Deployment Type  Self-hosted (on-prem deployment)  ### Version  @hoppscotch/cli@0.31.4..." |
| 36 | n8n-io/n8n | [#38882](https://github.com/n8n-io/n8n/issues/38882) | jonico | Postman | self hosted | 7 | "....38.6 Node.js: v26.7.0 Database: SQLite Execution mode: main Hosting: self hosted (Docker image n8nio/n8n:2.38.6) Affected package: frontend/editor-ui Affected ..." |
| 37 | n8n-io/n8n | [#38876](https://github.com/n8n-io/n8n/issues/38876) | RCheesley | @mautic | enterprise | 7 | "...atabase: sqlite - executionMode: regular - concurrency: 20 - license: enterprise (sandbox)  ### storage  - success: all - error: all - progress: false - manual:..." |
| 38 | langgenius/dify | [#42415](https://github.com/langgenius/dify/issues/42415) | L4XB | @sixsentences | self hosted | 7 | "...required fields.  ### Dify version  main (`9c6c48b50b`)  ### Cloud or Self Hosted  Self Hosted (Source)  ### Steps to reproduce  Upload a legacy `.xls` to a kno..." |
| 39 | langgenius/dify | [#42414](https://github.com/langgenius/dify/issues/42414) | L4XB | @sixsentences | self hosted | 7 | "...required fields.  ### Dify version  main (`6a0039812d`)  ### Cloud or Self Hosted  Self Hosted (Source)  ### Steps to reproduce  Upload a `.docx` to a knowledge..." |
| 40 | langgenius/dify | [#42358](https://github.com/langgenius/dify/issues/42358) | L4XB | @sixsentences | self hosted | 8 | "...required fields.  ### Dify version  main (`38f9d85d5a`)  ### Cloud or Self Hosted  Self Hosted (Source)  ### Steps to reproduce  Add a `.docx` to a knowledge ba..." |

Of the 40: 36 distinct authors, 15 repos, 8 issues have zero comments, 20 have a strong phrase. Rank 10 (truecourse-agent) is an agent account and should be treated as a company signal for TrueCourse, not a person. Rank 18-20 have no company field (bio or blog matched).

## 5. AI-PR policy per repo (from CONTRIBUTING.md fetched via `gh api repos/{o}/{r}/contents/CONTRIBUTING.md` on 2026-09-24, files in `r/contrib/*.md`; PR templates in `r/prtmpl/*.md`)

Classes: ban = AI contributions prohibited; disclosure = must or should state AI use; ownership = AI allowed if author understands and owns the code; none = no AI wording found in the file(s) checked.

| repo | policy | verbatim text (file) |
|---|---|---|
| medusajs/medusa | none | No AI wording. Relevant instead: "Our core maintainers prioritize pull requests (PRs) from within our organization. External contributions are regularly triaged, but not at any fixed cadence." (CONTRIBUTING.md) |
| strapi/strapi | none | Only "yarn ai:sync  # link AI skills into your local tool directories" (CONTRIBUTING.md) |
| n8n-io/n8n | disclosure (encouraged) + ownership | "We use AI tools ourselves and we welcome AI-assisted contributions. The problem is not the tool. The problem is code the author cannot stand behind." ... "We encourage you to note in the PR if AI tools did a meaningful part of the work, and which tools. It helps us calibrate review and it is not held against you." ... "AI-assisted features and refactors still need an accepted issue or forum topic first" (CONTRIBUTING.md section "4. Using AI Tools") |
| directus/directus | none found | repo contributing.md: "Please see [our contributing guidelines](https://directus.com/docs/community/contribution/pull-requests)"; that page fetched 2026-09-24, no AI policy text. Repo root has AGENTS.md and .claude/ (not read). |
| payloadcms/payload | none | Section "AI Code Tool Compatibility": "This project includes configuration files for AI-assisted development." No rule on submissions. (CONTRIBUTING.md) |
| supabase/supabase | none | No AI wording (CONTRIBUTING.md) |
| RocketChat/Rocket.Chat | none | No AI wording (CONTRIBUTING.md) |
| mattermost/mattermost | none found | CONTRIBUTING.md points to developers.mattermost.com/contribute/getting-started/ and the handbook page; both fetched 2026-09-24, no AI wording found. |
| appwrite/appwrite | ownership | "Using AI does not lower the bar: you own the pull request, you must follow those standards, and you must review and oversee any agent-generated work against them." (CONTRIBUTING.md) |
| calcom/cal.diy | none | Only: "You can use GitHub Copilot's auto-summarize feature, but make sure to verify it for accuracy and relevance." Also "Keep PRs under 500 lines of code changed and under 10 code files modified" (CONTRIBUTING.md) |
| langgenius/dify | ownership | "AI tools are welcome, but you are responsible for understanding and verifying every change you submit. Describe the problem, your solution, and actual test results in your own words. Unreviewed or repetitive low-quality submissions may be closed." (CONTRIBUTING.md "AI-assisted contributions") |
| Infisical/infisical | none found | CONTRIBUTING.md points to infisical.com/docs/contributing/getting-started/overview; fetched 2026-09-24, no AI policy. PR template has checkbox "Updated CLAUDE.md files (if needed)". |
| hoppscotch/hoppscotch | none | No AI wording (CONTRIBUTING.md, 702 bytes) |
| ToolJet/ToolJet | none | No AI wording (CONTRIBUTING.md); no PR template found |
| baptisteArno/typebot.io | none found | CONTRIBUTING.md: "All the content has been moved [here](https://docs.typebot.io/contribute/overview)"; page fetched 2026-09-24, no AI wording. |
| twentyhq/twenty | none | No AI wording (CONTRIBUTING.md); no PR template found |
| formbricks/formbricks | disclosure (PR template) and community PRs restricted | CONTRIBUTING.md: "For the time being, we don't have the capacity to properly facilitate community contributions ... we've decided to only facilitate community code contributions in rare exceptions in the coming months." PR template: "Delete if no agent was involved. Read both values out of the tool, never from memory" ... "**AI model used** — `<model>`, reasoning effort `<level>`." |
| documenso/documenso | ownership with block threat | "All AI-generated code must be thoroughly reviewed by the contributor before submitting a PR. You are responsible for understanding and validating every line of code you submit. If we detect that contributors are simply throwing AI-generated code over the wall without proper review, they will be blocked from the repository." (CONTRIBUTING.md "AI-Assisted Development with OpenCode") |
| saleor/saleor | none | No AI wording (CONTRIBUTING.md) |
| vendurehq/vendure | none | No AI wording (CONTRIBUTING.md) |

Summary: 0 bans, 2 disclosure (n8n encouraged, formbricks PR-template field), 3 ownership-only (appwrite, dify, documenso), 15 none/none found in the files checked. Nothing here blocks the lane; formbricks and medusa state that external PRs are deprioritized.

## 6. What the numbers say about the lane

Measured facts:
1. Volume of raw candidates: 295 unique externally company-affiliated logins across the 20 repos in a sample of 1834 open issues; 113 issues (from them) match any deployer phrase; 20 match a strong first-person phrase. Per repo the strong-phrase lead count is 0 to 3 in the current 100 newest open issues (n8n 12 and directus 23 "any phrase" leads are template artifacts; their strong counts are 6% and 1% of issues respectively and only a subset of those are company-affiliated).
2. Company field presence: 30% of fetched authors (317/1058). The field is free text ("freelance", university names, "Coffee driven development" all count as non-empty), so 21% "company-affiliated" is an upper bound on employer-identifiable reporters.
3. The lane is mostly bug reports (41% bug-labelled) filed a median 55 days ago, with 22% having zero comments. help wanted / good first issue labels are essentially absent (1% each), i.e. maintainers are not marking these issues as open for external contributors.
4. The operator's own issue traffic is visible in the sample (13 of 1834 issues, 7 of the 61 open medusa issues = 11%). Anyone running the same query on medusa sees the operator as the single largest issue author.
5. AI-agent-filed issues are now part of the population (99 issue bodies mention AI tooling; agent accounts exist), which means a company-affiliated reporter may itself be an agent (lead #10).

What this does not measure (unverified): whether any of the 295 reporters has budget, whether contacting them converts, or whether a fix PR leads to paid work. No conversion rate exists in this data; the lane's conversion probability remains an estimate, not a measurement.

## 7. Caveats

1. Template contamination: "self-hosted"/"self hosted"/"enterprise" are dropdown answers in the issue forms of directus ("Self-Hosted (Docker Image)" appears in 63 of 100 bodies), dify ("### Cloud or Self Hosted" in 52), n8n ("self hosted" in 33, "- license: enterprise (production)" in 13), infisical ("Self-hosted" in 28), hoppscotch ("Self-hosted (on-prem deployment)" in 26), formbricks ("Self-hosted Formbricks" in 15). Counted line frequencies are in this session's log. The "any deployer phrase" column therefore measures deployment type, not employment; use the strong-phrase column for prose signals.
2. Sample is the 100 newest open issues, not a random sample; repos with high issue churn (dify median age 7 d, n8n 11 d) are represented by the last one to two weeks only.
3. 230 issues (13%) have unfetched authors due to the 60-author cap; they are excluded from the class percentages' numerators but included in the denominator, so class percentages are slight underestimates.
4. The company-affiliation heuristic is text-based. It misclassifies universities, "freelance", and AI-agent accounts as company-affiliated, and misses people whose employer appears only on LinkedIn. It was not manually validated beyond the 16 profiles printed for the top leads.
5. author_association is relative to the repo, so vendor employees who post from personal accounts without org membership show as CONTRIBUTOR/NONE; the vendor-staff class catches only those who wrote the vendor name in their company field (32 issues).
6. Search API totals count issues visible to the token; cal.diy and vendurehq totals were fetched after discovering the renames (search returned HTTP 422 for the old names).
7. Percentages rounded to whole numbers; medians in days.

## 8. Files

- `r/issues/{o}_{r}.json` (20 files, raw sample), `r/users/*.json` (1058 profiles), `r/analyze.py`, `r/table_per_repo.md`, `r/leads_table.md`, `r/04-issue-reporters.csv` (top 40), `r/contrib/*.md`, `r/prtmpl/*.md`, `r/repo_meta.txt` (stars and open_issues_count incl. PRs), `r/raw/*.txt` (fetched external contribution pages).

## 9. Sources

| URL | what it supports | quoted text | fetched |
|---|---|---|---|
| https://api.github.com/search/issues?q=repo:{o}/{r}+is:issue+is:open (20 repos, via gh api) | open-issue totals and 100-issue samples per repo | JSON fields total_count, items[].user.login, author_association, created_at, labels, body | 2026-09-24 |
| https://api.github.com/users/{login} (1058 logins, via gh api) | company, blog, bio, email, created_at per author | JSON fields company, blog, bio | 2026-09-24 |
| https://api.github.com/repos/{o}/{r} (20 repos) | stars, rename of calcom/cal.com to calcom/cal.diy and vendure-ecommerce/vendure to vendurehq/vendure | e.g. "calcom/cal.diy stars=48636 open_issues_incl_prs=1435", "vendurehq/vendure stars=8469" | 2026-09-24 |
| https://github.com/directus/directus/issues/28281 | lead #1 | "causes the product_id to change live in production, causing massive outages for a ton of our users" | 2026-09-24 |
| https://github.com/strapi/strapi/issues/27567 | lead #5 | "This hit us in production during the v4→v5 upgrade." | 2026-09-24 |
| https://github.com/calcom/cal.diy/issues/30044 | lead #6 | "I hit this in production on a self-hosted 6.2.0 instance." | 2026-09-24 |
| https://github.com/Infisical/infisical/issues/7204 | lead #13 | "We're running against this exact limit in production" | 2026-09-24 |
| https://github.com/appwrite/appwrite/issues/12623 | lead #14, AI-agent-filed issue marker | "The bug itself was triaged and verified by a real human (encountered in production, reproduced, workarounds tested)." | 2026-09-24 |
| https://github.com/medusajs/medusa/issues/16950 | lead #18 | "We've been running this exact patch in production via patch-package for a few weeks without issues, happy to open a PR if that" | 2026-09-24 |
| https://api.github.com/users/truecourse-agent | agent account among reporters | company "TrueCourse", email "agent@truecourse.dev", created_at "2026-08-19T18:15:50Z" | 2026-09-24 |
| https://api.github.com/users/theluckystrike | operator account identification | company "Zovo", blog "https://zovo.one" | 2026-09-24 |
| https://github.com/medusajs/medusa/blob/develop/CONTRIBUTING.md (via contents API) | medusa AI policy: none; external PR deprioritization | "Our core maintainers prioritize pull requests (PRs) from within our organization." | 2026-09-24 |
| https://github.com/n8n-io/n8n/blob/master/CONTRIBUTING.md (via contents API) | n8n disclosure policy | "We encourage you to note in the PR if AI tools did a meaningful part of the work, and which tools." | 2026-09-24 |
| https://github.com/appwrite/appwrite/blob/main/CONTRIBUTING.md (via contents API) | appwrite ownership policy | "Using AI does not lower the bar: you own the pull request" | 2026-09-24 |
| https://github.com/langgenius/dify/blob/main/CONTRIBUTING.md (via contents API) | dify ownership policy | "AI tools are welcome, but you are responsible for understanding and verifying every change you submit." | 2026-09-24 |
| https://github.com/documenso/documenso/blob/main/CONTRIBUTING.md (via contents API) | documenso ownership/block policy | "If we detect that contributors are simply throwing AI-generated code over the wall without proper review, they will be blocked from the repository." | 2026-09-24 |
| https://github.com/formbricks/formbricks/blob/main/CONTRIBUTING.md and .github/PULL_REQUEST_TEMPLATE.md (via contents API) | formbricks restriction and disclosure field | "we've decided to only facilitate community code contributions in rare exceptions in the coming months." / "**AI model used** — `<model>`, reasoning effort `<level>`." | 2026-09-24 |
| https://github.com/calcom/cal.diy/blob/main/CONTRIBUTING.md (via contents API) | cal.com: no AI policy, PR size limit | "Keep PRs under 500 lines of code changed and under 10 code files modified" | 2026-09-24 |
| https://directus.com/docs/community/contribution/pull-requests | directus external guide, no AI policy | page contains no AI/LLM policy text (grep on fetched text) | 2026-09-24 |
| https://docs.typebot.io/contribute/overview (redirects to docs.typebot.com) | typebot external guide, no AI policy | no AI/LLM policy text (grep on fetched text) | 2026-09-24 |
| https://infisical.com/docs/contributing/getting-started/overview | infisical external guide, no AI policy | no AI/LLM policy text (grep on fetched text) | 2026-09-24 |
| https://developers.mattermost.com/contribute/getting-started/ and https://handbook.mattermost.com/contributors/contributors/guidelines/contribution-guidelines | mattermost external guides, no AI policy | no AI/LLM policy text (grep on fetched text) | 2026-09-24 |
