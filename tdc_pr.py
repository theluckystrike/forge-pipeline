import json,subprocess,tempfile,os

body = """This adds German translations for The Drowned City campaign expansion.

Covers 286 card texts and 98 subnames across tdcc.json. Terminology follows the German edition rulebook (Flutstufe, Alarmiert, Erbarmungslos, Patrouille, Zurückschlagen, Cthulhus Zorn) and uses the du form consistent with the existing German files. Tokens, traits and rune markers are unchanged.

Closes #1801."""

payload={'title':'German translation of The Drowned City campaign cards',
 'head':'theluckystrike:de/tdcc','base':'master','body':body}
f=tempfile.NamedTemporaryFile('w',suffix='.json',delete=False)
json.dump(payload,f); f.close()
r=subprocess.run(['gh','api','-X','POST','repos/Kamalisk/arkhamdb-json-data/pulls',
                  '--input',f.name],capture_output=True,text=True)
d=json.loads(r.stdout)
print(d.get('number'),d.get('state'),d.get('html_url'),d.get('mergeable'))
os.unlink(f.name)
