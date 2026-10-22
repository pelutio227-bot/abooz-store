# Abooz iOS (Store-Wrapper)

Capacitor-8-Wrapper für https://abooz.ch (Bundle-ID `com.pelutio.abooz`, ASC-App-ID 6825720576).
Die App lädt die Live-Seite; `www/` ist nur die Offline-Fallback-Seite.

## Native Schnittstelle (für den Web-Code via `window.Capacitor.Plugins`)
- `AboozNative.scanDocument()` → `{ images: string[] }` (JPEG base64, VisionKit-Scanner), Abbruch = reject «cancelled»
- `AboozNative.signInWithApple({ nonce? })` → `{ identityToken, authorizationCode, email, givenName, familyName, user }`
- `AboozNative.isAvailable()` → `{ scanner, appleSignIn }`
- Offizielle Plugins: App (appUrlOpen, Scheme `abooz://`), Browser, Haptics, StatusBar, Share, Keyboard
- User-Agent enthält `AboozApp/1.0`

## Build → TestFlight
Ohne Xcode lokal: GitHub Actions (`.github/workflows/ios-testflight.yml`, macOS-Runner).
Commit mit «[testflight]» auf `main` pushen → signierter Build wird hochgeladen. Sonst nur Compile-Check.
ASC/Signierung: `scripts/asc-setup.py` (Bundle-ID, Sign in with Apple, Profil «Abooz App Store»; `--secrets` setzt das Profil-Secret).
Apple-Zentrale: ~/Projects/company-pelutio (Karte `apps/abooz.md`).
