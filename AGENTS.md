# AGENTS.md — Plan SGGW

Dokument dla agentów AI pracujących w tym repozytorium.
Przeczytaj przed pierwszą zmianą w kodzie.

---

## Architektura (skrót)

```
sggw_client.py            Pobieranie arkuszy planów (.xlsx) ze stron/SharePoint SGGW
sggw_parser.py            Parser siatki Excel (.xlsx) za pomocą openpyxl
build_static.py           Punkt wejścia buildu — generuje pliki JSON i ICS do dist/
data/academic_calendar.json Jedyne źródło prawdy o dniach wolnych, zamianach i przerwach
data/subjects_manual.json Aliasy i konfiguracja klasyfikacji form przedmiotów
web/app.js                Główny kontroler frontendu PWA (vanilla JS)
web/js/schedule-engine.js Czysty silnik domenowy kalendarza i spotkań
web/js/cross-reference.js Silnik i UI wyszukiwarki sal, wykładowców i przedmiotów
tests/test_backend.py     Regresja Pythona (backend, modele, ICS)
tests/test_sggw_parser.py Regresja parsera Excel SGGW
tests/test_calendar.js    TDD logiki spotkań i UI w JS
tests/test_cross_reference.js TDD modali sal, wykładowców i przedmiotów w JS
tests/test_schedule_engine.js TDD czystego silnika harmonogramu w JS
```

Pełna architektura i słownik → [`CONTEXT.md`](CONTEXT.md)

---

## Testy — uruchom przed i po każdej zmianie

```powershell
.venv\Scripts\python.exe tests/test_backend.py   # Regresja backendu Python
npm test                                        # JS frontend (wszystkie zestawy testów)
```

Oba muszą przejść. Jeśli jeden czerwony — napraw przed commitem.

---

## Wymagania testowe

**Bug fix bez testu regresyjnego = niekompletna zmiana.**

Dodaj test do `tests/test_backend.py` / `tests/test_sggw_parser.py` (Python) lub odpowiedniego pliku w `tests/` (JS) który:
1. Przed fixem jest czerwony.
2. Po fixie jest zielony.

Nowe funkcje: test opcjonalny, ale mile widziany.

---

## Format commitów — Conventional Commits

```
feat(scope):   nowa funkcjonalność
fix(scope):    naprawa błędu
perf(scope):   optymalizacja bez zmiany działania
docs(scope):   tylko dokumentacja
refactor(scope): zmiana struktury bez zmiany działania
test(scope):   testy bez zmian produkcyjnych
ci(scope):     pipeline i deployment
```

Scope = moduł lub obszar (np. `calendar`, `pwa`, `parser`, `ics`, `web`, `sggw`).

---

## Krytyczne kontrakty Python ↔ JS

### Kontrakt 1 — sanityzacja nazwy grupy (nazwy plików)

Python (`build_static.py`) tworzy nazwy plików:
```python
safe_grupa = re.sub(r'[^\w-]', '_', grupa)
# Przykład: "gr. 1" → "gr__1"
```

JS (`app.js`) musi budować URL fetcha tą samą regułą:
```js
const safeGroup = group.replace(/[^\w-]/g, '_');
# Przykład: "gr. 1" → "gr__1"
```

### Kontrakt 2 — logika kalendarza akademickiego

`academic_calendar.json` jest parsowany niezależnie przez:
- Python (`ics_export.py`) — przy generowaniu ICS (build time)
- JS (`web/js/schedule-engine.js` / `web/app.js`) — przy wyświetlaniu spotkań (runtime)

---

## Strefy chronione — nie refaktoruj bez wyraźnej instrukcji

### `getLessonMeetingInfo` w `web/js/schedule-engine.js`

Liczy spotkania z uwzględnieniem daySwaps, holidays i przerw.
Ma pokrycie TDD w `tests/test_calendar.js` i `tests/test_schedule_engine.js`. Pętla zawiera guard na `"Inny"` (nieznany dzień)
i twardy cap 200 iteracji — nie usuwaj tych zabezpieczeń.

---

## Nowe zależności — zawsze zapytaj użytkownika

Nie dodawaj pakietów do `requirements.txt` bez zgody właściciela.

---

## Pliki konfiguracyjne — tylko za zgodą właściciela

| Plik | Dlaczego |
|------|---------|
| `data/academic_calendar.json` | Dane rektorskie — muszą być sprawdzone z oficjalnym kalendarzem SGGW |
| `data/subjects_manual.json` | Aliasy nazw przedmiotów — mogą wpłynąć na ICS i cross-reference |
| `TODO.md` | Backlog projektu |
