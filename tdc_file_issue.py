# Use python subprocess with tempfile JSON to avoid shell mangling
import json,subprocess,tempfile

body = """The German translations for The Drowned City campaign expansion (translations/de/pack/tdc/tdcc.json) are still missing for most cards. Comparing the German file against the English pack file, 374 fields are untranslated (276 card texts and 98 subnames), covering all acts, agendas, locations and enemies of the campaign, for example:

- 11503 (act): "[reaction] After the last clue is discovered from an [[Arkham]] location: Discard the top 3 cards of the encounter deck..." is identical to the English text
- 11701 (Cthulhu, subname "Ancient Evil") and its three enemy cards 11702/11703/11704 are untranslated
- All rooftop locations 11692-11700 and the story assets 11687/11688 show English texts

For comparison, the investigator expansion (tdcp.json) is complete, and the French campaign file got filled in recently. I have a complete German draft for all 374 fields ready, translated against the terminology of the German edition rulebook (Flutstufe, Flutmarker, Alarmiert, Erbarmungslos, Zurückschlagen, Cthulhus Zorn, etc.). I would open a PR against translations/de/pack/tdc/tdcc.json that closes this issue. Happy to split it up if a full-file change is easier to review in parts."""

payload = {
    "title": "German translation of The Drowned City campaign cards",
    "body": body,

}
import os
f=tempfile.NamedTemporaryFile('w',suffix='.json',delete=False)
json.dump(payload,f); f.close()
r=subprocess.run(['gh','api','-X','POST','repos/Kamalisk/arkhamdb-json-data/issues','--input',f.name,'--jq','{number,html_url,state}'],capture_output=True,text=True)
print(r.stdout or r.stderr)
os.unlink(f.name)
