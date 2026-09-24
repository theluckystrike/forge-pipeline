# How outreach drafts get sent

Nothing in this pipeline sends email on its own. The sender at bin/send_outreach.py runs as a dry run by default. With `--arm` it stops at a stub that raises NotImplementedError until the owner picks one of the two routes below.

## Review first

1. Run `python3 ~/oss-pipeline/bin/send_outreach.py --full` to read every draft that passed the gate.
2. For each draft you approve, add its file name (for example `123-L1.txt`) on its own line in `~/oss-pipeline/outreach/approved.txt`. A draft that isn't listed there never counts as sendable.
3. To reject a draft, move it to `outreach/rejected/` by hand and write the reason beside it.

Caps apply to both routes: 8 per UTC day and 40 per rolling 7 days, counted from outreach.sent_at. The sender refuses anything past the cap.

## Route A. Porkbun webmail, manual (available today)

The owner sends each approved draft by hand from mike@zovo.one in Porkbun webmail.

1. Copy the Subject line and the body (everything after the first blank line) into a new message. Send it to the address the dry run prints as `to=`.
2. Check the Reply-To is mike@zovo.one.
3. Right after sending, record it with `python3 ~/oss-pipeline/bin/send_outreach.py --mark-sent <file>`. That sets outreach.sent_at, moves the file to outreach/sent/, and keeps the caps honest.

Webmail notes from past sessions: the sent folder is INBOX.Sent, not Sent.

## Route B. Resend API, only after key rotation

The Resend key was compromised in August 2026. It sent 12,935 phishing emails from both domains, and copies of that key still sit in 3 places. No programmatic send may run until all of these are done by the owner:

1. Revoke the old key in the Resend dashboard and create a new one scoped to sending from zovo.one only.
2. Delete every old copy of the key from disk and from environment files.
3. Check the domain's SPF, DKIM and DMARC records and the Resend suppression list.
4. Store the new key where only the sender reads it, then replace `transport_send()` in bin/send_outreach.py with the Resend call. Keep the dry-run default and the `--arm` flag.

Until those steps are done, Route A is the only route.

## L4 and L5

L4 founder notes and L5 devrel pitches are manual. The owner writes each one from outreach/templates/L4.md, L4-linkedin.md or L5.md, with a fact he checked himself. LinkedIn automation stays off, so every LinkedIn message is typed and sent by hand. Before any L4 send, check that https://github.com/theluckystrike/codebase-licensing-checklist loads. It returned 404 on 2026-09-24.

## Humanize rules apply to every email, every time

The source of truth is ~/Desktop/humanize (HUMANIZE.md and scan.py). Nothing goes out unless it passes.

- The gate re-syncs both files from the Desktop on every run and logs the sha to state/humanize-sync.log.
- Email is zero tolerance. Every scan.py finding blocks, hard or soft. The gate also checks the HUMANIZE.md rules the scanner misses: colon before a list, three similar-length sentences in a row, no contractions, paragraphs over 4 sentences, a question as the opener, exclamation marks, and markdown bold or headings.
- The builder, the gate, and the sender (dry run, --arm, --mark-sent) all run it. A draft edited after gating is blocked until you re-gate it with `python3 outreach_gate.py --rehash FILE`.
- Any email written outside the pipeline (replies, follow-ups) gets the same check first with `python3 tools/email_humanize.py FILE`.
