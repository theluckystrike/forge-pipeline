import json
fixes = {
"11688|text": "Jeder [[Sternengezücht]]-Gegner verliert Patrouille sowie seine aufgedruckten <b>Beute</b>-Anweisungen und erhält Jäger sowie „<b>Beute</b> - Du.“\n[tdc_rune_u] · [tdc_rune_x] · [tdc_rune_o] · [tdc_rune_o] · [tdc_rune_d] · [tdc_rune_f] · [tdc_rune_z]\n[fast] Erschöpfe Horror in Ton: Behandle entweder das aufgedruckte Textfeld dieses Vorteils bis zum Ende der Runde, als ob es leer wäre <i>(mit Ausnahme der Merkmale)</i>, oder bewege einen [[Sternengezücht]]-Gegner einmal in eine beliebige Richtung."
}
json.dump(fixes, open('/tmp/tdc_extra_fixes7.json','w'), ensure_ascii=False, indent=1)
T=json.load(open('/tmp/tdc_de_all.json'))
T.update(fixes)
json.dump(T,open('/tmp/tdc_de_all.json','w'),ensure_ascii=False,indent=1)
print('done', len(T))
