# Plan WMW

[![CI](https://github.com/Qu4X/planwn/actions/workflows/deploy.yml/badge.svg?branch=main)](https://github.com/Qu4X/planwn/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)

Nowoczesny, szybki i responsywny plan zajęć dla studentów **Wydziału Medycyny Weterynaryjnej Szkoły Głównej Gospodarstwa Wiejskiego w Warszawie (SGGW)**. Aplikacja pobiera i przetwarza oficjalne plany zajęć publikowane w arkuszach Excel (.xlsx), udostępniając je w intuicyjnej aplikacji PWA z pełnym wsparciem trybu offline oraz automatycznym eksportem do kalendarzy osobistych (.ics).

---

## Funkcje

- **Plany studiów stacjonarnych i niestacjonarnych**: Pełne wsparcie dla wszystkich lat i grup kierunku Weterynaria.
- **Inteligentne rozpoznawanie sal i lokalizacji**: Obsługa auli, sal dydaktycznych i klinik weterynaryjnych (Nowy Rektorat, Wolica, Klinika Koni, Katedry).
- **Podział na połowy semestru i cykle**: Automatyczne wykrywanie zajęć w 1. i 2. połowie semestru oraz cykli tygodniowych (A / B).
- **Synchronizacja z kalendarzem akademickim SGGW**: Dni rektorskie, święta państwowe, zamiany planów dni oraz przerwy semestralne.
- **Eksport do kalendarza (.ics / webcal)**: Możliwość subskrypcji planu w Google Calendar, Apple Calendar oraz Microsoft Outlook.
- **Wyszukiwarka sal, wykładowców i przedmiotów**: Sprawdzanie wolnych sal oraz harmonogramu prowadzących.
- **PWA (Progressive Web App)**: Możliwość instalacji na telefonie i komputerze, natychmiastowe ładowanie offline i dedykowany ciemny/jasny motyw SGGW (`#12322a`).

---

## Architektura projektu

```
build_static.py            Główny punkt wejścia buildu — generuje pliki JSON i ICS do dist/
sggw_client.py             Pobieranie arkuszy planów (.xlsx) ze stron/SharePoint SGGW
sggw_parser.py             Parser siatki Excel (.xlsx) za pomocą openpyxl
ics_export.py              Generator RFC 5545 iCalendar (.ics) z uwzględnieniem kalendarza SGGW
models.py                  Modele domenowe TypedDict

data/                      Dane referencyjne i konfiguracja
├── academic_calendar.json Kalendarz akademicki SGGW (zamiany dni, święta, przerwy)
├── subjects_manual.json   Aliasy i klasyfikacja form przedmiotów
└── events.json            Wydarzenia akademickie i studenckie

web/                       Frontend PWA (Vanilla JS, CSS w barwach SGGW, bez bundlerów)
├── index.html             Główny interfejs aplikacji
├── style.css              Style aplikacji (kolor wiodący #12322a)
├── app.js                 Główny kontroler aplikacji
├── plansggw.svg           Logo aplikacji WMW SGGW
├── js/
│   ├── schedule-engine.js Silnik domenowy harmonogramu i numeracji spotkań
│   ├── cross-reference.js Modale wyszukiwania sal, wykładowców i przedmiotów
│   └── events-service.js  Obsługa wydarzeń studenckich
└── sw.js                  Service Worker (cache offline Network-First)

tests/                     Zestawy testów regresyjnych
├── test_backend.py        Testy backendu w Pythonie
├── test_sggw_parser.py    Testy parsera arkuszy Excel SGGW
├── test_calendar.js       Testy UI i spotkań w JS
├── test_schedule_engine.js Testy silnika harmonogramu w JS
├── test_cross_reference.js Testy wyszukiwarki cross-reference w JS
└── test_events.js         Testy serwisu wydarzeń w JS
```

---

## Wymagania

- Python 3.11 lub nowszy
- Node.js 18 lub nowszy (do uruchamiania testów frontendu)

Instalacja zależności:

```bash
pip install -r requirements.txt
```

---

## Uruchomienie lokalne

1. Utwórz i aktywuj wirtualne środowisko:

   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate
   ```

2. Zainstaluj wymagane pakiety:

   ```bash
   pip install -r requirements.txt
   ```

3. Zbuduj serwis statyczny:

   ```bash
   python build_static.py
   ```

4. Uruchom lokalny serwer HTTP:

   ```bash
   python -m http.server 8000 --directory dist
   ```

5. Otwórz w przeglądarce adres `http://localhost:8000`.

---

## Testy

Przed commitem należy upewnić się, że wszystkie testy przechodzą:

```bash
# Testy backendu Python
.venv\Scripts\python.exe tests/test_backend.py
.venv\Scripts\python.exe tests/test_sggw_parser.py

# Testy frontendu JS
npm test
```

---

## Nota prawna

Aplikacja ma charakter projektu studenckiego typu open source i nie jest oficjalnym systemem Szkoły Głównej Gospodarstwa Wiejskiego w Warszawie. Dane pochodzą z publicznie udostępnianych planów zajęć WMW SGGW.

---

## Licencja

Projekt udostępniany jest na warunkach licencji [MIT](LICENSE).
