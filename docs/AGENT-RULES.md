# WhiteHERO v3 shared agent rules (2026-09-24). Read fully before any tool call.

Plan: ~/oss-pipeline/WHITEHERO-V3-PLAN.html (section numbers below refer to it). PIPE=~/oss-pipeline.

## Money and APIs
- Paid API budget is $0. No DataForSEO, OpenRouter, treg, GLM/llm_translate.py, Resend, DeepL, Google, or any metered LLM/API. You are the model; do not call another.
- Free: gh CLI (authenticated as theluckystrike), curl to public pages, raw.githubusercontent.com, sqlite3, python3 stdlib, dig.

## Shared GitHub quota (8 agents run at once)
- Check `gh api rate_limit --jq '.resources | {core:.core.remaining, search:.search.remaining, graphql:.graphql.remaining}'` before any bulk run and every ~200 calls.
- Your cap unless your brief says otherwise: 600 REST calls, 150 search calls, 1500 GraphQL points per hour.
- Secondary limit or 403/429: back off 20 s, 40 s, 80 s, then stop the batch and record it.
- raw.githubusercontent.com fetches do not count against the API; prefer them for file contents.

## Filesystem
- Code and state live ONLY in ~/oss-pipeline. Never write executables under ~/Desktop.
- Any read under ~/Desktop must be wrapped in `timeout 25`. Never cp onto a dataless target.
- Never run killall or `ps aux`. Do not touch the running park_watch.sh or w43-night-loop.sh processes.
- git clone of large repos times out on this network: use the contents API or raw URLs.

## Database
- ~/oss-pipeline/state/kpi.db, WAL mode. Python: sqlite3.connect(path, timeout=30); CLI: `sqlite3 -cmd ".timeout 30000"`.
- Write only the tables your brief assigns. Never DROP or DELETE rows you did not create. Schema: plan section 7.

## Outward actions: FORBIDDEN unless your brief explicitly grants one
- No emails sent. No LinkedIn. No Upwork posting.
- No issues, PRs, comments, reactions, or stars on any repo you do not own.
- No commercial text in anything that lands on GitHub outside theluckystrike's own repos (AUP section 10).
- Do NOT harvest email addresses from GitHub (commit metadata, profiles, API) for outreach. GitHub AUP section 4 forbids using GitHub data for unsolicited email. Contacts come from the company's own website only.

## Prose (anything a human will read: reports, templates, READMEs, pages)
- No em-dashes (U+2014) or " -- ", no emojis, no "delve/leverage/robust/synergy" family. Rules: ~/oss-pipeline/docs/HUMANIZE.md.
- Gate: `python3 ~/oss-pipeline/tools/humanize_scan.py --strict <files>` must PASS (exit 0). It is proven against a bad control today.
- Never offer or propose a call, meeting, or Zoom in any outreach text.
- Never claim anything unverified: no "merged" unless gh says MERGED, no "native speaker review", no invented clients.

## Truth
- Verify artifacts, not prose. Every number you report must come from a command output you ran; save raw outputs beside your artifacts.
- Final message: files written (paths), commands run, measured counts, failures with error text, and anything left undone and why.
