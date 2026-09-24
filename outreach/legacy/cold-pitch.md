# Cold Pitch — drift-scraper leads

**To:** [owner] ([repo])
**Subject:** [repo] — your [locale] is missing [pct]% of keys vs en.json

---

Hi [owner],

Quick, specific note on [repo]: I ran a parity check on your locale files and
**your [locale].json is missing [pct]% of the keys that exist in en.json**.
That means [users in that language] are seeing untranslated strings or
placeholder text.

I do locale-parity work as a service. My pipeline:

- automates the diff against `en.json`,
- human-reviews every string (no machine-only output),
- ships **merge-ready PRs in under 48 hours**.

One-off completion or a retainer that keeps every locale green. If it's
useful, I can send a full breakdown of which keys are missing across all your
locales.

Best,
[Your name]

---

## Follow-up (one, max)

Hi [owner], just following up once on the [locale] parity gap in [repo] —
[missing]% of keys missing vs en.json. Happy to send the full key-by-key
breakdown if useful. If not, no worries.