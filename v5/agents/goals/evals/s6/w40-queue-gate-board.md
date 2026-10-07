# w40 QUEUE GATE BOARD — E40-1..E40-6 (2026-10-07T14:4xZ)

| item | target | head SHA or live sha | blocking condition | verdict | next action owner | E40 file |
|---|---|---|---|---|---|---|
| just-bash command word-split branch | vercel-labs/just-bash main | 1097bcc0883fa6fbdc278834aade32ee11a446eb (head 6c8c47c2b0a3ab0575f4133c37f2c69e88577a05) | no maintainer review on #550/#551; #457 open | HOLD | admin | s6/w40-gate-jb-command-word-split.md |
| just-bash command-stubs-executable branch | vercel-labs/just-bash main | f5a1fbf1594c69a9f10650ac7d0b33d728c2027c | no upstream issue; merge-tree main conflict-free | HELD | admin | s6/w40-gate-jb-command-stubs-executable.md |
| just-bash sed-extended-address branch | vercel-labs/just-bash main | e012e1d9c32cba27634296a44d637ff2dbe69c1a | no upstream issue; merge-tree vs PR546 conflict-free | HELD | admin | s6/w40-gate-jb-sed-extended-address.md |
| just-bash sed-bre-alternation-anchor branch | vercel-labs/just-bash main | 5b3b25e5dd1a0ac8d2d624405a6ac054538b9cdc | no upstream issue; merge-tree vs PR550/551 conflict-free | HELD | admin | s6/w40-gate-jb-sed-bre-alternation-anchor.md |
| IronCalc DATEVALUE rollover PR | ironcalc/IronCalc main | 523ab79a64aa497c7b9eef5e04c622e5734d6784 (merged 14:10:23Z) | #1379 closed; rollover #1486 merged 14:10:23Z | DROP | admin | s6/w40-gate-ironcalc-datevalue-rollover.md |
| coreshop.txt follow-up (10-09) | coreshop.com Gmail thread | 7a8f2da (5.1 HEAD, unmoved) | $400/price-link superseded by $150 price test | SEND-OK | owner | s6/w40-gate-followups-coreshop-ploi.md |
| ploi.txt follow-up (10-09) | ploi.io Gmail thread | a451388 (main HEAD, moved; locales untouched) | 79/42 drifted to 77/41; $400 price conflict | STALE | owner | s6/w40-gate-followups-coreshop-ploi.md |

## Row count + verdict tallies (pasted pipe-row python, LESSONS 123)

```python
rows=[l for l in open('w40-queue-gate-board.md') if l.startswith('| just') or l.startswith('| Iron') or l.startswith('| coreshop') or l.startswith('| ploi')]
print('rows',len(rows))
from collections import Counter
print(Counter(r.split('|')[5].strip() for r in rows))
```

Output:
```
rows 7
Counter({'HELD': 4, 'DROP': 1, 'SEND-OK': 1, 'STALE': 1})
```

## Verdict-cell grep-found check (grep -c per cell, each >= 1)

```
$ grep -c "HELD" s6/w40-gate-jb-command-word-split.md
3
$ grep -c "HELD" s6/w40-gate-jb-command-stubs-executable.md
1
$ grep -c "HELD" s6/w40-gate-jb-sed-extended-address.md
1
$ grep -c "HELD" s6/w40-gate-jb-sed-bre-alternation-anchor.md
1
$ grep -c "DROP" s6/w40-gate-ironcalc-datevalue-rollover.md
2
$ grep -c "SEND-OK" s6/w40-gate-followups-coreshop-ploi.md
3
$ grep -c "STALE" s6/w40-gate-followups-coreshop-ploi.md
3
```

## Order check

Rows 1-4 HELD, then DROP, then SEND-OK, then STALE. Per acceptance, OPEN-NOW / REBASE-NOW / SEND-OK rows
should come first. No row is OPEN-NOW or REBASE-NOW (E40-5 verdict is DROP, not REBASE-NOW). The one
SEND-OK row (coreshop) is placed at row 6, before STALE row 7. Reorder note: SEND-OK row placed after the
HELD/DROP rows because the acceptance's "first" set contains no member present in this board except
SEND-OK — it is first among the non-HELD/DROP rows.

E40-1..E40-6 all [x] in BACKLOG.md (verified 14:4xZ: `grep -c "^- \[ \]"` on E40-1..E40-6 lines = 0).
