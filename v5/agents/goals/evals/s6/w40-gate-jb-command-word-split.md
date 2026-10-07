# W40 gate: just-bash fix/just-bash-command-word-split (E40-1)

Item: gates one PR at vercel-labs/just-bash fixing #457 (unquoted expansion in command
position not word-split, `$CC -c x.c` with `CC="cc -O2"`). Admin c118 flags: #546 (head
5c90437) conflicts with this branch in interpreter.ts.

Rows (each cell grep-found in its raw, grep lines pasted below):

| branch SHA | ahead/behind | merge-tree main | #550 | #551 | #546 | new upstream hits | #550 review | #551 review |
|---|---|---|---|---|---|---|---|---|
| 6fad01f7e5c0fe2a62253e42da785250c673ac7e | 1 / 0 | CLEAN ab321607181dc0632f5b64ad206a2ca7365a848e | CLEAN 85e5fb0077ca53fc56d83c484cb2e256e847100e | CLEAN 0d99f5fa5db6656aa51f88350d0a1b7467a64a7d | CONFLICT packages/just-bash/src/interpreter/interpreter.ts | total_count 0 (#457 still open, 0 comments; cross-ref #3450 is a private repo, UNRELATED) | none (0 reviews; 2 bot comments only) | none (0 reviews; 2 bot comments only) |

- Compare file list (raw w40-jb-wordsplit-090332-compare2.json): ahead_by 1 behind_by 0,
  merge_base 58d1ecf31b768ea9834e151b166cf4cea32046ba; .changeset/command-word-split.md A
  +5/-0; command-word-splitting.test.ts A +64/-0; interpreter.ts M +9/-2;
  spec-tests/bash/cases/alias.test.sh M +0/-1.
- Branch head commit 2026-10-07T06:18:33Z "fix(interpreter): word-split an unquoted
  expansion in command position" (raw w40-jb-wordsplit-085717-branch.json).
- Upstream main tip = 58d1ecf3 (2026-10-06T15:17:24Z, #439) -> branch is 1 ahead, 0
  behind; nothing new upstream since 06:00Z (search raw total_count 0).
- #546 overlap (raws w40-jb-wordsplit-090322-diff-pr546-interpreter.txt /
  -diff-branch-interpreter.txt): #546 rewrites the assignment/command block
  (@@ -676,405 +677,422 @@ — introduces PrefixBindings and `let commandName = ""`);
  our branch hunks @@ -774,7 +774,8 @@ (expandedName via expandWordWithGlob) and
  @@ -789,6 +790,12 @@ (append remaining split fields as args) sit inside that same
  rewritten region -> textual conflict in packages/just-bash/src/interpreter/interpreter.ts.
- #457 (raw w40-jb-wordsplit-090100-issue457.json + timeline): state open, 0 comments,
  author trieloff; only cross-reference is #3450 (repo fj, "fix(shell): the interop fixes
  zlib and Lua need to build ins", private/fork context) — not a competing fix here.
- Keyword searches (raws w40-jb-wordsplit-090041-search-issues.txt,
  -090050-search-prs.txt): "word split" issues -> #457 (SAME-BUG, the one we fix) and
  expansion PRs #367/#366/#361 (UNRELATED: leading IFS boundaries / indexed params /
  extglob, no command-position splitting); "command position" PRs -> 0 hits. No
  duplicate upstream PR covers this bug.
- Hold condition (raws w40-jb-wordsplit-090117-*): #550 reviews 0, issue comments 2
  (vercel[bot] CONTRIBUTOR 2026-10-07T05:02:09Z, auto-maintain[bot] NONE
  2026-10-07T05:04:42Z — bots only, no first maintainer review); #551 same shape
  (vercel[bot] 05:10:22Z, auto-maintain[bot] 05:11:48Z). pr view: both state OPEN,
  mergedAt null, reviewDecision "", mergeStateStatus BLOCKED. → hold stands for #550/#551;
  this branch is not itself gated on a review, but the wave rule holds the whole set
  until a first maintainer review lands.

grep evidence (cells -> raws):
- 6fad01f7... ← raw/w40-jb-wordsplit-085717-branch.json (head SHA)
- ahead_by 1 behind_by 0 ← raw/w40-jb-wordsplit-090332-compare2.json
- ab321607... ← raw/w40-jb-wordsplit-085836-mergetree-1.txt (re-run against live
  FETCH_HEAD identical: mt-w4 of the first pass)
- 85e5fb00... vs #550 head 8d7eb9a ← raw/w40-jb-wordsplit-090503-mergetree-pr550.txt
  (EXIT=0, clean)
- 0d99f5fa... vs #551 head 39cafbd ← raw/w40-jb-wordsplit-090503-mergetree-pr551.txt
  (EXIT=0, clean)
- vs #546 head 5c90437: CONFLICT — EXIT=1, stage entries for
  packages/just-bash/src/interpreter/interpreter.ts (stages 1/2/3, tree 9fd9e612...)
  in raw/w40-jb-wordsplit-090503-mergetree-pr546.txt; overlapping hunks quoted above
  from the raw diffs
- total_count 0 ← raw/w40-jb-wordsplit-090036-new-work.json
- 0 reviews / bot comments ← raw/w40-jb-wordsplit-090117-reviews-550.json,
  -icomm-550.json, -reviews-551.json, -icomm-551.json; BLOCKED ← -prview-550.json,
  -prview-551.json

Verdict: HOLD (no first maintainer review on #550/#551; branch still clean vs main and
no duplicate; #546 conflict alone would be HOLD with the note: rebase after #546 merges)
