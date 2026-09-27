# L4 Rubric — cve-lite-cli #1000 (2026-09-27)

Candidate: OWASP/cve-lite-cli issue #1000, gate-line + docs decision (maintainer decided option 1 + output line in issue).

| Category | Pts | Evidence |
|---|---|---|
| Real value | 25 | Implements the maintainer's explicit decision, verbatim output format from issue. Not speculative. |
| Repo health | 10 | MIT, 740 stars, pushed 2026-09-26 (yesterday), OWASP org, active bot reviewer. |
| Issue state | 10 | Open, unassigned, maintainer-authored with decision comment, no competing PR, no stale cross-ref (PR #507 unrelated repo path). |
| Convention compliance | 25 | Verified from repo tree: helper placed next to reachesFailOn in severity.ts, both scan paths patched at exact current anchors post-#1129, jest test in tests/cli matching maintenance-args.test.ts style (direct import, describe/it), docs in website/docs/cli-reference.md table format. |
| Humanize gate | 10 | PR body + commit subjects scanned programmatically, zero em dashes, zero colons in authored prose, no bold labels. Pre-existing upstream lines untouched. |
| Verification depth | 15 | tsc clean at patched hunks (only pre-existing strict-mode TS7006/TS2307 elsewhere), 6-case logic unit test run in node incl. maintainer reproduction case, diff scan of added doc lines, test file typechecked clean. |
| Merge probability | 5 | Small (3 files + 1 test), maintainer-decided scope, test included, docs-only fallback acceptable to maintainer. |
| **Total** | **100** | |
