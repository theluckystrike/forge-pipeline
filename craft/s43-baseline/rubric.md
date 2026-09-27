# Rubric — svnaxis/obsidian-baseline README link fix (S43)

- Real defect, user-reported: issue #258, verified by live curl (404 on all aaaaalexis.github.io paths; pages site + account deleted). 25/25
- Minimal fix: 4 lines in one file, URL substitutions only, no reformatting. 20/20
- Verified targets: every replacement URL returns 200 incl. /marketplace/, /migration/, /install?name=Baseline, repo redirect. 20/20
- Uncontested: no open PR, no other claimant, maintainer responsive (last release 3.2.12 recent). 15/15
- Convention compliance: PRs use plain titles, fix: prefix seen upstream; branch from main; humanized commit subject (no colons/em dashes). 10/10
- No fabricated claims: all status codes from real curl/gh output in this session. 10/10

Total: 100/100 → SHIP.
