# w40 gate — theluckystrike/just-bash fix/just-bash-sed-bre-alternation-anchor

HELD; no upstream issue; sed twin of #551.
Raw prefix: w40-jb-sedbre (all in s6/raw/). Collected 2026-10-07T14:09Z.

Rows (branch SHA | ahead/behind | merge-tree main | #550 | #551 | #546 | new upstream hits | #550 review | #551 review):

| branch SHA | ahead/behind | mt main | #550 | #551 | #546 | new hits | #550 rev | #551 rev |
|---|---|---|---|---|---|---|---|---|
| 5b3b25e5dd1a | 1/0 | clean | clean | clean | clean | 0 | 0 | 0 |

Cell evidence (grep lines pasted from raws):

- branch SHA — python on w40-jb-sedbre-140918-branch.json → `head 5b3b25e5dd1a`
- ahead/behind — grep on w40-jb-sedbre-140918-compare.json → `"ahead_by":1` `"behind_by":0`
- mt main — `grep -c CONFLICT w40-jb-sedbre-140918-mergetree-main.txt` → `0`
- #550 — `grep -c CONFLICT w40-jb-sedbre-140918-mergetree-550.txt` → `0`
- #551 — `grep -c CONFLICT w40-jb-sedbre-140918-mergetree-551.txt` → `0`
- #546 — `grep -c CONFLICT w40-jb-sedbre-140918-mergetree-546.txt` → `0`
- new hits — python on w40-jb-sedbre-140918-newhits.json → `new prs 0` (search created:>=2026-10-07T06:00:00Z; new issues run at 140712 also 0)
- #550 review — python on w40-jb-sedbre-140918-reviews-550.json → `reviews 550 0`
- #551 review — python on w40-jb-sedbre-140918-reviews-551.json → `reviews 551 0`

METHOD 1-5 keyword searches (raws, grep-found):

- "sed alternation": w40-jb-sedbre-140918-search-sedalt.txt → 0 hits
- "anchor": w40-jb-sedbre-140918-search-anchor-issues.txt → 1 hit: `467  open  grep BRE: $ before \| is literal instead of an end-of-line anchor` (grep-side anchor bug; the sed twin of #551 has no upstream issue — this is the closest hit and is a different command)

No first maintainer review on #550/#551 (both review raws empty). Branch clean vs main, #550, #551, #546. No new upstream hits.

Verdict: HOLD (no first maintainer review on #550/#551; branch clean vs main, #550, #551, and #546; no new upstream hits; no upstream issue for the sed twin)
