import json
fixes = {
"11532b|text": "<blockquote><i>Du drückst drei kleine, versteckte Knöpfe in der Gewölbetür ein, und sie gleitet mit einem zufriedenen Zischen auf. Im Inneren befindet sich die vertrocknete Leiche einer fremdartigen Kreatur, ihr oktopoder Gesicht und ihre ledrigen Flügel sind zu Staub zerfallen. In einer knochigen Hand hält sie eine Tafel aus Obsidian; du erkennst darin eine Art Stadtkarte, vermutlich von R'lyeh selbst.</i></blockquote>\nDu entdeckst diese Glyphe:\n[tdc_rune_z]\nNotiere in deinem Kampagnenlogbuch „Stadt“ unter [tdc_rune_z] im Glyphenprotokoll. Diese Glyphe wurde übersetzt. Füge diese Karte dem Siegespunktestapel hinzu.",
"11627|subname": "Archiv der Sterne",
"11627|text": "[reaction] Wenn 1 oder mehr Karten von der Oberseite des Begegnungsdecks abgelegt werden, wähle und lege 1 Karte von deiner Hand ab: Lege 2 zusätzliche Karten von der Oberseite des Begegnungsdecks ab.\n[action]: <b>Bewegen.</b> Bewege dich zu einem enthüllten [[Durchgang]]-Ort.",
"11628|subname": "Archiv der Alten",
"11628|text": "[reaction] Wenn 1 oder mehr Karten von der Oberseite des Begegnungsdecks abgelegt werden, erleide 1 direkten Horror: Lege 3 zusätzliche Karten von der Oberseite des Begegnungsdecks ab.",
"11629|subname": "Archiv der Träume",
"11629|text": "[reaction] Wenn 1 oder mehr Karten von der Oberseite des Begegnungsdecks abgelegt werden, nimm 1 Horror: Lege 2 zusätzliche Karten von der Oberseite des Begegnungsdecks ab.\n[action]: Lege eine [willpower]-Probe (3) ab. Falls die Probe misslingt, lege 1 Verderben auf die aktuelle Agenda.",
"11630|subname": "Archiv des Konflikts",
"11631|subname": "Archiv der Geschichte",
"11635|subname": "Im Turm gefangen",
"11635|text": "Gewaltig.\nDer Kolossale Tyrann bekommt +3 [per_investigator] Gesundheit und kann sich nicht bewegen.\n<b>Erzwungen</b> - Wenn die Gegnerphase endet, falls sich keine Ermittler am Ort des Kolossalen Tyrannen befinden: Füge jeder Karte mit geistiger Gesundheit an jedem angrenzenden Ort 1 direkten Horror zu.",
"11639|text": "[reaction] Sobald du 1 oder mehr Hinweise von deinem Ort entdeckst: Lege eine [willpower]-Probe (3) ab. Falls die Probe gelingt, entdecke die Glyphe:\n[tdc_rune_b]\nNotiere in deinem Kampagnenlogbuch „Pflanze“ unter [tdc_rune_b] im Glyphenprotokoll. Diese Glyphe wurde übersetzt.",
"11640|text": "[reaction] Nachdem du den letzten Hinweis an diesem Ort entdeckst: Du entdeckst diese Glyphe:\n[tdc_rune_c]\nNotiere in deinem Kampagnenlogbuch „Älteres Wesen“ unter [tdc_rune_c] im Glyphenprotokoll. Diese Glyphe wurde übersetzt.",
"11669|text": "Wagnis.\n<b>Enthüllung</b> - Du musst entscheiden (wähle eins):\n- Lege 1 Verderben auf die aktuelle Agenda. Dieser Effekt kann die aktuelle Agenda vorrücken lassen.\n- Jeder Ermittler erleidet 2 direkten Horror.\n- Wende den <b>Erzwungen</b>-Effekt auf der Story-Karte Westliche Winde/Östliche Winde an, als ob du einen Nicht-[elder_sign]-Symbolmarker gezogen hättest."
}
json.dump(fixes, open('/tmp/tdc_extra_fixes2.json','w'), ensure_ascii=False, indent=1)
print('written', len(fixes))
