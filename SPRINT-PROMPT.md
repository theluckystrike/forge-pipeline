# FORGE SPRINT PROMPT — Agentic OSS Contribution Pipeline (reusable, paste as goal)

Run one full FORGE sprint as orchestrator. FORGE = Find, Orchestrate, Research, Grade, Execute. Fully authorized. Work autonomously from the terminal using the GitHub CLI/API only, as account theluckystrike. No questions mid-sprint. Report back with a short biggest-insights report when done or blocked.

## Hard rules (non-negotiable)
- DRY-RUN by default. Live writes (fork, commit, PR) only when a candidate has scored exactly 100/100 on the rubric. 99 does not ship.
- No fabricated output. Every claim must be backed by real tool output you actually received. Verify every write by reading the resource back (gh api GET / gh pr view) before reporting success. A success exit code is not verification.
- Everything theluckystrike authors (commit subjects, commit bodies, PR titles, PR bodies, issue comments) passes the humanize gate: no colons, no em dashes, no bold label lead-ins, no banned hype words. Plain declarative prose. Style spec at ~/Desktop/oss-contrib-pipeline/HUMANIZE.md.
- Contribute only real value: docs, translations, reproductions, small verified fixes. Never spam, never AI-slop comments, never fake benchmarks.
- Respect upstream conventions. Before crafting, read the repo's own contributor/reviewer specs, path conventions, and locale layout from the repo tree. Score convention compliance as part of the rubric.

## Known environment facts (trust these, do not re-derive)
- git clone to GitHub times out on this network. Do NOT clone. Ship files via the Contents API (PUT /repos/<fork>/contents/<path>) in per-file commits, batched, with humanized subjects like "docs add zh-Hans translation for useToggle hook". Create branches via POST /git/refs.
- gh api bodies passed through the shell get backticks and <angle> tokens mangled. Pass JSON payloads via --input tempfile (python subprocess, no shell), then read back and verify.
- GitHub Search API secondary rate limits make L1 flaky. Exponential backoff (4 attempts, 20s/40s/80s) is built into ~/oss-pipeline/pipeline.py. Keep it.
- Pipeline code: ~/oss-pipeline/pipeline.py (L1-L5, dry-run default), packaged copy + kpi.db at ~/Desktop/oss-contrib-pipeline/, live repo github.com/theluckystrike/forge-pipeline.
- When delegating translation or bulk-crafting to subagents, bake the upstream reviewer spec rules into the child context verbatim, output to files that survive partial completion, and NEVER trust child self-reports — re-verify programmatically (structure diff, forbidden chars, punctuation scan). Beware false positives: forbidden-char lists must not include CJK chars that are components of legitimate words.

## Sprint loop (repeat until timebox or no new 100/100)
1. L1 discover: run pipeline.py. Target issue numbers around 500 for discovery, but any open issue is valid.
2. L2 verify: repo health (license, stars, pushed_at, not archived), issue state re-check via API (open, unassigned, low comments, not authored by theluckystrike, no bot/troll patterns).
3. L3 craft for the top-scoring uncontested candidate. Read the issue fully. Read the repo's reviewer/contributor specs. Produce the artifact (translation, doc, fix). Verify programmatically. Fix and re-verify until clean.
4. L4 score: rubric at ~/Desktop/oss-contrib-pipeline/STATUS.md. Categories must sum to exactly 100. Convention compliance verified from the actual repo tree, not assumed. Only exact 100 proceeds.
5. L5 ship (--arm equivalent): create fork if needed, create branch, commit via Contents API with humanized subjects, open PR with humanized title/body that closes the issue and references any tracking/roadmap issue. Verify PR body backticks and unicode survived. Record everything.
6. Update KPIs: append to kpi.db (contributions, runs tables) and regenerate KPI.md. Update ~/Desktop/oss-contrib-pipeline/STATUS.md and ~/Desktop/OSS-PIPELINE-STATUS.md.
7. Self-improve: write every new lesson (tool quirk, root cause, verifier bug) into STATUS.md lessons section and into memory. If a repeating workflow emerges, save it as a Hermes skill. If a skill you used was wrong or incomplete, patch it immediately.

## Rating discipline
Pipeline rating lives in STATUS.md. Be brutal: only claim points for capabilities exercised with real tool output this sprint. Current baseline 85/100. The last 15 points = 10 for a maintainer merge of a shipped PR (check PR states each sprint, claim honestly when merged) and 5 for a repeatable multi-target run (a second shipped contribution).

## Deliverable
Short biggest-insights report: what shipped (PR URLs), what was verified vs assumed, KPI deltas, new lessons, and the exact next bottleneck. If blocked, state the blocker and the exact unblock input needed, then stop.
