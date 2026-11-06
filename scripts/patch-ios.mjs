// Ergänzt das von Capacitor erzeugte iOS-Projekt um die nötigen Berechtigungstexte.
import fs from 'node:fs';
const pl = 'ios/App/App/Info.plist';
let x = fs.readFileSync(pl, 'utf8');
const add = {
  NSCameraUsageDescription: 'Tellerflamme nutzt die Kamera, um Barcodes und Verpackungen zu lesen.',
  NSPhotoLibraryUsageDescription: 'Tellerflamme liest Fotos von Verpackungen, um Nährwerte zu erkennen.',
  NSHealthShareUsageDescription: 'Tellerflamme liest Schritte, Aktivkalorien und Gewicht, um dein Kalorienziel anzupassen.',
  NSHealthUpdateUsageDescription: 'Tellerflamme schreibt keine Gesundheitsdaten.'
};
let extra = '';
for (const [k, v] of Object.entries(add)) if (!x.includes(`<key>${k}</key>`)) extra += `\t<key>${k}</key>\n\t<string>${v}</string>\n`;
if (extra) { const i = x.lastIndexOf('</dict>'); x = x.slice(0, i) + extra + x.slice(i); fs.writeFileSync(pl, x); }
console.log('iOS-Projekt angepasst');
