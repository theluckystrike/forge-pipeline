#!/usr/bin/env python3
"""anvil_dataset.py — build + store the ANVIL dataset from live data.
Sources: kpi.db contributions, live gh PR state, outreach state.
Output: /Users/mike/oss-pipeline/state/anvil_dataset.csv + .json (regenerated each run, always up to date).
"""
import sqlite3, json, csv, subprocess, datetime, sys

STATE="/Users/mike/oss-pipeline/state"
NOW=datetime.datetime.now(datetime.timezone.utc)

def gh(url, jq):
    r=subprocess.run(["gh","api",url,"--jq",jq],capture_output=True,text=True)
    return r.stdout.strip()

# 1) kpi.db -> contribution rows
db=sqlite3.connect(f"{STATE}/kpi.db"); db.row_factory=sqlite3.Row
rows=[dict(r) for r in db.execute("SELECT * FROM contributions ORDER BY id")]

# 2) live-verify the credential PRs (the revenue engine)
CRED=[("janhq/jan",9054),("calcom/cal.diy",30229),("calcom/cal.diy",30230),("toss/react-simplikit",523),("hoppscotch/hoppscotch",6669)]
live=[]
for repo,pr in CRED:
    s=gh(f"repos/{repo}/pulls/{pr}", '.state+"|"+(.mergeable|tostring)+"|"+(.additions|tostring)+"|"+(.comments|tostring)')
    st=s.split("|") if s else ["unknown"]*4
    live.append({"repo":repo,"pr":pr,"state":st[0],"mergeable":st[1] if len(st)>1 else "?","additions":st[2] if len(st)>2 else "?","comments":st[3] if len(st)>3 else "?"})

# 3) dataset rows: one per contribution + live state for credential PRs
ds=[]
for r in rows:
    d={"id":r.get("id"),"repo":r.get("repo"),"pr":r.get("pr") or r.get("issue") or "",
       "category":r.get("category",""),"status":r.get("status",""),"ts":r.get("ts","")}
    lv=next((x for x in live if x["repo"]==r.get("repo") and str(x["pr"])==str(d["pr"])),None)
    if lv: d.update({"live_state":lv["state"],"mergeable":lv["mergeable"],"additions":lv["additions"]})
    ds.append(d)

# 4) summary metrics (the ROI layer)
tot=len(ds)
merged=sum(1 for d in ds if d["status"].upper()=="MERGED")
cred_rows=[d for d in ds if d["repo"] in ("janhq/jan","calcom/cal.diy","toss/react-simplikit","hoppscotch/hoppscotch","medusajs/medusa")]
summary={
  "generated": NOW.isoformat(),
  "total_contributions": tot,
  "merged": merged,
  "open": sum(1 for d in ds if d["status"].lower()=="open"),
  "closed": sum(1 for d in ds if d["status"].upper()=="CLOSED"),
  "credential_prs_live": live,
  "outreach": {"twenty_d0_sent":"2026-09-24","jan_queued":True,"cadence":"D+4 09-28, D+10 10-04"},
  "sprints_today": ["RO-1 jan#9054 zh-CN 670 keys","RO-2 cal.diy#30229 zh-CN 235 keys","RO-5 cal.diy#30230 th 4769 keys"]
}

json.dump({"summary":summary,"contributions":ds},open(f"{STATE}/anvil_dataset.json","w"),indent=1)
keys=sorted({k for d in ds for k in d})
with open(f"{STATE}/anvil_dataset.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=keys,restval=""); w.writeheader(); w.writerows(ds)
print(json.dumps(summary,indent=1))
print("stored:", f"{STATE}/anvil_dataset.json", f"{STATE}/anvil_dataset.csv")
