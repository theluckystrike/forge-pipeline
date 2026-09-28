import json
import sys
sys.path.insert(0,'/Users/mike/oss-pipeline')
from tdc_fix import replace_entries

fixes = {
"11637": "\"11637|text\": \"Alarmiert.\\n<b>Erscheinen</b> - Höchste Stufe ohne Ermittler.\\n<b>Beute</b> - Niedrigster [agility]-Wert.\\n<b>Erzwungen</b> - Wenn die Gegnerphase beginnt, falls dieser Gegner spielbereit und nicht im Kampf verbunden ist: Bewegt er sich zum Ort seiner Beute.\",",
"11650": "\"11650|text\": \"Die Schwebende Turmspitze kann nicht bewegt werden und kann das Spiel nicht verlassen.\\n[action] Gib 1-3 Ressourcen aus: Lege entsprechend viele Hinweise <i>(aus dem Markervorrat)</i> auf einen beliebigen enthüllten Ort. (Nur ein Mal pro Runde.)\",",
"11651": "\"11651|text\": \"Der Westwall kann nicht bewegt werden und kann das Spiel nicht verlassen.\\n<b>Erzwungen</b> - Nachdem du diesen Ort enthüllst: Ziehe die beiseitegelegte Verratskarte Erodierter Fries [tdc_rune_e].\\n[action]: <b>Aufgeben.</b> Du steigst herab.\",",
"11652": "\"11652|text\": \"Die Uralte Kuppel kann nicht bewegt werden und kann das Spiel nicht verlassen.\\n<b>Erzwungen</b> - Nachdem du diesen Ort enthüllst: Ziehe die beiseitegelegte Verratskarte Erodierter Fries [tdc_rune_e].\\n[action]: <b>Aufgeben.</b> Du steigst herab.\",",
"11664": "\"11664|text\": \"<b>Enthüllung</b> - Hänge den Erodierten Fries [tdc_rune_e] an deinen Ort an. Kann nicht aufgehoben werden. Falls der Erodierte Fries [tdc_rune_e] das Spiel verlassen würde, lege ihn beiseite, außerhalb des Spiels.\\n[action]: Lege eine [combat]- oder [intellect]-Probe (3) ab. Falls die Probe misslingt, nimm 1 Schaden. Lege andernfalls 1 Ressource auf diese Karte. Falls sich 1 [per_investigator] Ressourcen auf dem Erodierten Fries [tdc_rune_e] befinden, drehe ihn um und handle seinen Text ab.\",",
}
p='/Users/mike/oss-pipeline/tdc_de_c3.py'
T=replace_entries(p,fixes)
for k in fixes:
    print(k, T[k+'|text'][:60].replace('\n',' | '))
