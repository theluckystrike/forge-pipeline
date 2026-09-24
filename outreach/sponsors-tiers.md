# GitHub Sponsors tiers for theluckystrike (plan step 0.5)

Owner action. Agents do not publish these through the API.

## Current state (read 2026-09-24)

Command: `gh api graphql -f query='{user(login:"theluckystrike"){hasSponsorsListing sponsorsListing{isPublic activeGoal{title}}}}'`

Result: `hasSponsorsListing: false`, `isPublic: false`, `activeGoal: null`.

The listing exists but is not public (slug `sponsors-theluckystrike`). It already holds four monthly tiers: $3, $10, $25 and $100. Raw output: `state/pitch-evidence/sponsors-state.json` and `state/pitch-evidence/sponsors-tiers-now.json`.

## Tier text to paste

### Tier 1, one-time, $50

Description:

> Repo audit: drift and locale parity report for one repo.
>
> After you sponsor, email mike@zovo.one with the repo URL. Within 3 working days you get a written report covering locale parity per language (missing keys against your source locale), README numbers that no longer match the code, and examples that fail to build. You keep the report whether or not you buy anything else.

### Tier 2, one-time, $500

Description:

> One locale to 100% parity as a merge-ready PR.
>
> Pick one locale file in one repo. I fill every missing key and open a pull request against your repo: LLM translation, placeholder-exact, CI-validated, human spot check on 10% of strings. You review and merge. If the PR fails your CI, I fix it at no charge.

### Tier 3, monthly, $1,500

Description:

> Maintenance retainer: 10 to 15 PRs per month on your repos.
>
> Locale parity kept as new keys land, stale numbers in docs corrected, broken examples fixed. Every change arrives as a pull request you review. Cancel any month from your sponsorship settings.

The existing $3, $10, $25 and $100 monthly tiers can stay. Retiring them is optional.

## Click path to publish

1. Open https://github.com/sponsors/theluckystrike/dashboard (signed in as theluckystrike).
2. In the left menu, choose "Sponsor tiers".
3. Choose "Add a one-time tier". Enter 50 as the amount, paste the Tier 1 description, then choose "Publish tier". GitHub may ask you to save a draft first. If so, save it, then open the draft and publish it.
4. Repeat step 3 with 500 and the Tier 2 description.
5. Choose "Add a monthly tier". Enter 1500 as the amount, paste the Tier 3 description, and publish it.
6. Back on the dashboard overview, finish whatever the checklist still shows as open. Your July notes list three steps: accept the Sponsors agreement, set up the Stripe Connect bank account, and file the W-8BEN tax form. Then submit the profile for approval or publish it.
7. Check it worked: run the command above again. The target is `hasSponsorsListing: true` and `isPublic: true`.

GitHub renames these menu labels from time to time. If a label has changed, look for the tiers section of the Sponsors dashboard.
