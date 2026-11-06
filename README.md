# Tellerflamme

Kostenloser Ernährungs-Tracker mit Streaks, Vitaminen und Mineralstoffen, Rezepten, Zielrechner und Datenexport.

- **Webseite:** wird bei jedem Push nach `main` über GitHub Pages veröffentlicht (`www/`).
- **Home Assistant:** Vorrat, Einkaufsliste, Rezeptvorschläge nach Vitaminlücken und Abgleich zwischen Handy und Tablet. Anleitung: [homeassistant/README.md](homeassistant/README.md).
- **Android-App:** wird bei jedem Push automatisch gebaut. Die neueste APK liegt unter *Releases → Tellerflamme (neueste Version)*. Die App liest über Health Connect Aktivkalorien und Gewicht (z. B. von Samsung Health).

## Datenquellen
- Eigene Lebensmittel-Datenbank (Richtwerte nach USDA/BLS)
- Open Food Facts (Barcodes, Markenprodukte)
- USDA FoodData Central (vollständige Mikronährstoffe)
- Schweizer Nährwertdatenbank V 7.1, © Bundesamt für Lebensmittelsicherheit und Veterinärwesen (BLV), naehrwertdaten.ch
- Bundeslebensmittelschlüssel BLS 4.0: Max Rubner-Institut (2025): Bundeslebensmittelschlüssel (BLS), Version 4.0 – Deutsche Nährstoffdatenbank. Karlsruhe. DOI: 10.25826/Data20251217-134202-0, Lizenz CC BY 4.0

## Aufbau
- `www/index.html`: die komplette App in einer Datei
- `scripts/patch-android.mjs`: ergänzt Health-Connect-Berechtigungen im erzeugten Android-Projekt
- `.github/workflows/`: Pages-Deployment und APK-Build
- `custom_components/tellerflamme/`: Home-Assistant-Erweiterung (über HACS installierbar)
