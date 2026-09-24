import re,json,glob,sys,collections
def stats(f):
    s=open(f,encoding='utf-8',errors='ignore').read()
    m=re.search(r'"CollectiveStatsType","id":\d+,"balance":(-?\d+),"yearlyBudget":(-?\d+)',s)
    r12=re.search(r'totalAmountReceived\(\{\\"periodInMonths\\":12\}\)":\{"__typename":"Amount","valueInCents":(\d+)',s)
    tot=re.search(r'"totalAmountReceived":\{"__typename":"Amount","valueInCents":(\d+)',s)
    spent=re.search(r'"totalAmountSpent[^}]*?"value":(-?[\d.]+)',s)
    snap=re.search(r'web/(\d{14})',s)
    name=re.search(r'<title>([^<]*)</title>',s)
    goals=[]
    g=re.search(r'"goals":(\[\{.*?\}\])',s)
    if g:
        try:
            for x in json.loads(g.group(1)): goals.append((x.get('title'),x.get('amount'),(x.get('description') or '')[:200]))
        except: pass
    return dict(balance=int(m.group(1))/100 if m else None, yearlyBudget=int(m.group(2))/100 if m else None, received12=int(r12.group(1))/100 if r12 else None, totalReceived=int(tot.group(1))/100 if tot else None, title=name.group(1) if name else '', goals=goals)
def expenses(f):
    s=open(f,encoding='utf-8',errors='ignore').read()
    seen=set(); out=[]
    for m in re.finditer(r'"Expense:([^"]+)":\{(.*?)\},"(?:Expense|ExpensePermissions|Individual|Amount|Host|Organization|Collective|Vendor)',s):
        if m.group(1) in seen: continue
        seen.add(m.group(1)); b=m.group(2)
        d=re.search(r'"description":"(.*?)"',b); a=re.search(r'"amount":(\d+)',b); c=re.search(r'"createdAt":"([^"]+)"',b); st=re.search(r'"status":"([A-Z_]+)"',b); pay=re.search(r'"payee":\{"__ref":"([^"]+)"',b); t=re.search(r'"type":"([A-Z]+)"',b)
        out.append((c.group(1)[:10] if c else '?', st.group(1) if st else '?', t.group(1) if t else '?', int(a.group(1))/100 if a else 0, pay.group(1) if pay else '?', d.group(1) if d else '?'))
    return out
for s in sys.argv[1:]:
    print('=====',s)
    for pat in [f'wb2_{s}_page.out',f'wb_{s}_page.out']:
        try: st=stats(pat); print('STATS',pat,st); break
        except FileNotFoundError: pass
    for pat in [f'wb2_{s}_exp.out',f'wb_{s}_exp.out']:
        try:
            ex=expenses(pat); paid=[e for e in ex if e[1]=='PAID']
            print('EXP file',pat,'n',len(ex),'paid',len(paid),'paid total',round(sum(e[3] for e in paid),2),'distinct payees',len(set(e[4] for e in paid)), 'date range', min((e[0] for e in ex),default=''), max((e[0] for e in ex),default=''))
            for e in ex[:12]: print('  ',e[0],e[1],e[2],e[3],e[4][:14],'|',e[5][:60])
            break
        except FileNotFoundError: pass
