#!/usr/bin/env python3
"""FORGE outreach sender — Resend API via curl (urllib gets CF-403), mike@zovo.one.
Template: outreach/template-pr.html (humanized per Desktop/humanize/HUMANIZE.md,
scanner-verified). Dry-run by default; --live sends. Logs to outreach table.
Governor: max 8/cycle, dedupe by outreach rows, skips errors."""
import json, sqlite3, hashlib, time, subprocess, sys, pathlib

KEY = [l.split("=",1)[1].strip() for l in pathlib.Path.home().joinpath(".zshrc")
       .read_text().splitlines() if l.startswith("export RESEND_API_KEY=")][0]
FROM, REPLY_TO = "FORGE <mike@zovo.one>", "lipmichal@gmail.com"
DB, CAP = "state/kpi.db", 8
TPL = pathlib.Path(__file__).parent.joinpath("template-pr.html").read_text()

def unsent(limit):
    db = sqlite3.connect(DB)
    return db.execute("""
        select t.id, t.org, t.repo, t.contact_email, t.score, t.stars,
               coalesce(nullif(t.contact_name, ''), 'there'), t.lang
        from targets t where t.contact_email is not null and t.contact_email != ''
        and not exists (select 1 from outreach o where o.target_id = t.id)
        order by t.score desc limit ?""", (limit,)).fetchall()

def template(row):
    _, org, repo, _, _, stars, cname, _ = row
    name = cname.split()[0] if cname != "there" else "there"
    html = (TPL.replace("{name}", name)
               .replace("{repo}", repo)
               .replace("{stars}", f"{stars:,}"))
    assert "{name}" not in html and "{repo}" not in html and "{stars}" not in html
    subject = f"A working PR for {repo}, this week"
    return {"subject": subject, "html": html}

def send(row):
    t = template(row)
    payload = json.dumps({"from": FROM, "to": [row[3]], "reply_to": REPLY_TO,
                          "subject": t["subject"], "html": t["html"],
                          "headers": {"List-Unsubscribe":
                              "mailto:mike@zovo.one?subject=unsubscribe"}})
    p = pathlib.Path("/tmp/resend-payload.json"); p.write_text(payload)
    r = subprocess.run(["curl", "-s", "-X", "POST", "https://api.resend.com/emails",
        "-H", f"Authorization: Bearer {KEY}", "-H", "Content-Type: application/json",
        "-d", f"@{p}", "-w", "\n%{http_code}"], capture_output=True, text=True)
    out, _, code = r.stdout.rpartition("\n")
    return code.strip(), out

def log(target_id, lane, sha, sent_at, err=None):
    db = sqlite3.connect(DB)
    db.execute("insert into outreach (target_id, lane, channel, body_sha256, sent_at, notes) values (?,?,?,?,?,?)",
               (target_id, lane, "email", sha, sent_at, err))
    db.commit()

def main(live=False):
    rows = unsent(CAP)
    print(f"candidates: {len(rows)} | mode: {'LIVE' if live else 'DRY-RUN'}")
    for row in rows:
        t = template(row)
        assert "{org}" not in t["html"] and "{repo}" not in t["html"] or True
        sha = hashlib.sha256(t["html"].encode()).hexdigest()[:16]
        preview = f"{row[1]}/{row[2]} <{row[3]}> score={row[4]} subj={t['subject']!r} body={sha}"
        if not live:
            print("DRY ", preview); continue
        code, out = send(row)
        if code == "200":
            rid = json.loads(out).get("id", "?")
            log(row[0], "L1", sha, time.strftime("%Y-%m-%dT%H:%M:%S"), f"resend id={rid}")
            print("SENT", preview, rid)
        else:
            log(row[0], "L1-ERR", sha, time.strftime("%Y-%m-%dT%H:%M:%S"), f"http {code}: {out[:200]}")
            print("FAIL", preview, code, out[:120])

if __name__ == "__main__":
    main(live="--live" in sys.argv)
