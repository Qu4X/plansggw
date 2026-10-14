# Plan WMW — Backlog / TODO

Rejestr zadań, pomysłów i planowanych usprawnień dla aplikacji **Plan WMW** (Wydział Medycyny Weterynaryjnej SGGW w Warszawie).

---

## 📌 Do zrobienia w kolejnych krokach (Backlog)

### 1. Rozszerzenie bazy planów i semestrów (`build_static.py`, `sggw_client.py`)
- [ ] **Dodanie kolejnych semestrów WMW (lata I–VI)**: W miarę udostępniania arkuszy `.xlsx` przez dziekanat WMW SGGW, dołączenie semestrów 1–6 oraz 8–11 do konfiguracji `DEFAULT_WMW_PLANS`.
- [ ] **Automatyczne pobieranie arkuszy z SharePoint / strony WMW (`sggw_client.py`)**: Wdrożenie weryfikacji sum kontrolnych i automatycznego pobierania najnowszych arkuszy ze stron wydziałowych SGGW.

### 2. Rozwój interfejsu użytkownika (`web/`)
- [ ] **Widok porównawczy dla grup**: Opcja podglądu zajęć wielu grup jednocześnie w jednym widoku (ułatwienie przy zamianach i konsultacjach między grupami).
- [ ] **Przywrócenie wyszukiwarki sal i wykładowców**: Gdy dziekanat udostępni kompletne dane personalne prowadzących i kody audytoriów, odblokowanie wyszukiwarki cross-reference w UI.
- [ ] **Widok listy (agenda)**: Opcjonalny widok chronologiczny w formie prostej listy obok widoku kafelkowego.

### 3. Parser siatki Excel (`sggw_parser.py`)
- [ ] **Obsługa niestandardowych bloków klinicznych**: Rozpoznawanie blokowych ćwiczeń klinicznych realizowanych w klinikach weterynaryjnych (Klinika Koni, Klinika Małych Zwierząt, Wolica).
- [ ] **Słownik wyjątków i aliasów sal (`data/rooms_manual.json`)**: Manualna standaryzacja skrótów sal (np. mapowanie `Wolica 106`, `aula 3`, `Nowy Rektorat` na ujednolicone oznaczenia).

---

## ✅ Zrealizowane funkcjonalności (v1.0.0)

### Branding i tożsamość aplikacji
- [x] **Pełny rebranding na Plan WMW**: Nowa nazwa, estetyczna szata graficzna w oficjalnych barwach SGGW (`#12322a`), nowe meta-tagi i manifest PWA.
- [x] **Dedykowany zestaw ikon PWA**: Wygenerowano ikony maskowalne (safe zone), Apple Touch Icon oraz ikony standardowe z maskotką pandy i kalendarzem z zachowaniem tła `#003b2f`.
- [x] **Rzeczywiste zrzuty ekranu PWA**: Wygenerowano zrzuty ekranu desktop (1280×720) i mobile (720×1280) z realnego planu Weterynarii.
- [x] **Formularz zgłaszania uwag Tally**: Zintegrowano dedykowany formularz kontaktowy online (`https://tally.so/r/VLRkgl`).

### Architektura danych i parser SGGW
- [x] **Parser siatek Excel (`sggw_parser.py`)**: Bezpośrednie przetwarzanie arkuszy `.xlsx` z siatką godzinową, scalonymi komórkami i podziałami na grupy.
- [x] **Detekcja form zajęć i lokalizacji**: Rozpoznawanie wykładów, ćwiczeń, audytoriów i sal z opisów komórek.
- [x] **Obsługa podziałów semestralnych i cykli**: Wykrywanie zajęć 1. i 2. połowy semestru oraz cyklu tygodniowego (co 2 tyg. / A / B).
- [x] **Usunięcie pozostałości starej uczelni**: Oczyszczono repozytorium z nieużywanych katalogów, plików konfiguracyjnych i odniesień do UMG.

### Kalendarz akademicki i eksport ICS
- [x] **Synchronizacja z zarządzeniem Rektora SGGW (`academic_calendar.json`)**: Dni wolne, święta państwowe, dni rektorskie i zamiany planów dni.
- [x] **Eksport do formatu iCalendar (`ics_export.py`)**: Generowanie plików `.ics` z UID w domenie `@sggw.edu.pl` i bezpośrednią subskrypcją Google / Apple / Outlook.

### Silnik frontendowy PWA (`web/`)
- [x] **Schedule Engine (`web/js/schedule-engine.js`)**: Logika numeracji spotkań dydaktycznych (np. 2 z 15) z uwzględnieniem dni wolnych i przerw.
- [x] **Dostosowanie UI do dostępnych danych**: Ukrycie z menu wyszukiwarki sal i prowadzących do czasu publikacji pełnych danych przez wydział.
- [x] **Service Worker i tryb offline**: Buforowanie zasobów w strategii Network-First z fallbackiem offline.
