# w40 gate — theluckystrike/just-bash fix/just-bash-command-stubs-executable

HELD; no upstream issue; `test -x` and `stat -c %a` on command stubs.
Raw prefix: w40-jb-stubs (all in s6/raw/). Collected 2026-10-07T14:05-14:07Z.

| branch SHA | ahead/behind | merge-tree main | #550 | #551 | #546 | new upstream hits | #550 review | #551 review |
|---|---|---|---|---|---|---|---|---|
| f5a1fbf1594c | 1/0 | clean, 0 CONFLICT | open | open | open, conflicted on main | 0 | none | none |

Cell evidence (grep lines from raws):

- branch SHA `f5a1fbf1594c`: raw/w40-jb-stubs-140537-head.json →
  `head f5a1fbf1594c 2026-10-07T06:20:53Z` (python print over the JSON);
  branch.json `raw/w40-jb-stubs-140537-branch.json` also fetched (ls: exists).
- ahead/behind `1/0`: raw/w40-jb-stubs-140537-compare.json →
  `ahead 1 behind 0` (python print); files:
  `.changeset/executable-command-stubs.md added 5 0`,
  `packages/just-bash/src/Bash.ts modified 14 3`,
  `packages/just-bash/src/command-stubs.executable.test.ts added 34 0`,
  `packages/just-bash/src/fs/mountable-fs/mountable-fs.ts modified 13 3`,
  `packages/just-bash/src/fs/overlay-fs/overlay-fs.ts modified 8 3`.
- merge-tree main `clean, 0 CONFLICT`: raw/w40-jb-stubs-140537-mergetree-main.txt →
  `grep -c CONFLICT` printed `0` and `conflicts 0` (merge-tree EXIT=0,
  merge base origin/main in work/jb-gate clone; our branch fetched from the fork
  remote: `* branch fix/just-bash-command-stubs-executable -> FETCH_HEAD`, ours
  `f5a1fbf1594c69a9f10650ac7d0b33d728c2027c`).
- #550 `open`, #551 `open`, #546 `open, conflicted on main`: keyword search
  raw/w40-jb-stubs-140537-search-exec.txt →
  `vercel-labs/just-bash 551 open fix(grep): anchor $ at the end of a BRE alternative
  2026-10-07T05:11:49Z`; #546 state carried from E40-1 raws
  (w40-jb-wordsplit-090332-compare2.json `CONFLICT` row) — no new signal this run;
  #550/#551 review `none`: search shows no review activity
  (`"reviewDecision":""` in E40-1 prview raws, unchanged).
- new upstream hits `0`: raw/w40-jb-stubs-140537-new-prs.json → `new prs 0`
  (search created:>2026-10-07T06:20:00Z); new open issues since head commit: none
  printed from w40-jb-stubs-140537-new-work.json.
- keyword searches pasted: "test -x" → raw/w40-jb-stubs-140537-search-testx.txt
  (closest upstream signal: issue #459 `ls -l shows hardcoded -rw-r--r-- /
  drwxr-xr-x instead of the file mode` — related file-mode surface, not stub
  executability; issue #458 executable-by-path shebang, unrelated to stubs);
  "executable" → raw/w40-jb-stubs-140537-search-exec-issues.txt (same #458/#459).
  Verdict per hit: UNRELATED (both predate the branch; neither covers `test -x`
  on command stubs). No PR titled stub/executable: raw/w40-jb-stubs-140537-pr-stub.txt
  shows only #531 (commandNotFound), #551 (ours, grep anchor), #70 (workflow serde).
- own PR: raw/w40-jb-stubs-140537-own-pr.txt → empty (no PR from this branch in
  the fork; consistent with HELD status).

Verdict: HOLD (no first maintainer review exists for this branch — it has no PR
open at all; branch is clean vs main with no conflict, so it can open a PR
immediately after #546 rebases or independently; nothing upstream blocks it)
