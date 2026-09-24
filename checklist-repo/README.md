# Codebase licensing checklist

AI labs now pay to license private source code, with its git history, as training and evaluation data. This repo is a checklist a company can work through before it talks to a buyer, plus `estimate.py`, a small script that turns a local checkout into a token count and a rough price.

None of this is legal advice. Every price below is what a buyer publishes on its own site, so treat each one as an estimate, not a quote.

## Who buys and what they publish

The quotes below were checked against the live pages on 24 September 2026.

### HUD

A HUD team member's post on dev.to says frontier labs "pay up to $10k for a qualifying one" and that "it's a license, not a sale", so you keep ownership. The same codebase can be licensed to more than one buyer. Once you accept a lab's request, the post says you're paid within 7 to 14 days. ([dev.to post](https://dev.to/hansel_hud_gtm_guy/would-you-license-an-olddead-startups-codebase-as-ai-training-data-for-up-to-10k-12jc))

HUD's platform guide, dated 24 June 2026, lists its DataVendor product at a "$5,000 baseline per codebase" that "increases with grading", on an "80/20 seller split, with the seller keeping the larger share". ([hud.ai platform guide](https://www.hud.ai/resources/best-platforms-selling-codebase))

A second HUD guide says "each sale grants a non-exclusive license" and that HUD "will not accept repos containing unscrubbed personal data". It also asks that "employee IP assignments should be clean, with no founder or contractor retaining rights". ([hud.ai selling guide](https://www.hud.ai/resources/how-to-sell-startup-assets-model-labs))

### Pangea

Pangea publishes standing indicative rates of $100 per million tokens of source code at head and $40 per million tokens of git history, as the owner's share. ([what labs buy](https://pangea-code-licensing-repo-value.netlify.app/))

Its program page calls one rule "the one hard rule". The code must be private and never have been public. An Internet Archive snapshot of the repo page counts as proof it was public, and making the repo private later doesn't undo that. Forks and code already shipped on npm, PyPI or similar are declined for the same reason. On licenses it says buyers care most about copyleft, "GPL, AGPL and LGPL especially", and that "an undisclosed copyleft dependency can unwind a deal after it has closed". ([program page](https://info-hub-pangea-agencies.netlify.app/))

Pangea also lists the rough numbers buyers screen for, which are 3+ contributors, 100+ commits, 10+ merged pull requests and 10k+ lines of original code. It says these aren't hard gates.

### Turing Project Lazarus

Lazarus buys a company's operating record rather than one repo. That means source, code reviews, tickets, chat threads, wikis and runbooks together. Its page offers "a single payout of up to $1M" and says it's for "operating and winding-down companies". Intake is scheduled within one business day under NDA, and a sampling review usually takes about a week before an offer. ([lazarus.turing.com](https://lazarus.turing.com/))

HUD's platform guide describes Lazarus pricing as $10K to $100K for legacy code and up to $15K for a modern repository.

## Hard eligibility rules

Work down both lists before you send anything. One "no" usually ends it for that repo.

### Where the code came from

- [ ] The code is private and has never been public. That covers a public GitHub or GitLab repo at any point, a public gist, and an Internet Archive snapshot of the repo page.
- [ ] It isn't a fork or a mirror of someone else's project.
- [ ] It was never published as a package on npm, PyPI, crates.io, Maven Central or similar.
- [ ] There's no copyleft code in the tree. No GPL, AGPL, LGPL, MPL or EUPL files vendored in, and no undisclosed copyleft dependencies. `estimate.py` flags declared licenses but doesn't resolve dependencies, so run a real license scanner as well.

### Who owns it and what's in it

- [ ] The company owns all of it. Every employee and contractor signed an IP assignment to the company. No client owns or co-owns it, no NDA restricts it, and nobody is still owed money for writing it.
- [ ] Personal data and secrets are scrubbed from the current tree and from the full git history. Think API keys, credentials, customer records, and real emails in fixtures or seed files.
- [ ] It has a real multi-contributor history. Several people, many commits, and merged pull requests with review, built over months or years. A large repo written by one person in a few weekends is worth far less.

## What to prepare

Buyers ask for roughly the same pack. Having it ready shortens the time from first contact to payout.

Start with the code itself.

- Read-only access to the repos you pick, through a GitHub, GitLab or Bitbucket app scoped to just those repos.
- Full repo exports with the commit history intact.

Then add the context that explains it.

- Ticket exports from Jira or Linear.
- Snapshots of internal docs, runbooks and design notes.
- A one-page context brief per repo that says what the system did, how it scaled and what made it hard.
- A dependency license list, either an SBOM, a lockfile, or a CSV of component, version and license.

## Estimate a price

`estimate.py` uses only the Python standard library.

```
python3 estimate.py <path-to-local-repo> [--history-tokens-from-git] [--exclude DIR ...]
```

It walks the tree and skips dependency and build folders (`node_modules`, `vendor`, `dist`, `build`, `target`, `.git` and similar), lockfiles, license files, minified bundles, and binary or data files such as images, fonts, archives, databases and logs. It sums the bytes left over by extension and divides by 4 to get tokens. Four bytes per token is an approximation. Real tokenizers vary by language and coding style, so treat the result as a rough figure.

With `--history-tokens-from-git` it streams `git log -p` for the repo, with the same folders left out, and converts that byte count at the same ratio. It then prices source at $100 per million tokens and history at $40 per million. You can change both with `--source-rate` and `--history-rate`.

It also scans LICENSE and COPYING files, including ones under `vendor/` and `third_party/`, plus the declared license fields in `package.json`, `composer.json`, `pyproject.toml`, `setup.cfg`, `setup.py`, `Cargo.toml` and gemspecs. Any GPL, AGPL, LGPL, MPL or EUPL string prints a WARN line. It does not look up the licenses of dependencies listed in `package.json`, `pyproject.toml`, `setup.cfg`, requirements files, `Cargo.toml` or `go.mod`.

Exit codes are 0 for a clean run, 2 when a copyleft warning was found, and 1 for bad input.

### Worked example

Here's the script run on 24 September 2026 against the maintainer's own working folder, which isn't a clean single repo.

```
$ python3 estimate.py ~/oss-pipeline --history-tokens-from-git
repo: ~/oss-pipeline
files counted: 11634 (skipped outside excluded dirs: 497)
bytes by extension (top 12):
  .ts            5127 files     46,253,976 bytes
  .html           231 files     43,695,555 bytes
  .json          1259 files     27,880,921 bytes
  .tsx           4057 files     25,894,641 bytes
  .raw              2 files      5,745,576 bytes
  .patch          165 files      1,950,840 bytes
  .txt             54 files        837,295 bytes
  .hdr            396 files        510,230 bytes
  .py             112 files        462,888 bytes
  .md             102 files        416,867 bytes
  .js               2 files        286,975 bytes
  .kt              29 files         85,633 bytes
  (other 14)       98 files        218,182 bytes
source bytes: 154,239,579
source tokens: 38,559,894 (approximate, 4 bytes per token)
history bytes (git log -p): 1,066,632
history tokens: 266,658 (approximate, 4 bytes per token)
price: source $3,855.99 at $100/M + history $10.67 at $40/M = $3,866.66
note: published indicative rates, not a quote; buyers grade and may pay more or less
note: dependency licenses are not resolved; dependencies in package.json, pyproject.toml, setup.cfg, requirements files, Cargo.toml and go.mod are not scanned
result: no copyleft strings found in LICENSE files or declared license fields
$ echo $?
0
```

That $3,866.66 headline is wrong, and the reason is the most common mistake in this whole process. All of those TypeScript bytes are a local mirror of a public open source project, kept in `state/` for other work, and much of the JSON is API data dumps. Public code is worth nothing to these buyers, and data dumps aren't source. The script can't tell provenance from bytes, so you have to leave that out yourself.

```
$ python3 estimate.py ~/oss-pipeline --history-tokens-from-git --exclude state --exclude plan-evidence
repo: ~/oss-pipeline
excluded by --exclude: plan-evidence, state
files counted: 193 (skipped outside excluded dirs: 13)
bytes by extension (top 12):
  .raw              2 files      5,745,576 bytes
  .json           124 files      1,657,317 bytes
  .py              30 files        305,880 bytes
  .html             5 files        124,525 bytes
  .md              21 files         65,489 bytes
  .txt              6 files         25,298 bytes
  .sh               4 files         10,549 bytes
  (none)            1 files          1,648 bytes
source bytes: 7,936,282
source tokens: 1,984,070 (approximate, 4 bytes per token)
history bytes (git log -p): 1,066,632
history tokens: 266,658 (approximate, 4 bytes per token)
price: source $198.41 at $100/M + history $10.67 at $40/M = $209.07
note: published indicative rates, not a quote; buyers grade and may pay more or less
note: dependency licenses are not resolved; dependencies in package.json, pyproject.toml, setup.cfg, requirements files, Cargo.toml and go.mod are not scanned
result: no copyleft strings found in LICENSE files or declared license fields
$ echo $?
0
```

The history line is small for a reason. When this ran, the folder's git repository held a single commit by a single author, made the same day. So the code that's left fails the multi-contributor rule above whatever it scores, and a buyer would grade it that way.

For a sense of scale, a team repo with 30 MB of source and a 120 MB `git log -p` works out to 7.5M source tokens ($750) plus 30M history tokens ($1,200), or $1,950 at the published Pangea rates.

## Tests

```
python3 -m unittest discover -s tests -v
```

The tests build a throwaway repo with known file sizes, a `node_modules` folder that must be skipped, and an AGPL LICENSE that must make the script exit with code 2.

## License

MIT. See [LICENSE](LICENSE).

Maintained by theluckystrike.
