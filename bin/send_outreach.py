#!/usr/bin/env python3
"""WhiteHERO v3 outreach sender. DRY RUN BY DEFAULT. Nothing leaves this machine without --arm,
and --arm currently stops at a transport stub on purpose (see outreach/SENDING.md).

Caps (plan section 5 and 10), counted from outreach.sent_at over channel 'email':
  8 per UTC day, 40 per rolling 7 days.
A draft is sendable only when all of these hold:
  it sits in outreach/queue/, it passes outreach_gate.check() again right now,
  its file name is listed in outreach/approved.txt (the owner's review sign-off),
  its outreach row has sent_at NULL and the same body_sha256 as the file,
  the target has a contact_email.

Usage:
  python3 bin/send_outreach.py                    dry run, list what would go out today
  python3 bin/send_outreach.py --full             dry run and print every sendable body
  python3 bin/send_outreach.py --arm              real send (raises NotImplementedError until the
                                                   owner selects a transport)
  python3 bin/send_outreach.py --mark-sent FILE   record a draft the owner sent by hand through
                                                   Porkbun webmail (sets sent_at, moves it to sent/)
"""
import argparse, os, shutil, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from outreach_lib import OUT, QUEUE, db, sha256, split_email, lane_from_filename
import outreach_gate

DAY_CAP, WEEK_CAP = 8, 40
APPROVED = os.path.join(OUT, "approved.txt")
SENT = os.path.join(OUT, "sent")


def transport_send(to_addr, subject, body, reply_to):
    raise NotImplementedError("owner selects transport: webmail or rotated Resend key")


def caps(conn):
    day = conn.execute("""select count(*) from outreach where channel='email' and sent_at is not null
                          and date(sent_at) = date('now')""").fetchone()[0]
    week = conn.execute("""select count(*) from outreach where channel='email' and sent_at is not null
                           and datetime(sent_at) > datetime('now','-7 days')""").fetchone()[0]
    return day, week, max(0, min(DAY_CAP - day, WEEK_CAP - week))


def approved():
    if not os.path.exists(APPROVED):
        return set()
    return {l.strip() for l in open(APPROVED, encoding="utf-8") if l.strip() and not l.startswith("#")}


def candidates(conn):
    out = []
    appr = approved()
    for f in sorted(os.listdir(QUEUE)) if os.path.isdir(QUEUE) else []:
        if not f.endswith(".txt"):
            continue
        p = os.path.join(QUEUE, f)
        tid, lane = lane_from_filename(f)
        text = open(p, encoding="utf-8").read()
        t = conn.execute("select * from targets where id=?", (tid,)).fetchone()
        row = conn.execute("select * from outreach where target_id=? and sent_at is null order by id desc limit 1",
                           (tid,)).fetchone()
        problems = [r for r, _ in outreach_gate.check(p, conn)]
        if f not in appr:
            problems.append("not in outreach/approved.txt")
        if row is None:
            problems.append("no unsent outreach row")
        elif row["body_sha256"] != sha256(text):
            problems.append("sha mismatch")
        if t is None or not t["contact_email"]:
            problems.append("no contact_email")
        out.append(dict(file=f, path=p, tid=tid, lane=lane, text=text, target=t, row=row, problems=problems))
    return out


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--arm", action="store_true")
    g.add_argument("--mark-sent")
    ap.add_argument("--full", action="store_true")
    args = ap.parse_args()
    conn = db()
    day, week, room = caps(conn)
    print(f"sent today {day}/{DAY_CAP}, last 7 days {week}/{WEEK_CAP}, room now {room}")

    if args.mark_sent:
        f = os.path.basename(args.mark_sent)
        c = [x for x in candidates(conn) if x["file"] == f]
        if not c:
            sys.exit(f"{f} is not in outreach/queue/")
        c = c[0]
        if c["problems"]:
            sys.exit(f"refusing to record {f}: {', '.join(c['problems'])}")
        if room <= 0:
            sys.exit("cap reached: 8 per day or 40 per week. Do not send more today.")
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("update outreach set sent_at=?, notes='sent via webmail' where id=?", (ts, c["row"]["id"]))
        conn.commit()
        os.makedirs(SENT, exist_ok=True)
        shutil.move(c["path"], os.path.join(SENT, f))
        print(f"recorded {f} sent_at={ts} (outreach id {c['row']['id']})")
        return

    cands = candidates(conn)
    ready = [c for c in cands if not c["problems"]]
    batch = ready[:room]
    print(f"queued {len(cands)}, sendable {len(ready)}, would send now {len(batch)}")
    for c in cands:
        hdr, body = split_email(c["text"])
        mark = "SEND" if c in batch else ("HOLD" if not c["problems"] else "BLOCK")
        to = c["target"]["contact_email"] if c["target"] else "?"
        why = "" if not c["problems"] else "  [" + "; ".join(c["problems"]) + "]"
        print(f"{mark} {c['file']} to={to} subject={hdr.get('subject','')!r}{why}")
        if args.full and mark == "SEND":
            print("-" * 60 + "\n" + c["text"] + "-" * 60)
    if not args.arm:
        print("dry run: nothing sent. Add --arm to send (transport is a stub until the owner picks one).")
        return
    for c in batch:
        hdr, body = split_email(c["text"])
        transport_send(c["target"]["contact_email"], hdr["subject"], body, hdr.get("reply-to"))


if __name__ == "__main__":
    main()
