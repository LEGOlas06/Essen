// Ergänzt das von Capacitor erzeugte iOS-Projekt um die nötigen Berechtigungstexte.
import fs from 'node:fs';
const pl = 'ios/App/App/Info.plist';
let x = fs.readFileSync(pl, 'utf8');
const add = {
  NSCameraUsageDescription: 'Tellerflamme nutzt die Kamera, um Barcodes und Verpackungen zu lesen.',
  NSPhotoLibraryUsageDescription: 'Tellerflamme liest Fotos von Verpackungen, um Nährwerte zu erkennen.',
  NSHealthShareUsageDescription: 'Tellerflamme liest Schritte, Aktivkalorien und Gewicht, um dein Kalorienziel anzupassen.',
  NSHealthUpdateUsageDescription: 'Tellerflamme schreibt keine Gesundheitsdaten.',
  NSLocalNetworkUsageDescription: 'Tellerflamme gleicht Vorrat und Tagebuch mit deinem Home Assistant im Heimnetz ab.'
};
let extra = '';
for (const [k, v] of Object.entries(add)) if (!x.includes(`<key>${k}</key>`)) extra += `\t<key>${k}</key>\n\t<string>${v}</string>\n`;
// Home Assistant im Heimnetz über http erlauben (gilt nur für lokale Adressen wie homeassistant.local)
if (!x.includes('<key>NSAppTransportSecurity</key>')) extra += `\t<key>NSAppTransportSecurity</key>\n\t<dict>\n\t\t<key>NSAllowsLocalNetworking</key>\n\t\t<true/>\n\t</dict>\n`;
if (extra) { const i = x.lastIndexOf('</dict>'); x = x.slice(0, i) + extra + x.slice(i); fs.writeFileSync(pl, x); }
// HealthKit-Berechtigung (für Schritte, Aktivkalorien und Gewicht)
const ent = 'ios/App/App/App.entitlements';
if (!fs.existsSync(ent)) fs.writeFileSync(ent, `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>com.apple.developer.healthkit</key>
\t<true/>
\t<key>com.apple.developer.healthkit.access</key>
\t<array/>
</dict>
</plist>
`);
const pbx = 'ios/App/App.xcodeproj/project.pbxproj';
let p = fs.readFileSync(pbx, 'utf8');
if (!p.includes('CODE_SIGN_ENTITLEMENTS')) { p = p.replace(/(\t+)CODE_SIGN_STYLE = Automatic;/g, '$1CODE_SIGN_STYLE = Automatic;\n$1CODE_SIGN_ENTITLEMENTS = App/App.entitlements;'); fs.writeFileSync(pbx, p); }
console.log('iOS-Projekt angepasst');
