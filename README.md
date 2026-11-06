# Tellerflamme

Kostenloser Ernährungs-Tracker mit Streaks, Vitaminen und Mineralstoffen, Rezepten, Zielrechner und Datenexport.

- **Webseite:** wird bei jedem Push nach `main` über GitHub Pages veröffentlicht (`www/`).
- **Android-App:** wird bei jedem Push automatisch gebaut. Die neueste APK liegt unter *Releases → Tellerflamme (neueste Version)*. Die App liest über Health Connect Aktivkalorien und Gewicht (z. B. von Samsung Health).

## Datenquellen
- Eigene Lebensmittel-Datenbank (Richtwerte nach USDA/BLS)
- Open Food Facts (Barcodes, Markenprodukte)
- USDA FoodData Central (vollständige Mikronährstoffe)

## Aufbau
- `www/index.html`: die komplette App in einer Datei
- `scripts/patch-android.mjs`: ergänzt Health-Connect-Berechtigungen im erzeugten Android-Projekt
- `.github/workflows/`: Pages-Deployment und APK-Build
