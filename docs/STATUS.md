# OSS Pipeline Status (w43d sprint, 2026-09-24 14:20 +07)

## Fleet (all verified via gh pr view this sprint)
- MiroFish #826 (74k stars) es locale 631 keys - OPEN MERGEABLE, +673 single file - SHIPPED THIS SPRINT
- jsxc #1136 nds 137 keys - OPEN
- bob-wallet #688 zh 160 keys - OPEN
- ox_inventory #7 es 180 keys - OPEN
- Fenrus #258 de 204 keys - OPEN
- medusa 10 PRs - OPEN (16932 has open bot items, sradevski pinged)

## KPIs (kpi.db working copy /tmp/kpi-work.db; Desktop sync stalled)
- contributions 70, MERGED 19, OPEN 42
- rating: 85/100 (baseline; +merge still pending)

## Blockers
- /Users/mike/Desktop iCloud stall + disk 100% (freed to 5.6Gi; Desktop file ops still time out)
- kpi.db writes on Desktop time out; /tmp/kpi-work.db is authoritative until Desktop recovers

## Lessons (w43d)
- search/code GET querystring with + separators works; -f POST form fails (404) for search endpoints
- translation worker stalled on read_file of a Desktop path inherited from context - bake "never touch /Users/mike/Desktop" into every child brief
- byte-verify every Contents API PUT with cmp against readback before PR open
