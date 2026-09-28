import json

fixes = {
"11532b|text": "<blockquote><i>Du drückst drei kleine, versteckte Knöpfe in der Gewölbetür ein, und sie gleitet mit einem zufriedenen Zischen auf. Im Inneren befindet sich die vertrocknete Leiche einer fremdartigen Kreatur, ihr oktopoder Gesichter und ledrigen Flügel sind zu Staub zerfallen. In einer knochigen Hand hält sie eine Tafel aus Obsidian; du erkennst darin eine Art Stadtkarte, vermutlich von R'lyeh selbst.</i></blockquote>\nDu entdeckst diese Glyphe:\n[tdc_rune_z]\nNotiere in deinem Kampagnenlogbuch „Fremdling“ unter [tdc_rune_z] im Glyphenprotokoll. Diese Glyphe wurde übersetzt. Füge diese Karte dem Siegespunktestapel hinzu.",
"11537b|text": "Gewaltig. Patrouille (nächstgelegener nicht überfluteter oder teilweise überfluteter Ort). <b>Erscheinen</b> - Barrierekern.\nDer Seegrundleviathan bekommt +3 [per_investigator] Gesundheit.\n<b>Erzwungen</b> - Wenn die Gegnerphase beginnt, falls dieser Gegner spielbereit ist: Erhöhe die Flutstufe seines Ortes.",
"11626|text": "Dieser Ort bekommt -1 Schleier für jede [[Glyphe]]-Karte im Siegespunktestapel.\n<b>Erzwungen</b> - Sobald dieser Ort enthüllt wird: Erschaffe den beiseitegelegten Sternengezücht-Beobachter an diesem Ort.\n[action]: <b>Bewegen.</b> Bewege dich zu einem enthüllten [[Durchgang]]-Ort.",
"11627|text": "<b>Erzwungen</b> - Nachdem du 1 oder mehr Karten von der Oberseite des Begegnungsdecks ablegst, während du am Erhabenen Steg bist: Der nächstgelegene spielbereite Nicht-[[Elite]]-Gegner löst sich von jedem Ermittler und bewegt sich zu diesem Ort.",
"11628|text": "Die Leuchtenden Archive bekommen +1 Schleier für jede [[Glyphe]]-Karte an diesem Ort oder die an ihn angehängt ist.\n[fast] Gib X Aktionen aus (mindestens 1): Durchsuche den Ablagestapel des Begegnungsdecks nach bis zu X [[Glyphe]]-Karten und ziehe sie, einzeln nacheinander.\n[action]: <b>Bewegen.</b> Bewege dich zu einem enthüllten [[Durchgang]]-Ort.",
"11629|text": "<b>Erzwungen</b> - Wenn die Ermittlungsphase endet, falls sich Hinweise auf den Leuchtenden Archiven befinden: Mische jede an diesen Ort angehängte [[Glyphe]]-Verratskarte in das Begegnungsdeck.\n[action][action]: Durchsuche den Ablagestapel des Begegnungsdecks nach einer [[Glyphe]]-Karte und ziehe sie.",
"11630|text": "Falls die Ermittler 10 oder mehr Glyphen übersetzt haben, erhält dieser Gegner Unnachgiebig.\n<b>Erzwungen</b> - Wenn du diesen Gegner besiegst, entdecke diese Glyphe:\n[tdc_rune_k]\nNotiere in deinem Kampagnenlogbuch „Träume“ unter [tdc_rune_k] im Glyphenprotokoll. Diese Glyphe wurde übersetzt.",
"11631|text": "Falls die Ermittler 10 oder mehr Glyphen übersetzt haben, erhält dieser Gegner Alarmiert und Zurückschlagen.\n<b>Erzwungen</b> - Wenn du diesen Gegner besiegst, entdecke diese Glyphe:\n[tdc_rune_j]\nNotiere in deinem Kampagnenlogbuch „Schlaf“ unter [tdc_rune_j] im Glyphenprotokoll. Diese Glyphe wurde übersetzt.",
"11639|text": "Leicht / Standard\n[skull]: -X. X ist die aktuelle Sturmintensität.\n[cultist]: -4. Falls diese Probe misslingt, platziere 1 Verderben auf den nächstgelegenen Gegner.\n[tablet]: -1 für jeden offenen Himmel, der an deinen aktuellen Ort angrenzt.\n[elder_thing]: -2. Falls sich ein Gegner an deinem Ort befindet, enthülle einen weiteren Marker.",
"11640|text": "<b>Erzwungen</b> - Wenn die Runde endet, enthülle genauso viele Marker aus dem Chaosbeutel, wie die Sturmintensität beträgt. Falls ein Nicht-[elder_sign]-Symbolmarker enthüllt wird:\n- Mische die rechtesten offenen Himmel/[[Gipfel]]-Orte in den Reihen 2 und 4 und lege sie oben auf das Gipfeldeck (oder lege sie stattdessen in den Siegespunktestapel, falls sie <b>Sieg X</b> haben und keine Hinweise auf ihnen liegen). Jeder Gegner, jeder Marker und jedes Anhängsel an jenen Orten wird mit ihnen abgelegt.",
"11640b|text": "<b>Erzwungen</b> - Wenn die Runde endet, enthülle genauso viele Marker aus dem Chaosbeutel, wie die Sturmintensität beträgt. Falls ein Nicht-[elder_sign]-Symbolmarker enthüllt wird:\n- Mische die linktesten offenen Himmel/[[Gipfel]]-Orte in den Reihen 1 und 3 und lege sie oben auf das Gipfeldeck (oder lege sie stattdessen in den Siegespunktestapel, falls sie <b>Sieg X</b> haben und keine Hinweise auf ihnen liegen). Jeder Gegner, jeder Marker und jedes Anhängsel an jenen Orten wird mit ihnen abgelegt.",
"11641|text": "Jeder Nicht-Schwäche-Gegner darf den offenen Himmel betreten oder verlassen, als ob er ein Ort wäre.\nJeder Ort ist mit jedem ihm <i>(und dem offenen Himmel)</i> angrenzenden Ort verbunden.\n<b>Erzwungen</b> - Sobald der Ort eines Ermittlers das Spiel verlassen würde: Bewege jenen Ermittler zu einem beliebigen [[Zentral]]-Ort. Er nimmt 2 direkten Schaden.",
"11642|text": "Jeder Nicht-Schwäche-Gegner darf den offenen Himmel betreten oder verlassen, als ob er ein Ort wäre.\nJeder Ort ist mit jedem ihm <i>(und dem offenen Himmel)</i> angrenzenden Ort verbunden.\n<b>Erzwungen</b> - Sobald der Ort eines Ermittlers das Spiel verlassen würde: Bewege jenen Ermittler zu einem beliebigen [[Zentral]]-Ort. Er nimmt 2 direkten Schaden.",
"11643|text": "[action] Gib X Hinweise aus: Enthülle X Karten von der Unterseite des Gipfeldecks. Du darfst 1 enthüllten Ort in einem angrenzenden offenen Himmel ins Spiel bringen und dich dorthin bewegen. <i>(Lege jene offene-Himmel-Karte und jede andere enthüllte Karte in beliebiger Reihenfolge oben auf das Gipfeldeck zurück.)</i>\n<b>Ziel</b> - Falls jeder überlebende Ermittler an der Zentralen Turmspitze ist, rücke vor.",
"11644|text": "[action] Gib X Hinweise aus: Enthülle X Karten von der Unterseite des Gipfeldecks. Du darfst 1 enthüllten Ort in einem angrenzenden offenen Himmel ins Spiel bringen und dich dorthin bewegen. <i>(Lege jene offene-Himmel-Karte und jede andere enthüllte Karte in beliebiger Reihenfolge oben auf das Gipfeldeck zurück.)</i>\n<b>Ziel</b> - Falls jeder überlebende Ermittler aufgegeben hat, rücke vor.",
"11645|text": "[action] Gib X Hinweise aus: Enthülle X Karten von der Unterseite des Gipfeldecks. Du darfst 1 enthüllten Ort in einem angrenzenden offenen Himmel ins Spiel bringen und dich dorthin bewegen. <i>(Lege jene offene-Himmel-Karte und jede andere enthüllte Karte in beliebiger Reihenfolge oben auf das Gipfeldeck zurück.)</i>\n<b>Ziel</b> - Falls jeder überlebende Ermittler an der Zentralen Turmspitze ist, rücke vor.",
"11646|text": "[action] Gib X Hinweise aus: Enthülle X Karten von der Unterseite des Gipfeldecks. Du darfst 1 enthüllten Ort in einem angrenzenden offenen Himmel ins Spiel bringen und dich dorthin bewegen. <i>(Lege jene offene-Himmel-Karte und jede andere enthüllte Karte in beliebiger Reihenfolge oben auf das Gipfeldeck zurück.)</i>\n<b>Ziel</b> - Falls jeder überlebende Ermittler an der Schwebenden Turmspitze ist, rücke vor.",
"11647|text": "[action] Gib X Hinweise aus: Enthülle X Karten von der Unterseite des Gipfeldecks. Du darfst 1 enthüllten Ort in einem angrenzenden offenen Himmel ins Spiel bringen und dich dorthin bewegen. <i>(Lege jene offene-Himmel-Karte und jede andere enthüllte Karte in beliebiger Reihenfolge oben auf das Gipfeldeck zurück.)</i>\n<b>Ziel</b> - Falls jeder überlebende Ermittler aufgegeben hat, rücke vor.",
"11648|text": "Die Straßen von R'lyeh können nicht bewegt werden und können das Spiel nicht verlassen.\n[action] Gib 1-3 Ressourcen aus: Platziere genauso viele Hinweise <i>(aus dem Markervorrat)</i> auf einem beliebigen enthüllten Ort. (Limit einmal pro Runde.)",
"11649|text": "Die Zentrale Turmspitze kann nicht bewegt werden und kann das Spiel nicht verlassen.\n[action] Gib 1-3 Ressourcen aus: Platziere genauso viele Hinweise <i>(aus dem Markervorrat)</i> auf einem beliebigen enthüllten Ort. (Limit einmal pro Runde.)",
"11650|text": "Die Schwebende Turmspitze kann nicht bewegt werden und kann das Spiel nicht verlassen.\n[action] Gib 1-3 Ressourcen aus: Platziere genauso viele Hinweise <i>(aus dem Markervorrat)</i> auf einem beliebigen enthüllten Ort. (Limit einmal pro Runde.)",
"11651|text": "Der Westwall kann nicht bewegt werden und kann das Spiel nicht verlassen.\n<b>Erzwungen</b> - Nachdem du diesen Ort enthüllst: Ziehe die beiseitegelegte Verratskarte Erodierter Fries [tdc_rune_e].\n[action]: <b>Aufgeben.</b> Du kletterst herab.",
"11652|text": "Die Uralte Kuppel kann nicht bewegt werden und kann das Spiel nicht verlassen.\n<b>Erzwungen</b> - Nachdem du diesen Ort enthüllst: Ziehe die beiseitegelegte Verratskarte Erodierter Fries [tdc_rune_e].\n[action]: <b>Aufgeben.</b> Du kletterst herab.",
"11662|text": "Falls das Glyphen-Planetarium [tdc_rune_d] das Spiel verlassen würde, lege es beiseite, außerhalb des Spiels (oder in den Siegespunktestapel, falls keine Hinweise auf ihm liegen).\n<b>Erzwungen</b> - Sobald du diesen Ort betreten würdest, falls du nicht die Obsidianklaue kontrollierst: Du musst entweder 1 Hinweis ausgeben oder eine [agility]-Probe (2) ablegen. Falls die Probe misslingt, hebe die Effekte der Bewegung auf.\n[action] Gib 1 [per_investigator] Hinweise aus, als Gruppe: Drehe diese Karte um.",
"11664b|text": "Du entdeckst diese Glyphe:\n[tdc_rune_e]\nNotiere in deinem Kampagnenlogbuch „Finsternis“ unter [tdc_rune_e] im Glyphenprotokoll. Diese Glyphe wurde übersetzt. Füge diese Karte dem Siegespunktestapel hinzu.",
"11666|text": "<b>Enthüllung</b> - Lege eine [willpower]-Probe (1) ab. Diese Probe bekommt +1 Schwierigkeit für jeden offenen Himmel, der an deinen Ort angrenzt. Für jeden Punkt, um den die Probe misslingt, musst du entweder 1 Aktion verlieren oder 1 Horror nehmen.",
"11667|text": "<b>Enthüllung</b> - Bringe Schwingen des Schreckens in deiner Bedrohungszone ins Spiel.\n<b>Erzwungen</b> - Nachdem du eine Fertigkeitsprobe misslingst: Lege Karten von der Oberseite des Begegnungsdecks ab, bis ein Gegner abgelegt wird. Entweder ziehst du jenen Gegner, oder er greift dich an <i>(vom Ablagestapel aus)</i>. Lege dann Schwingen des Schreckens ab.",
"11681|text": "<b>Erzwungen</b> - Wenn Cthulhu diesen Ort betritt: Jeder Ermittler entfernt die oberste Karte seines Decks aus dem Spiel.\n[action] Gib 1 [per_investigator] Hinweise aus: Platziere 1 Verderben auf dem Splitter von Y'ch'lecht. Ermittler an diesem Ort dürfen 1 [per_investigator] Hinweise ausgeben, als Gruppe, um 1 zusätzliches Verderben auf den Splitter von Y'ch'lecht zu platzieren.",
"11682|text": "Leicht / Standard\n[skull]: -X. X ist die halbe Anzahl an Orten ohne Szenariokarten darunter (aufgerundet).\n[cultist]: -3. Falls diese Probe misslingt, platziere 1 Verderben auf den nächstgelegenen Gegner ohne Verderben.\n[tablet]: -3. Falls diese Probe misslingt, platziere 1 deiner Hinweise auf deinem Ort.\n[elder_thing]: -2. Falls dein Ort überflutet ist, enthülle einen weiteren Marker.",
"11683|text": "[action]: <b>Aufgeben.</b> Du gibst deine Suche auf.\n<b>Erzwungen -</b> Wenn Verderben auf diese Agenda platziert wird: Erhöhe die Flutstufe vom Ort des führenden Ermittlers.",
"11714|text": "Senke die Flutstufe vom Ort Cthulhus und wähle einen anderen Ort (mit einem Ermittler, falls möglich), dessen Flutstufe erhöht werden kann. Erhöhe die Flutstufe des gewählten Ortes.\nJeder Ermittler an einem völlig überfluteten Ort legt eine [agility]-Probe (X) ab, wobei X Cthulhus Zorn ist. Falls die Probe misslingt, muss er entweder 1 Schaden nehmen oder ein Nicht-Story-Vorteil, den er kontrolliert, ablegen.",
"11722|text": "<b>Enthüllung</b> - Bringe Infiziert! in deiner Bedrohungszone ins Spiel. Limit 1 pro Ermittler.\n<b>Erzwungen</b> - Nachdem du deinen Zug an einem Ort beendet hast, an dem sich ein anderer Ermittler oder ein [[Blindpassagier]]-Gegner befindet: Platziere 1 Verderben auf Infiziert!\n[action]: Lege eine [willpower]-Probe (3) ab. Falls die Probe misslingt, nimm 1 Schaden. Falls sie gelingt, lege Infiziert! ab.",
"11724|text": "Zurückhaltend.\n<b>Erscheinen</b> - Beliebiger Ort (leer, falls möglich).\nSolange der Pilgerführer spielbereit ist, bekommt jeder andere [[Kultist]]-Gegner +2 Kampf und erhält Jäger und Unnachgiebig.",
}

p='/Users/mike/oss-pipeline/tdc_fix2.py'
import sys
sys.path.insert(0,'/Users/mike/oss-pipeline')

def replace_entries(path, fixes):
    lines=open(path).read().split('\n')
    out=[]
    skip=False
    for ln in lines:
        if skip:
            if ln.startswith('"') and ln.rstrip().endswith('",'):
                skip=False
            continue
        matched=False
        for k,v in fixes.items():
            if '"'+k+'"' in ln:
                out.append(v+',')
                skip=True
                matched=True
                break
        if not matched:
            out.append(ln)
    open(path,'w').write('\n'.join(out))

for key,val in fixes.items():
    code=key.split('|')[0]
    n=int(code[:1])  # not reliable; find chunk by searching
for n in range(6):
    p=f'/Users/mike/oss-pipeline/tdc_de_c{n}.py'
    s=open(p).read()
    mine={k:v for k,v in fixes.items() if '"'+k+'"' in s}
    if mine:
        replace_entries(p,mine)
        print(n, list(mine))
