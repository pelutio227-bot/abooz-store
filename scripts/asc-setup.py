#!/usr/bin/env python3
"""Bundle-ID com.pelutio.abooz + Sign in with Apple + App-Store-Profil «Abooz App Store» (Dist-Zertifikat W8MMUGRNV5).
Nutzt den ASC-Mini-Client aus ~/Projects/company-pelutio/scripts/asc.py."""
import base64, os, sys, subprocess
sys.path.insert(0, os.path.expanduser("~/Projects/company-pelutio/scripts"))
from asc import call
BUNDLE, NAME, PROFILE, CERT = "com.pelutio.abooz", "Abooz", "Abooz App Store", "W8MMUGRNV5"
APPLE = os.path.expanduser("~/Projects/_memory/apple")

st, b = call("GET", f"/v1/bundleIds?filter[identifier]={BUNDLE}")
data = [d for d in b.get("data", []) if d["attributes"]["identifier"] == BUNDLE]
if not data:
    st, b = call("POST", "/v1/bundleIds", {"data": {"type": "bundleIds", "attributes": {"identifier": BUNDLE, "name": NAME, "platform": "IOS"}}})
    if st != 201: sys.exit(f"Bundle-ID fehlgeschlagen: {st} {b}")
    data = [b["data"]]; print("Bundle-ID angelegt")
bid = data[0]["id"]; print("Bundle-ID-Record:", bid)
st, caps = call("GET", f"/v1/bundleIds/{bid}/bundleIdCapabilities")
have = {c["attributes"]["capabilityType"] for c in caps.get("data", [])}
if "APPLE_ID_AUTH" not in have:
    st, c = call("POST", "/v1/bundleIdCapabilities", {"data": {"type": "bundleIdCapabilities", "attributes": {"capabilityType": "APPLE_ID_AUTH", "settings": [{"key": "APPLE_ID_AUTH_APP_CONSENT", "options": [{"key": "PRIMARY_APP_CONSENT"}]}]},
                  "relationships": {"bundleId": {"data": {"type": "bundleIds", "id": bid}}}}})
    print("Sign in with Apple:", st)
else:
    print("Sign in with Apple: vorhanden")
st, profs = call("GET", "/v1/profiles?filter[name]=Abooz%20App%20Store")
for p_ in profs.get("data", []):
    call("DELETE", f"/v1/profiles/{p_['id']}"); print("altes Profil gelöscht:", p_["id"])
st, p = call("POST", "/v1/profiles", {"data": {"type": "profiles", "attributes": {"name": PROFILE, "profileType": "IOS_APP_STORE"},
             "relationships": {"bundleId": {"data": {"type": "bundleIds", "id": bid}}, "certificates": {"data": [{"type": "certificates", "id": CERT}]}}}})
if st != 201: sys.exit(f"Profil fehlgeschlagen: {st} {p}")
path = os.path.join(APPLE, "Abooz_App_Store.mobileprovision")
open(path, "wb").write(base64.b64decode(p["data"]["attributes"]["profileContent"]))
print("Profil:", p["data"]["id"], p["data"]["attributes"]["uuid"], "bis", p["data"]["attributes"]["expirationDate"], "→", path)
if "--secrets" in sys.argv:
    R = "pelutio227-bot/abooz-store"
    subprocess.run(["gh", "secret", "set", "IOS_APPSTORE_PROFILE", "-R", R], input=base64.b64encode(open(path, "rb").read()), check=True)
    print("Secret IOS_APPSTORE_PROFILE gesetzt")
