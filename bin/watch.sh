#!/bin/bash
# WhiteHERO v3 watcher (plan Phase 0 step 0.6, stage 6 "Watch").
# Logic carried over from ~/oss-pipeline-state/w43-night-loop.sh, generalised from a
# hard-coded PR list to every contributions row with status OPEN in kpi.db.
#  (a) poll open PRs with gh pr view (max 60 calls per run, rotating cursor),
#      update contributions.status to MERGED or CLOSED on change, log one line per change
#  (b) grep new PR comments and review bodies for bot|automated|spam|AI-generated|slop -> RED FLAG lines
#  (c) print days remaining to the Medusa fuse (2026-10-07)
#  (d) run bin/expensify_feed.py (owned by another agent) if present and executable
# Run by launchd com.theluckystrike.mergewatch every 1800 s. Every command is wrapped in timeout.
set -u
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
PIPE=/Users/mike/oss-pipeline
DB="$PIPE/state/kpi.db"
LOG="$PIPE/state/watch.log"
SEEN="$PIPE/state/watch-seen.json"
CURSOR="$PIPE/state/watch-cursor.txt"
MAX_CALLS=60
FUSE=2026-10-07
TS=$(timeout 5 date -u +%FT%TZ)
WORK=$(timeout 5 mktemp -d "${TMPDIR:-/tmp}/whwatch.XXXXXX") || { echo "[$TS] ERROR mktemp failed" >> "$LOG"; exit 1; }
trap 'timeout 10 rm -rf "$WORK"' EXIT

log() { echo "$1" | timeout 5 tee -a "$LOG"; }

# (a) collect OPEN PR urls; rows without pr_url are rebuilt from repo + pr; issue links are skipped
timeout 60 sqlite3 -cmd ".timeout 30000" -separator '|' "$DB" \
  "select id, coalesce(pr_url,''), coalesce(repo,''), coalesce(pr,'') from contributions where upper(status)='OPEN' order by id" \
  > "$WORK/rows.txt" 2> "$WORK/sqlite.err" || { log "[$TS] ERROR sqlite read failed: $(timeout 5 head -c 200 "$WORK/sqlite.err")"; }

timeout 30 python3 - "$WORK/rows.txt" "$WORK/urls.txt" <<'PY'
import sys, re
rows = [l.rstrip("\n").split("|") for l in open(sys.argv[1]) if l.strip()]
urls = []
for rid, url, repo, pr in rows:
    if not re.match(r"https://github\.com/[^/]+/[^/]+/pull/\d+$", url):
        n = re.sub(r"\D", "", pr)
        url = f"https://github.com/{repo}/pull/{n}" if repo and n else ""
    if url and url not in urls:
        urls.append(url)
open(sys.argv[2], "w").write("".join(u + "\n" for u in urls))
PY

TOTAL=$(timeout 5 wc -l < "$WORK/urls.txt" | tr -d ' ')
START=$(timeout 5 cat "$CURSOR" 2>/dev/null || echo 0)
case "$START" in ''|*[!0-9]*) START=0 ;; esac
[ "$TOTAL" -gt 0 ] && [ "$START" -ge "$TOTAL" ] && START=0

CALLS=0; ERRS=0; i=0
: > "$WORK/fetched.txt"
while IFS= read -r url; do
  if [ "$i" -ge "$START" ] && [ "$CALLS" -lt "$MAX_CALLS" ]; then
    CALLS=$((CALLS+1))
    f="$WORK/pr_$CALLS.json"
    if timeout 60 gh pr view "$url" --json state,mergedAt,reviewDecision,comments,reviews > "$f" 2> "$f.err"; then
      echo "$url|$f" >> "$WORK/fetched.txt"
    else
      ERRS=$((ERRS+1))
      log "[$TS] ERROR gh pr view $url: $(timeout 5 head -c 160 "$f.err" | tr '\n' ' ')"
      if timeout 5 grep -qiE 'rate limit|secondary|abuse|403|429' "$f.err"; then
        log "[$TS] rate limited, stopping batch"; break
      fi
    fi
  fi
  i=$((i+1))
done < "$WORK/urls.txt"
NEXT=$((START+CALLS)); [ "$NEXT" -ge "$TOTAL" ] && NEXT=0
echo "$NEXT" > "$CURSOR"

# Apply state changes and scan comments in one python pass
DAYS=$(timeout 10 python3 -c "import datetime;print((datetime.date.fromisoformat('$FUSE')-datetime.date.today()).days)")
timeout 120 python3 - "$WORK/fetched.txt" "$DB" "$SEEN" "$LOG" "$TS" "$TOTAL" "$CALLS" "$ERRS" "$DAYS" <<'PY'
import sys, json, re, sqlite3, os
fetched, db_path, seen_path, log_path, ts, total, calls, errs, days = sys.argv[1:10]
def log(line):
    print(line, flush=True)
    with open(log_path, "a") as fh: fh.write(line + "\n")
try:
    seen = json.load(open(seen_path))
    baseline = False
except Exception:
    seen, baseline = {}, True
FLAG = re.compile(r"\b(bot|automated|spam|ai[- ]generated|slop)\b", re.I)
BOTLOGIN = re.compile(r"(bot$|-bot|\[bot\]|^github-actions|^vercel|^netlify|^codecov|^coderabbit|^sonar|^cla-?assistant|^copilot)", re.I)
db = sqlite3.connect(db_path, timeout=30)
changes = merged = closed = flags = botflags = newc = 0
for line in open(fetched):
    url, path = line.rstrip("\n").split("|", 1)
    try: d = json.load(open(path))
    except Exception as e:
        log(f"[{ts}] ERROR parse {url}: {e}"); continue
    state = d.get("state", "")
    num = url.rsplit("/", 1)[1]; repo = url.split("github.com/")[1].rsplit("/pull/", 1)[0]
    if state in ("MERGED", "CLOSED"):
        ids = [r[0] for r in db.execute(
            "select id from contributions where upper(status)='OPEN' and (pr_url=? or (repo=? and replace(cast(pr as text),'#','')=?))",
            (url, repo, num))]
        if ids:
            db.executemany("update contributions set status=? where id=?", [(state, i) for i in ids])
            db.commit()
            changes += 1; merged += state == "MERGED"; closed += state == "CLOSED"
            log(f"[{ts}] CHANGE {url} OPEN -> {state} mergedAt={d.get('mergedAt')} review={d.get('reviewDecision')} rows={ids}")
    items = [("comment", c) for c in d.get("comments", [])] + [("review", r) for r in d.get("reviews", []) if r.get("body")]
    for kind, c in items:
        cid = c.get("id") or f"{url}#{c.get('createdAt') or c.get('submittedAt')}"
        if cid in seen: continue
        seen[cid] = ts; newc += 1
        who = (c.get("author") or {}).get("login", "?")
        if who == "theluckystrike": continue
        body = c.get("body") or ""
        m = FLAG.search(body)
        if not m: continue
        is_bot = bool(BOTLOGIN.search(who))
        snippet = re.sub(r"\s+", " ", body[max(0, m.start()-80): m.end()+80]).strip()
        if is_bot:
            botflags += 1
            if baseline: continue
            log(f"[{ts}] RED FLAG [bot-author] {url} {kind} by {who}: word='{m.group(0)}' ... {snippet} ...")
        else:
            flags += 1
            log(f"[{ts}] RED FLAG {url} {kind} by {who}: word='{m.group(0)}' ... {snippet} ...")
db.close()
json.dump(seen, open(seen_path, "w"))
log(f"[{ts}] SUMMARY open_urls={total} polled={calls} errors={errs} changes={changes} merged={merged} closed={closed} "
    f"new_comments={newc} red_flags={flags} bot_author_matches={botflags}{' (baseline run, bot matches not itemised)' if baseline else ''} "
    f"medusa_fuse={days}d_to_2026-10-07")
PY
PYRC=$?
[ "$PYRC" -ne 0 ] && log "[$TS] ERROR python pass failed rc=$PYRC"

# (c) Medusa fuse line on stdout for the launchd log
echo "[$TS] Medusa fuse 2026-10-07: $DAYS days remaining"

# (d) Expensify Help Wanted feed, built by another agent
if [ -x "$PIPE/bin/expensify_feed.py" ]; then
  timeout 300 "$PIPE/bin/expensify_feed.py" >> "$PIPE/state/expensify_feed.out" 2>&1
  log "[$TS] expensify_feed.py exit=$?"
fi
exit "$PYRC"
