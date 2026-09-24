import sys,glob
for f in sorted(glob.glob("q_*.tsv")):
    rows=[l.rstrip("\n").split("\t") for l in open(f) if "\tERR" not in l and l.strip()]
    n=len(rows); org=[r for r in rows if r[3]=="Organization"]
    c=[r for r in rows if int(r[1])>=1000]; p=[r for r in rows if int(r[2])>=100]
    cp=[r for r in rows if int(r[1])>=1000 and int(r[2])>=100]
    full=[r for r in cp if r[3]=="Organization"]
    fullsite=[r for r in full if r[4]]
    copyleft=[r for r in full if r[6] in ("GPL-3.0","GPL-2.0","AGPL-3.0","LGPL-3.0","LGPL-2.1","MPL-2.0")]
    print(f"{f}\tn={n}\torg={len(org)}\tcommits>=1000={len(c)}\tmergedPR>=100={len(p)}\tboth={len(cp)}\tboth+org={len(full)}\tboth+org+website={len(fullsite)}\tcopyleft_among_pass={len(copyleft)}")
    if f=="q_named.tsv":
        for r in full: print("   PASS", r[0], r[1], r[2], r[4], r[6], "codeMB=%.1f"%(int(r[10])/1e6))
