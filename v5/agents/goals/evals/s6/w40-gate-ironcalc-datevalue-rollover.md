# w40 gate — IronCalc DATEVALUE rollover (gates the PR for ironcalc/IronCalc#1379)

Raw prefix: w40-ic (all in s6/raw/). Collected 2026-10-07T14:11Z.

## (1) #1485 state + reviews (raw/w40-ic-141118-pr1485.json)

- state MERGED, mergedAt 2026-10-07T12:43:47Z, reviewDecision APPROVED, mergeStateStatus UNKNOWN, headRefOid 523ab79a64aa497c7b9eef5e04c622e5734d6784
- Non-bot reviews quoted:
  - copilot-pull-request-reviewer 2026-10-07T09:37:14Z "<!-- ccr-overview-v2 --> … 🟡 Changes recommended … Quadratic whitespace scanning can stall" (bot)
  - theluckystrike 2026-10-07T09:55:02Z '' (own ack, non-review body empty)
  - nhatcher 2026-10-07T12:43:38Z "LGTM!" ← maintainer review, APPROVED
- comments: 0

## (2) Rollover branch head + stacked check (raw/w40-ic-141118-rollover-commit.json, w40-ic-141118-pr1485-head-commit.json)

- fix/ironcalc-datevalue-rollover head 3fbf6620e92b, parents ['03beb38e3cf2']
- #1485 head 523ab79a64aa, parent e012e1d9705e (matches hint e012e1d9)
- stacked YES/NO: parent of rollover head is 03beb38e3cf2, NOT #1485's headRefOid 523ab79a64aa → stacked NO (branch already re-based/diverged from #1485)

## (3) Compare main...rollover (raw/w40-ic-141118-compare-rollover.json)

- ahead_by 1, behind_by 1, status diverged
- files: base/src/functions/date_and_time.rs modified; base/src/test/mod.rs modified; base/src/test/test_datevalue_rollover.rs added; xlsx/tests/calc_tests/DATE_AND_TIME/DATEVALUE_issue_1379.xlsx added

## (4) #1379 + competing PRs

- raw/w40-ic-141118-issue1379.json: state closed, comments 0, title "DATEVALUE doesn't roll over date when time portion exceeds 2"
- raw/w40-ic-141118-issue1379-timeline.json: closed; cross-referenced #1381 and #1486; referenced commits eb7770b9, 3fbf6620 (our rollover head), 106c587d
- raw/w40-ic-141118-prsearch1379.txt: `1486  DATEVALUE: roll the date over when the time part reaches 24 hours like Excel (#1379)  theluckystrike:fix/ironcalc-datevalue-rollover  MERGED  2026-10-07T12:51:55Z` — our own PR is the #1379 PR, now MERGED (merge completed 14:10:23Z per raw/w40-ic-141118-pr1486.json: "mergedAt":"2026-10-07T14:10:23Z")
- raw/w40-ic-141118-search-datevalue.txt: hits #1443 "fix: VALUE and DATEVALUE read dates and times written as text" (UNRELATED — text parsing, not rollover) and #777 "Fix/issue 761 locale date edit" (UNRELATED). No competing PR.

## Verdict rows

| #1485 state | rollover head | parent | stacked | ahead/behind | #1379 state | competing PR |
| MERGED | 3fbf6620e92b | 03beb38e3cf2 | NO | 1/1 diverged | closed | none |

grep proof: each cell above is grep-found in its raw (state MERGED → pr1485.json; head/parent → rollover-commit.json; ahead 1 behind 1 → compare-rollover.json; closed → issue1379.json; none → search-datevalue.txt).

## Verdict

DROP (https://github.com/ironcalc/IronCalc/pull/1486 — #1379 closed AND our own rollover PR #1486 itself MERGED at 2026-10-07T14:10:23Z moments before this gate ran; maintainer nhatcher approved #1485 with "LGTM!" and merged it at 12:43:47Z, then the stacked rollover landed. Nothing left to gate or open.)
