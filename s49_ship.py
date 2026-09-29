# S49: append missing de translations to WiVRn PR #1136 branch (update_pr branch name?), via Contents API.
import subprocess,json,base64,tempfile,os,sys,polib
REPO='theluckystrike/WiVRn'
# find my PR branch
BR='de-translations-1007'
print('PR branch:',BR)
def get(p,ref):
    d=subprocess.run(['gh','api',f'repos/{REPO}/contents/{p}?ref={ref}'],capture_output=True,text=True)
    j=json.loads(d.stdout)
    return j['sha'], base64.b64decode(j['content']).decode()

CLIENT={
 "Use 'auto' to select the refresh rate based on measured application performance. May cause flicker when a change happens.": "Wählen Sie „auto“, um die Bildwiederholfrequenz anhand der gemessenen Anwendungsleistung zu wählen. Kann bei Änderungen flimmern.",
 "Video": "Video",
 "Frame rate and resolution.": "Bildwiederholfrequenz und Auflösung.",
 "Foveation center override": "Override des Foveationszentrums",
 "Change": "Ändern",
 "Disable in-stream window": "In-Stream-Fenster deaktivieren",
 "Disable audio filters, such as noise cancellation.": "Audiofilter wie die Geräuschunterdrückung deaktivieren.",
 "System language": "Systemsprache",
 "USB networking": "USB-Netzwerk",
 "Debug": "Debug",
 "About": "Über",
 "Exit": "Beenden",
 "Applications": "Anwendungen",
 "Stop all applications": "Alle Anwendungen beenden",
 "The following applications/overlays are open:": "Folgende Anwendungen/Overlays sind geöffnet:",
 "Start": "Starten",
 "Statistics overlay": "Statistik-Overlay",
 "Compact view": "Kompakte Ansicht",
 "Do you really want to disable the in-stream window?\nYou will not be able to re-open it with the thumbsticks.": "Möchten Sie das In-Stream-Fenster wirklich deaktivieren?\nSie können es nicht mehr mit den Thumbsticks wieder öffnen.",
 "Enables connection by USB without ADB or developer mode.\nMake sure the server allows IPv6 link-local only connections.": "Ermöglicht die Verbindung per USB ohne ADB oder Entwicklermodus.\nStellen Sie sicher, dass der Server nur IPv6-Link-Local-Verbindungen zulässt.",
}
DASH={
 "Clamp extrapolation for SteamVR tracked devices": "Extrapolation für SteamVR-getrackte Geräte begrenzen",
 "SteamVR max pose extrapolation": "SteamVR maximale Posen-Extrapolation",
 "%1ms": "%1ms",
 "Maximum time in milliseconds that poses may be extrapolated ahead for SteamVR tracked devices. Tune this value if you experience jittery or wobbly tracking.": "Maximale Zeit in Millisekunden, um die Posen für SteamVR-getrackte Geräte extrapoliert werden. Passen Sie diesen Wert an, wenn das Tracking zitterig oder wackelig wirkt.",
 "SteamVR joystick deadzone": "SteamVR Joystick-Totzone",
 "Deadzone to apply to joysticks on lighthouse-tracked controllers, such as Index.\nFor standalone controllers, deadzones may be adjusted via the headset's system settings.": "Totzone für die Joysticks von Lighthouse-getrackten Controllern wie dem Index.\nBei Standalone-Controllern kann die Totzone über die Systemeinstellungen des Headsets angepasst werden.",
}
files=[('locale/de/wivrn.po',CLIENT),('locale/de/wivrn-dashboard.po',DASH)]
for path,trans in files:
    fsha,raw=get(path,BR)
    po=polib.pofile(raw)
    existing={e.msgid for e in po}
    added=0
    for mid,msgstr in trans.items():
        if mid in existing:
            e=po.find(mid)
            if e and not e.obsolete and (not e.msgstr or e.translated() is False or 'fuzzy' in e.flags):
                e.msgstr=msgstr
                if 'fuzzy' in e.flags: e.flags.remove('fuzzy')
                added+=1
        else:
            e=polib.POEntry(msgid=mid,msgstr=msgstr)
            po.append(e); added+=1
    newraw=bytes(str(po),'utf-8') if False else po.__unicode__(width=0) if False else str(po)
    # polib default wrapping keeps standard po style
    content=base64.b64encode(str(po).encode()).decode()
    payload={'message':'add missing de translations for new settings strings','content':content,'branch':BR,'sha':fsha}
    f=tempfile.NamedTemporaryFile('w',delete=False,suffix='.json');json.dump(payload,f);f.close()
    r=subprocess.run(['gh','api',f'repos/{REPO}/contents/{path}','-X','PUT','--input',f.name],capture_output=True,text=True)
    os.unlink(f.name)
    if r.returncode!=0:
        print('FAIL',path,r.stderr[:300]); sys.exit(1)
    out=json.loads(r.stdout)
    print('COMMITTED',path,'added',added,'->',out['commit']['sha'][:12])
