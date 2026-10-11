# 1. Źródło danych planów: publiczne arkusze XLSX zamiast scrapingu HTML/PDF

Date: 2026-10-11

## Status
Zaakceptowany (Accepted)

## Kontekst
Projekt bazowy (`plan_umg` / Plan WN) opierał się na scrapowaniu uczelnianego systemu Arktur (HTML) oraz parsowaniu wektorowych tabel PDF dla studiów niestacjonarnych.
Szkoła Główna Gospodarstwa Wiejskiego (SGGW), począwszy od Wydziału Medycyny Weterynaryjnej (WMW), publikuje oficjalne plany zajęć w postaci arkuszy Microsoft Excel (`.xlsx`) na publicznie dostępnych linkach SharePoint / OneDrive.

## Decyzja
1. Zastępujemy cały scraping HTML Arktura oraz dedykowany parser PDF silnikiem opartym na pobieraniu arkuszy `.xlsx` z linków SharePoint (`sggw_client.py`) i ich bezpośrednim przetwarzaniu (`sggw_parser.py`) za pomocą biblioteki `openpyxl`.
2. Zachowujemy w 100% niezmieniony kontrakt danych wyjściowych dla PWA:
   - `dist/data/schedules/{plan_id}_{group}.json`
   - `dist/calendars/{plan_id}_{group}.ics`
   - `dist/data/plans.json` oraz `dist/data/cross_reference.json`
3. Wszystkie reguły dotyczące sal, grup (np. `gr. 1`–`7`), form (`ćw.`, `wykład`, `fakultet`) oraz zakresów tygodni ("1-5 tydzień zajęć", "od 6 tygodnia zajęć") są normalizowane w warstwie Pythona przed zrzuceniem do statycznego JSON.

## Konsekwencje
- Eliminujemy niestabilne parsowanie znaczników HTML i specyficznych kolorów fontów Arktura.
- Budowanie planów staje się deterministyczne i niezależne od sesji uczelnianych portali studenta.
- Moduł `build_static.py` zostaje odchudzony i przepięty na `sggw_client` / `sggw_parser`.
