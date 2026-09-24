import json, glob, os, re, csv, statistics
from datetime import datetime, timezone
D="/private/tmp/claude-501/-Users-mike-cloud-session-test/6a7524ee-68d0-4521-aef8-fbea27f1798b/scratchpad/r"
NOW=datetime(2026,9,24,16,30,tzinfo=timezone.utc)
ORDER=["medusajs/medusa","strapi/strapi","n8n-io/n8n","directus/directus","payloadcms/payload","supabase/supabase","RocketChat/Rocket.Chat","mattermost/mattermost","appwrite/appwrite","calcom/cal.diy","langgenius/dify","Infisical/infisical","hoppscotch/hoppscotch","ToolJet/ToolJet","baptisteArno/typebot.io","twentyhq/twenty","formbricks/formbricks","documenso/documenso","saleor/saleor","vendurehq/vendure"]
STRONG=["in production","our company","we use","our team","our customers","our store","our instance"]
PHRASES=["in production","our company","we use","our team","self-hosted","self hosted","enterprise","our customers","our store","our instance"]
MAINT={"MEMBER","OWNER","COLLABORATOR"}
PERSONAL_HOSTS=re.compile(r'(github\.io|github\.com|gitlab\.com|linkedin\.com|twitter\.com|x\.com|medium\.com|dev\.to|hashnode|substack|youtube|instagram|facebook|t\.me|telegram|discord|bsky|mastodon|vercel\.app|netlify\.app|pages\.dev|about\.me|bio\.link|linktr|notion\.site|wordpress\.com|blogspot|tumblr|codepen|stackoverflow|kaggle|leetcode|hackerrank|reddit|upwork|fiverr|calendly)', re.I)
BIO_RE=re.compile(r'\b(CTO|CEO|COO|founder|co-founder|cofounder|engineer at|developer at|engineer @|developer @|working at|work at|lead at|architect at|head of)\b', re.I)
users={}
for f in glob.glob(D+"/users/*.json"):
    try: u=json.load(open(f)); users[u["login"]]=u
    except Exception: pass
def classify(issue):
    if issue["user_type"]!="User": return "bot"
    if issue["author_association"] in MAINT: return "maintainer"
    u=users.get(issue["login"])
    if u is None: return "unfetched"
    if issue["login"]=="theluckystrike": return "operator"
    comp=(u.get("company") or "").strip()
    org,name=issue["repo"].split("/"); prod=re.sub(r'(-io|hq|-ecommerce|\.io|\.com|\.diy|js|cms)$','',name.lower())
    prod={"rocket.chat":"rocket","cal":"cal.com","cal.diy":"cal.com","dify":"dify","twenty":"twenty"}.get(prod,prod)
    if prod and (prod in comp.lower() or org.lower() in comp.lower().replace("@","") or (u.get("email") or "").lower().endswith("@"+prod+".com") or (u.get("email") or "").lower().endswith("@"+prod+".io")): return "vendor_staff"
    blog=(u.get("blog") or "").strip()
    bio=(u.get("bio") or "").strip()
    reasons=[]
    if comp: reasons.append("company:"+comp)
    if blog and not PERSONAL_HOSTS.search(blog):
        host=re.sub(r'^https?://','',blog).split('/')[0].lower()
        # crude personal-domain heuristic: host contains login or name token
        name=(u.get("name") or "").lower().split()
        if not (issue["login"].lower() in host or any(len(t)>3 and t in host for t in name)):
            reasons.append("blog:"+blog)
    if BIO_RE.search(bio): reasons.append("bio:"+bio.replace("\n"," ")[:80])
    issue["_reasons"]=reasons
    return "company_affiliated" if reasons else "anonymous"
rows=[]; per={}
for repo in ORDER:
    f=D+"/issues/"+{"calcom/cal.diy":"calcom_cal.com","vendurehq/vendure":"vendure-ecommerce_vendure"}.get(repo,repo.replace("/","_"))+".json"
    d=json.load(open(f)); items=d["items"]
    for it in items:
        it["cls"]=classify(it)
        body=(it["body"] or "")+" "+(it["title"] or "")
        bl=body.lower()
        it["sig"]=[p for p in PHRASES if p in bl]
        it["strong"]=[p for p in STRONG if p in bl]
        it["age"]=(NOW-datetime.fromisoformat(it["created_at"].replace("Z","+00:00"))).days
        L=[l.lower() for l in it["labels"]]
        it["hw"]=any("help wanted" in l or "help-wanted" in l for l in L)
        it["gfi"]=any("good first issue" in l or "good-first-issue" in l for l in L)
        it["bug"]=any("bug" in l for l in L)
        it["total_open"]=d.get("total")
        rows.append(it)
    per[repo]=items
def pct(n,d): return f"{100*n/d:.0f}%" if d else "n/a"
out=[]
out.append("| repo | open issues (search total) | sampled | maintainer (assoc.) | vendor staff (company field) | operator (theluckystrike) | company-affil. ext. | anonymous | unfetched/bot | any deployer phrase | strong first-person phrase | median age (d) | help wanted | good first issue | bug label | ext. co-affil. reporters (unique) | leads (co-affil + signal) |")
out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
tot={"n":0,"m":0,"v":0,"op":0,"c":0,"a":0,"o":0,"sig":0,"st":0,"hw":0,"gfi":0,"bug":0,"lead":0}; ages=[]; ext_all=set()
for repo in ORDER:
    items=per[repo]; n=len(items)
    m=sum(i["cls"]=="maintainer" for i in items); c=sum(i["cls"]=="company_affiliated" for i in items)
    a=sum(i["cls"]=="anonymous" for i in items); v=sum(i["cls"]=="vendor_staff" for i in items); op=sum(i["cls"]=="operator" for i in items); o=n-m-c-a-v-op
    sig=sum(bool(i["sig"]) for i in items); st=sum(bool(i["strong"]) for i in items); hw=sum(i["hw"] for i in items); gfi=sum(i["gfi"] for i in items); bug=sum(i["bug"] for i in items)
    ag=[i["age"] for i in items]; med=statistics.median(ag) if ag else 0
    ext=set(i["login"] for i in items if i["cls"]=="company_affiliated"); ext_all|=ext
    lead=sum(1 for i in items if i["cls"]=="company_affiliated" and i["sig"])
    total=items[0]["total_open"] if items else None
    out.append(f"| {repo} | {total if total else 'n/a (search 422)'} | {n} | {pct(m,n)} | {v} | {op} | {pct(c,n)} | {pct(a,n)} | {o} | {pct(sig,n)} | {pct(st,n)} | {med:.0f} | {pct(hw,n)} | {pct(gfi,n)} | {pct(bug,n)} | {len(ext)} | {lead} |")
    for k,v in zip(["n","m","v","op","c","a","o","sig","st","hw","gfi","bug","lead"],[n,m,v,op,c,a,o,sig,st,hw,gfi,bug,lead]): tot[k]+=v
    ages+=ag
n=tot["n"]
out.append(f"| **ALL** | | {n} | {pct(tot['m'],n)} | {tot['v']} | {tot['op']} | {pct(tot['c'],n)} | {pct(tot['a'],n)} | {tot['o']} | {pct(tot['sig'],n)} | {pct(tot['st'],n)} | {statistics.median(ages):.0f} | {pct(tot['hw'],n)} | {pct(tot['gfi'],n)} | {pct(tot['bug'],n)} | {len(ext_all)} | {tot['lead']} |")
open(D+"/table_per_repo.md","w").write("\n".join(out)+"\n")
# leads: company-affiliated external + deployer signal; rank by company field present, then comments, then recency
leads=[i for i in rows if i["cls"]=="company_affiliated" and i["sig"]]
def score(i):
    u=users[i["login"]]; return (1 if i["strong"] else 0, 1 if (u.get("company") or "").strip() else 0, i["hw"] or i["gfi"], -i["age"])
leads.sort(key=score, reverse=True)
with open(D+"/04-issue-reporters.csv","w",newline="") as fh:
    w=csv.writer(fh); w.writerow(["rank","repo","issue_url","title","author_login","company_field","blog","bio_excerpt","deployer_phrases","issue_age_days","labels","comments","classification_reasons"])
    for k,i in enumerate(leads[:40],1):
        u=users[i["login"]]
        w.writerow([k,i["repo"],i["html_url"],i["title"][:100],i["login"],(u.get("company") or ""),(u.get("blog") or ""),(u.get("bio") or "").replace("\n"," ")[:120],";".join(i["sig"]),i["age"],";".join(i["labels"]),i["comments"],";".join(i["_reasons"])])
# context snippets for top leads
snip=[]
for k,i in enumerate(leads[:40],1):
    bl=(i["body"] or "")
    p=(i["strong"] or i["sig"])[0]; idx=bl.lower().find(p)
    s=bl[max(0,idx-70):idx+90].replace("\n"," ").replace("|","/") if idx>=0 else i["title"]
    u=users[i["login"]]
    snip.append(f"| {k} | {i['repo']} | [#{i['number']}]({i['html_url']}) | {i['login']} | {(u.get('company') or '').replace('|','/')} | {', '.join(i['sig'])} | {i['age']} | \"...{s}...\" |")
open(D+"/leads_table.md","w").write("| # | repo | issue | author | company field | phrase(s) | age d | quoted context |\n|---|---|---|---|---|---|---|---|\n"+"\n".join(snip)+"\n")
# extra stats
print("rows",len(rows),"users fetched",len(users),"leads total",len(leads))
print("company field non-empty among fetched users:",sum(1 for u in users.values() if (u.get('company') or '').strip()),"/",len(users))
print("signal by class:",{c:(sum(bool(i['sig']) for i in rows if i['cls']==c),sum(1 for i in rows if i['cls']==c)) for c in ['maintainer','vendor_staff','operator','company_affiliated','anonymous','unfetched','bot']})
from collections import Counter
print("strong-signal leads:",sum(1 for i in leads if i["strong"]),"strong by class:",{c:sum(bool(i["strong"]) for i in rows if i["cls"]==c) for c in ["maintainer","company_affiliated","anonymous"]})
print("phrase counts:",Counter(p for i in rows for p in i["sig"]).most_common())
print("vendor_staff logins:",sorted(set((i["login"],i["repo"]) for i in rows if i["cls"]=="vendor_staff")))
print("operator issues by repo:",Counter(i["repo"] for i in rows if i["cls"]=="operator"))
print("issues with 0 comments:",sum(1 for i in rows if i['comments']==0),"/",len(rows))
print("company field top:",Counter((users[i['login']].get('company') or '').strip().lower() for i in rows if i['cls']=='company_affiliated').most_common(25))
