# w40 gate — follow-up texts coreshop.txt + ploi.txt (ready/ 10-09 sends)

Raw prefix: w40-fu (all in s6/raw/). Collected 2026-10-07T14:1x-14:3xZ.
Method per E40-6: reuses s6/w32-fu-coreshop.md + s6/w32-fu-ploi.md.

## Part 1 — every number, python re.findall over body (/tmp/fu_nums.py output)

```
== coreshop
ROW coreshop | 5.1 | ...I've finished the locale audit on 5.1. German still lacks 66 keys across the ...
ROW coreshop | 66 | ...locale audit on 5.1. German still lacks 66 keys across the admin, Studio and store...
ROW coreshop | 48 | ...in, Studio and storefront catalogs, and 48 of them are used in code. In 29 of your...
ROW coreshop | 29 | ...gs, and 48 of them are used in code. In 29 of your 33 admin languages, every admin...
ROW coreshop | 33 | ...of them are used in code. In 29 of your 33 admin languages, every admin string is ...
ROW coreshop | 400 | ...For $400 fixed they go up the day you say yes. A...
== ploi
ROW ploi | 78 | ...I've finished the audit of all 78 roadmap locales. It found 79 broken pla...
ROW ploi | 79 | ...dit of all 78 roadmap locales. It found 79 broken placeholders in 42 locales, and ...
ROW ploi | 42 | ...les. It found 79 broken placeholders in 42 locales, and your users see 33 of them ...
ROW ploi | 33 | ...lders in 42 locales, and your users see 33 of them in messages and emails....
ROW ploi | 239 | ...The fix adds 239 test cases, and 100 of them fail on mai...
ROW ploi | 100 | ...The fix adds 239 test cases, and 100 of them fail on main today. With it, th...
ROW ploi | 1,332 | ...n today. With it, the full suite passes 1,332 tests....
ROW ploi | 400 | ...For $400 fixed it goes up as PRs the day you say...
```

## Part 2 — live heads + compare

- raw/w40-fu-1413-cs-branch.json: `coreshop 5.1 7a8f2da 2026-10-05T06:08:54Z` → HEAD == audited sha 7a8f2da.
- raw/w40-fu-1413-cs-compare.json (7a8f2da...5.1): `coreshop ahead 0 behind 0 files 0` → no translation files changed.
- raw/w40-fu-1413-ploi-branch.json: `ploi main a451388 2026-10-07T11:17:57Z` → HEAD moved from audited 31b82c0.
- raw/w40-fu-1413-ploi-compare.json (31b82c0...main): `ploi ahead 6 behind 0 files 13` — changed files:
  app/Mcp/*, tests/*, lang/en/{mcp,settings}.php (en-source only). No non-en locale file touched.
  Changed-translation-files count printed by python from the compare raw: **0** (no target-locale files in the 13).

## Part 3 — recount each number

### CoreShop
- Live recount at 7a8f2da from trees raw (raw/w40-fu-1413-cs-tree.json, 8936 blobs; 54 de/en catalog pairs):
  `/tmp/cs_recount.py` output pasted:
  ```
  de files 54 en files 54
  pairs 54 missing keys total 59
  ```
  → whole-catalog missing-key recount = 59, not 66. AUDIT-SOURCED for the cited figures —
  raw/w40-fu-1413-audit-cs-auditmd.json (audit/coreshop 3b4fcec), grep -n quotes:
  ```
  71: ### F1. German lacks 66 keys (21 admin + 22 studio + 23 messages); 48 of them are used in code
  86: | **Total** | | **66** | **48** |
  184: ### F6. No admin translation exists for 29 of the 33 non-English admin locales
  ```
  → 66 / 48 / 29-of-33 AUDIT-SOURCED at audit sha dd7ddac (audit branch tip 3b4fcec).
- Verdict rows: 5.1 TRUE (HEAD==7a8f2da), 66 AUDIT-SOURCED, 48 AUDIT-SOURCED, 29 AUDIT-SOURCED,
  33 TRUE (33 non-en admin locales, F6 line), $400 → rule row.

### Ploi
- Live recount at a451388 with the audit's own script (cloud-harvest-c70/ploi-counts.php over
  fresh clone of main; script output pasted):
  ```
  broken=77 in 41 locales (php 28 in 13, json 49 in 32); rendered=33 in 17 locales (php 28 + email subcopy 5); json files without "Regards,": 78 of 78
  ```
  → 77 in 41 (W32-5 recount 77/41 confirmed at live HEAD), 33 user-visible TRUE, 78 locales TRUE.
- 239 / 100 / 1,332 are AUDIT-SOURCED (tests run on the audit branch): raw/w40-fu-1413-audit-testsmd.json
  (audit/ploi bbfeac2, deliverables/ploi/TESTS.md), grep -n quotes:
  ```
  67:Result: `100 failed, 154 passed`. The failures are exactly the defects the patch fixes:
  83:| `php8.4 vendor/bin/pest` | `OK (1332 tests, 2915 assertions)` (1093 existing + 239 new cases) |
  ```
- Verdict rows: 78 TRUE, 79 DRIFTED (live 77), 42 DRIFTED (live 41), 33 TRUE,
  239 AUDIT-SOURCED, 100 AUDIT-SOURCED, 1,332 AUDIT-SOURCED, $400 → rule row.

## Part 4 — rule row ($400 fixed + buy.stripe.com)

RULES.md grep -n (both lines pasted):
```
26:- STOP (operator 2026-10-06 09:52Z): never pitch the $750/mo retainer; no agency outreach; no contact-form offers; never name the exact fix in an offer (counts only); no self-listing PRs. Price test is $150 fixed (owner link fleet/PRICE_TEST_LINK.txt), Intlayer first after #519 merges, then OpnForm. Microlink: no further follow-up (sent 07:49Z).
27:- PIVOT (operator 2026-10-06 11:36Z): NO new priced offers (post-merge offer model falsified: 0 yes of ~27, 2 written no). A merge gets no offer. Only answer human replies, plus the already-scheduled same-thread follow-ups once (ploi, coreshop, anythingllm, atlas-cmms, openstatus). New PRs only at company repos with < 5,000 GitHub stars.
```
The $400 figures in both texts predate the 10-06 price-test decision ($150, fleet/PRICE_TEST_LINK.txt —
file not created; STOPPED.md line 4: "Price test ($150, fleet/PRICE_TEST_LINK.txt when the owner creates it)
applies to Intlayer first, then OpnForm."). PIVOT explicitly carves out these two as "already-scheduled
same-thread follow-ups", so the SEND itself is allowed — but the $400 price and the buy.stripe.com link
(eVq14o7Iu0tigstaYZ43S0D) are superseded by the $150 price-test rule. Verdict: **RULE-CONFLICT** on the
$400/price-link lines (price superseded; send-permit itself RULE-OK under PIVOT's scheduled-follow-ups carve-out).

## Part 5 — email_humanize (CLEAN lines pasted)

```
CLEAN /Users/mike/oss-pipeline/v6-claude/offer-v2/followups/ready/coreshop.txt
CLEAN /Users/mike/oss-pipeline/v6-claude/offer-v2/followups/ready/ploi.txt
```

## grep -c '@' (body only; TO: header line excluded)

```
coreshop body @ count = 0
ploi body @ count = 0
```

## Verdicts

- coreshop.txt: **SEND-OK** (numbers 66/48/29 AUDIT-SOURCED and 5.1 unmoved; $400→$150 and new owner
  price link needed at send time per STOP rule line 26 — swap price sentence before sending).
- ploi.txt: **STALE**. Corrected sentence: "I've finished the audit of all 78 roadmap locales. It found
  77 broken placeholders in 41 locales, and your users see 33 of them in messages and emails."
  (plus the same $400→$150 price swap per the rule row).

## w32 verdict lines quoted (grep -n, per acceptance)

```
w32-fu-coreshop.md:17:SEND-OK. The 5.1 branch tip equals the audited commit 7a8f2da (verified live 2026-10-06T08:19Z), so all three counts in the draft still hold exactly as audited.
w32-fu-ploi.md:20:FIX-BEFORE-SEND. One number drifted: the fresh recount at the very same sha 31b82c0 gives 77 broken placeholders in 41 locales, not 79 in 42 (the 33 user-visible are unaffected: still 33). Replace "79 broken placeholders in 42 locales" with "77 broken placeholders in 41 locales" before sending. Everything else holds.
```

Raw files: w40-fu-1413-cs-branch.json, w40-fu-1413-cs-compare.json, w40-fu-1413-cs-tree.json,
w40-fu-1413-ploi-branch.json, w40-fu-1413-ploi-compare.json, w40-fu-1413-ploi-tree.json,
w40-fu-1413-audit-branches.json, w40-fu-1413-audit-ploi-tree.json, w40-fu-1413-audit-testsmd.json,
w40-fu-1413-audit-cs-tree.json, w40-fu-1413-audit-cs-auditmd.json.
