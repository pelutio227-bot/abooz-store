#!/usr/bin/env python3
"""Gruppe «Intern» (alle Builds) + Tester pelutio@icloud.com + «Was testen» (de-DE) für den neusten/angegebenen Build.
Nutzung: testflight-intern.py [BUILD_NR]"""
import os, sys, time
sys.path.insert(0, os.path.expanduser("~/Projects/company-pelutio/scripts"))
from asc import call
APP, EMAIL = "6825720576", "pelutio@icloud.com"
WHAT = ("Abooz als App: Startseite, Login (Google über den System-Browser, Sign in with Apple), "
        "Rechnung oder Vertrag mit dem Dokumenten-Scanner einlesen, KI-Analyse und Angebote vergleichen. "
        "Hinweis: Login und Analyse brauchen das Backend; ist es pausiert, zeigt die App Fehler beim Anmelden.")
want = sys.argv[1] if len(sys.argv) > 1 else None

st, g = call("GET", f"/v1/apps/{APP}/betaGroups")
grp = next((x for x in g.get("data", []) if x["attributes"]["name"] == "Intern"), None)
if not grp:
    st, r = call("POST", "/v1/betaGroups", {"data": {"type": "betaGroups", "attributes": {"name": "Intern", "isInternalGroup": True, "hasAccessToAllBuilds": True},
                 "relationships": {"app": {"data": {"type": "apps", "id": APP}}}}})
    if st != 201: sys.exit(f"Gruppe fehlgeschlagen: {st} {r}")
    grp = r["data"]; print("Gruppe Intern angelegt:", grp["id"])
gid = grp["id"]
st, t = call("GET", f"/v1/betaGroups/{gid}/betaTesters")
if not any(x["attributes"].get("email") == EMAIL for x in t.get("data", [])):
    st, r = call("POST", "/v1/betaTesters", {"data": {"type": "betaTesters", "attributes": {"email": EMAIL, "firstName": "Claw", "lastName": "P"},
                 "relationships": {"betaGroups": {"data": [{"type": "betaGroups", "id": gid}]}}}})
    print("Tester:", st, r.get("errors", [{}])[0].get("detail") if st >= 300 else "hinzugefügt")
else:
    print("Tester schon in Intern")

for i in range(40):
    q = f"/v1/builds?filter[app]={APP}&sort=-uploadedDate&limit=5&fields[builds]=version,processingState,uploadedDate"
    if want: q += f"&filter[version]={want}"
    st, b = call("GET", q)
    builds = b.get("data", [])
    if builds and builds[0]["attributes"]["processingState"] == "VALID": break
    print("warte auf Build …", [(x["attributes"]["version"], x["attributes"]["processingState"]) for x in builds]); time.sleep(60)
else:
    sys.exit("Build nicht VALID nach 40 Min.")
bld = builds[0]; bid = bld["id"]; print("Build:", bld["attributes"]["version"], "VALID")
st, loc = call("GET", f"/v1/builds/{bid}/betaBuildLocalizations")
de = next((x for x in loc.get("data", []) if x["attributes"]["locale"] == "de-DE"), None)
if de: st, _ = call("PATCH", f"/v1/betaBuildLocalizations/{de['id']}", {"data": {"type": "betaBuildLocalizations", "id": de["id"], "attributes": {"whatsNew": WHAT}}})
else: st, _ = call("POST", "/v1/betaBuildLocalizations", {"data": {"type": "betaBuildLocalizations", "attributes": {"locale": "de-DE", "whatsNew": WHAT}, "relationships": {"build": {"data": {"type": "builds", "id": bid}}}}})
print("Was testen:", st)
st, d = call("GET", f"/v1/builds/{bid}/buildBetaDetail")
print("Beta-Status intern:", d.get("data", {}).get("attributes", {}).get("internalBuildState"))
