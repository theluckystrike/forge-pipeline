import sys, json, subprocess
repos=[l.strip() for l in open(sys.argv[1]) if l.strip()]
frag="""r%d: repository(owner:"%s",name:"%s"){ nameWithOwner stargazerCount pushedAt isFork licenseInfo{spdxId} primaryLanguage{name} languages(first:20){totalSize} defaultBranchRef{target{... on Commit{history{totalCount}}}} mergedPRs: pullRequests(states:MERGED){totalCount} owner{__typename login ... on Organization{websiteUrl isVerified} } }"""
out=[]
for i in range(0,len(repos),15):
    chunk=repos[i:i+15]
    q="{"+" ".join(frag%(j,r.split('/')[0],r.split('/')[1]) for j,r in enumerate(chunk))+"}"
    res=subprocess.run(["gh","api","graphql","-f","query="+q],capture_output=True,text=True)
    try: d=json.loads(res.stdout)["data"]
    except Exception as e: print("ERR",res.stdout[:300],res.stderr[:300],file=sys.stderr); continue
    for j,r in enumerate(chunk):
        x=d.get("r%d"%j)
        if not x: out.append([r,"ERR"]); continue
        out.append([x["nameWithOwner"], (x["defaultBranchRef"] or {}).get("target",{}).get("history",{}).get("totalCount",0), x["mergedPRs"]["totalCount"], x["owner"]["__typename"], x["owner"].get("websiteUrl") or "", x["owner"].get("isVerified",False), (x["licenseInfo"] or {}).get("spdxId","NONE"), x["stargazerCount"], x["pushedAt"][:10], (x["primaryLanguage"] or {}).get("name",""), x["languages"]["totalSize"], x["isFork"]])
for row in out: print("\t".join(str(c) for c in row))
