# FORGE — Agentic OSS Contribution Pipeline

FORGE = Find, Orchestrate, Research, Grade, Execute.
Fully autonomous open-source contribution pipeline via GitHub CLI/API only, account theluckystrike.

## Rules (hard)
- Dry-run by default. Live only with explicit --arm.
- 100/100 rubric gate. 99 does not ship.
- No fabricated output. Every claim backed by real tool output.
- All commits, PR titles and bodies humanized per HUMANIZE.md (no colons, no em dashes, plain prose).
- Zero-clone fallback: commit via Contents API when git clone is blocked.

## Layers
L1 discover -> L2 verify -> L3 craft -> L4 score (100-pt hard gate) -> L5 ship

## Files
- pipeline.py — orchestrator (L1-L5)
- l1t_docs.py — docs/test-coverage discovery lane
- STATUS.md — current status and rating (85/100)
- HUMANIZE.md — commit/PR style gate
- kpi.db — SQLite KPI database (contributions, runs, kpi tables)

## KPIs
Query: sqlite3 kpi.db "select * from kpi;"
