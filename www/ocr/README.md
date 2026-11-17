# Texterkennung offline (Speisekarten-Scanner)

Unveränderte Dateien aus npm, damit die Texterkennung ohne Internet läuft:

- `tesseract.min.js`, `worker.min.js` aus tesseract.js 5.1.1 (Apache-2.0, siehe LICENSE-tesseract.js.md)
- `tesseract-core-simd-lstm.wasm.js` aus tesseract.js-core 5.1.1
- `eng.traineddata.gz`, `tha.traineddata.gz` aus @tesseract.js-data/eng und /tha 1.0.0 (Ordner 4.0.0_best_int)

In der Android-App liest ML Kit lateinische Schrift, Tesseract wird dort nur für Thai gebraucht. iPhone und Webseite nutzen Tesseract für alles.
