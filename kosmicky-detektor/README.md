# Kosmický detektor (PWA)

Česká experimentální aplikace pro mobilní fotoaparát nebo webkameru.

- Zakryj objektiv neprůsvitně, povol přístup ke kameře a spusť kalibraci/měření.
- Aplikace lokálně vyhledává jasné krátkodobé anomálie a maskuje opakující se horké pixely.
- Data zůstávají v prohlížeči (IndexedDB), lze je exportovat do CSV/JSON.
- Stránka vyžaduje HTTPS (na GitHub Pages zajištěno), běží i offline po úspěšném prvním načtení.
- Na mobilu musí při dlouhém měření zůstat prohlížeč v popředí a displej aktivní.
- Nejde o kalibrovaný dozimetr: detekované události **nejsou prokázané kosmické částice**.

Inspirace (nezávislá implementace, nikoli oficiální aplikace CREDO):
https://github.com/credo-science/credo-detector-android
https://github.com/credo-science/credo-web-detector
