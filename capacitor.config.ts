import type { CapacitorConfig } from "@capacitor/cli";

// Store-Wrapper für abooz.ch: lädt die Live-Seite, www/ ist nur die Offline-Fallback-Seite.
const config: CapacitorConfig = {
  appId: "com.pelutio.abooz",
  appName: "Abooz",
  webDir: "www",
  server: {
    url: "https://abooz.ch",
    allowNavigation: ["abooz.ch", "www.abooz.ch"],
    errorPath: "offline.html",
  },
  ios: {
    contentInset: "never",
    backgroundColor: "#F4F4F6",
    appendUserAgent: "AboozApp/1.0",
    limitsNavigationsToAppBoundDomains: false,
  },
  plugins: {
    Keyboard: { resize: "native" },
    StatusBar: { overlaysWebView: true },
  },
};

export default config;
