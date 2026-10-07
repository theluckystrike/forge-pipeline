# w40 gate — theluckystrike/just-bash fix/just-bash-sed-extended-address

HELD; no upstream issue; `sed -E` / `-r` address regexes.
Raw prefix: w40-jb-sedext (all in s6/raw/). Collected 2026-10-07T14:07Z.

Rows (branch SHA | ahead/behind | merge-tree main | #550 | #551 | #546 | new upstream hits | #550 review | #551 review):

| branch SHA | ahead/behind | mt main | #550 | #551 | #546 | new hits | #550 rev | #551 rev |
|---|---|---|---|---|---|---|---|---|
| 1097bcc0883f | 1/0 | clean | clean | clean | clean | 0 | 0 | 0 |

Cell evidence (grep lines pasted from raws):

- branch SHA — `python3 -c` on w40-jb-sedext-140712-branch.json → `head 1097bcc0883f`
- ahead/behind — `grep -o '"ahead_by": *[0-9]*\|"behind_by": *[0-9]*' w40-jb-sedext-140712-compare.json` → `"ahead_by":1` `"behind_by":0`
- mt main — `grep -c CONFLICT w40-jb-sedext-140712-mergetree-main.txt` → `0`
- #550 — `grep -c CONFLICT w40-jb-sedext-140712-mergetree-550.txt` → `0`
- #551 — `grep -c CONFLICT w40-jb-sedext-140712-mergetree-551.txt` → `0`
- #546 — `grep -c CONFLICT w40-jb-sedext-140712-mergetree-546.txt` → `0`
- new hits — `python3 -c ... w40-jb-sedext-140712-newhits.json` → `new prs 0`; `... newissues.json` → `new issues 0`
- #550 review — `grep '"total_count"' w40-jb-sedext-140712-reviews-550.json` → `[]` (len 0)
- #551 review — same file pattern for 551 → `[]` (len 0)

METHOD 1-5 keyword searches (raws, grep-found):

- "sed -E": w40-jb-sedext-140712-search-sedE-issues.txt (0 issues) and w40-jb-sedext-140712-search-sedE.txt → 1 hit: `407  open  feat(regex): pluggable engine behind UserRegex via BashOptions.regexEngine` (unrelated engine slot, not address regexes)
- "sed address": w40-jb-sedext-140712-search-sedaddr.txt → 1 hit: `496  open  sed: n and p output out of order (p;s,.*/,,;n)` (n/p ordering, not addresses)

No PR exists upstream for this branch (`gh api search/issues q=sed-extended-address` → `total 0` — w40-jb-sedext-140712-prsearch.json). No first maintainer review on #550/#551 (both review files empty). Branch still clean vs main and vs both sibling PRs, no #546 overlap.

Verdict: HOLD (no first maintainer review on #550/#551; branch clean vs main, #550, #551, and #546; no new upstream hits; no PR opened for this branch yet)
