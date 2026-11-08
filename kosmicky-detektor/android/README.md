# Kosmický detektor Android 1.1 — experimentální RAW měření

Nativní Camera2 aplikace, bez WebView/PWA. Přidána podpora skutečného **RAW_SENSOR** (16bitová Bayerova mozaika) u kamer, které ji přes Camera2 zpřístupňují.

## Režimy a snímání
- **RAW_SENSOR** (výchozí, při nepodpoře automaticky YUV): senzorové hodnoty bez demosaicingu. Analýza středového výřezu až 2048 × 1536 senzorových pixelů, tedy nikoli celé plochy snímače.
- **YUV**: rychlejší režim se zpracovaným obrazem, vhodný pro porovnání.
- **Expoziční časy**: volby 50, 100, 300 ms, 1, 2, 5, 10, 30 s, vždy omezené rozsahem `SENSOR_INFO_EXPOSURE_TIME_RANGE` daného telefonu. ISO 100–3200 rovněž omezené hardwarem.
- Vypnutí korekce vadných pixelů a odšumování, jen pokud takovou možnost Camera2 hlásí. Ruční nastavení není na všech kamerách podporované.
- Snímání po jednotlivých expozicích, párování RAW snímku a skutečných metadat Camera2.
- Kalibrace RAW 18 snímky, YUV 50 snímky. Software odlišuje trvalé a opakující se pixely od nových kandidátních shluků; nadměrně světlé snímky odmítá.

## Data a export
- Metadata události: čas, x/y v **souřadnicích celého snímače**, počet pixelů, vrchol změny, režim, skutečná expozice a ISO.
- Ukládají se diferenciální PNG výřezy (RAW režim) nebo výřezy YUV.
- Přepínač „Uložit DNG“ vytvoří při zásahu celý RAW soubor DNG (max. 50 pro jeden běh). Může být velmi velký.
- CSV export i ZIP archiv obsahující CSV, PNG výřezy a uložené DNG. Archiv se vytváří ve vedlejším vlákně.
- Databáze starších událostí se migrací zachovává.

Android 1.1 má záměrně jiný identifikátor balíčku (`cz.bernio.kosmickydetektor.raw`) než stará verze. Lze ho tedy nainstalovat vedle 1.0; její uložené události zůstávají v původní aplikaci.\n\n## Sestavení APK
GitHub Actions → „Kosmicky detektor APK“ → nejnovější úspěšný běh → Artifacts.
Lokálně je potřeba Android SDK 35, Gradle 8.10.2 a JDK 17.

## Důležitá omezení
Ani nekomprimovaný RAW nezaručuje naprosto nezpracovanou informaci: před zobrazením může čip nebo firmware dělat vlastní korekce. Rozsah ruční expozice vyplývá z Camera2 metadat (telefon může žádost omezit). Není vědecky potvrzeno, že každý kandidát pochází z kosmického záření. RAW frame může zabírat velkou paměť, delší expozice prodlužuje kalibraci a zahřívá zařízení. Měření při zamknuté obrazovce závisí na systému. Bez validace na skutečném telefonu nelze prohlásit detekci za kalibrovanou.

Vývojová inspirace: [CREDO](https://github.com/credo-science/credo-detector-android).
