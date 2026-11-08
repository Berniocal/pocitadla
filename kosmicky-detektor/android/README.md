# Kosmický detektor — nativní Android aplikace

Samostatná Android verze (Java / Camera2), nejde o WebView/PWA obal.

- Používá Camera2 + ImageReader YUV snímky.
- Požádá o vypnutí redukce šumu a korekce horkých pixelů, pokud to kamera umožňuje.
- Vypne automatickou expozici, pokud hardware dovolí manuální ovládání.
- Kalibruje tmavý obraz a hledá izolované přechodné jasné shluky.
- Běží jako služba v popředí s upozorněním; může pokračovat po zhasnutí obrazovky.
- Do interní databáze ukládá čas, polohu, velikost a sílu kandidátního zásahu i lokální ořez obrázku.
- Exportuje CSV přes systémové Uložit jako.

## Sestavení APK

Na GitHubu: Actions > Kosmicky detektor APK > poslední úspěšný běh > Artifacts > kosmicky-detektor-apk.

Lokálně: otevři složku `android` v Android Studiu nebo spusť `gradle assembleDebug` s Android SDK 35 a JDK 17. Instalace výsledku `app/build/outputs/apk/debug/app-debug.apk`.

## Interpretace a omezení

Detekce je experimentální a nemůže sama potvrdit, že anomálie pochází z kosmického záření. Android Camera2 nemusí poskytovat neovlivněná data snímače: YUV obraz stále prochází ISP. Chybějící podpora ruční expozice nebo vypnutí šumu bude řešena návratem k automatickému režimu.

Spouštěj měření z otevřené aplikace. Android 14+ nedovoluje zakládat kamerovou službu libovolně z pozadí. Po uzamčení obrazovky může výrobce kamerovou relaci i přes službu ukončit; dlouhé měření je nutné ověřit na konkrétním telefonu. Při dlouhodobém měření sleduj zahřívání a spotřebu.
