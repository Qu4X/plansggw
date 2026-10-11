# Plan SGGW

Słownik pojęć domenowych dla systemu obsługi i prezentacji planów zajęć Szkoły Głównej Gospodarstwa Wiejskiego w Warszawie (SGGW), w szczególności Wydziału Medycyny Weterynaryjnej (WMW).

## Kalendarz i Dni

**Dzień kalendarzowy**:
Konkretna data w kalendarzu (np. 12 listopada 2026), reprezentująca faktyczny dzień roku.
_Avoid_: Data planu, dzień.

**Dzień bazowy planu**:
Dzień tygodnia, do którego zajęcia są na stałe przypisane w siatce planu uczelni (np. ŚRODA).
_Avoid_: Dzień zajęć, dzień tygodnia.

**Dzień realizowany**:
Dzień tygodnia, według którego planu faktycznie odbywają się zajęcia w danej dacie po uwzględnieniu decyzji rektora (zarządzenia o organizacji roku).
_Avoid_: Dzień zastępczy, dzień efektywny, zamiana.

**Zamiana dnia**:
Zarządzenie rektorskie nakazujące realizację w danym dniu kalendarzowym zajęć z innego dnia bazowego planu (np. 12 listopada 2026 odrabianie środy).
_Avoid_: Odrobienie, przesunięcie, odpracowanie.

**Dzień wolny**:
Dzień kalendarzowy wyłączony z realizacji zajęć dydaktycznych (święto państwowe, kościelne lub dzień rektorski, np. 30 października 2026, 2 listopada 2026).
_Avoid_: Wolne, przerwa.

**Przerwa dydaktyczna**:
Ciągły wielodniowy okres w roku akademickim wolny od zajęć dydaktycznych (np. przerwa świąteczna zimowa: 23–31 grudnia 2026).
_Avoid_: Wakacje, ferie, urlop.

**Okres zajęć dydaktycznych**:
Część semestru przeznaczona na regularne prowadzenie zajęć z siatki planu (w semestrze zimowym 2026/2027: 1 października 2026 r. – 29 stycznia 2027 r.).
_Avoid_: Semestr, okres nauki, czas trwania semestru.

**Sesja zaliczeniowa / egzaminacyjna**:
Okres w roku akademickim następujący po okresie zajęć dydaktycznych, przeznaczony na egzaminy i zaliczenia końcowe (np. sesja zimowa I: 1–12 lutego 2027 r.).
_Avoid_: Sesja, okres egzaminów.

## Jednostki i Czas Zajęć

**Spotkanie**:
Pojedynczy, zaplanowany w siatce blok czasowy danych zajęć w określonym dniu kalendarzowym (np. blok ćwiczeniowy lub wykładowy).
_Avoid_: Zjazd, lekcja, godzina, tydzień.

**Numer spotkania**:
Kolejny numer zrealizowanego lub planowanego spotkania danej grupy z danego przedmiotu.
_Avoid_: Tydzień zajęć, numer tygodnia, numer zjazdu.

**Tydzień semestru**:
Kolejny kalendarzowy tydzień trwania semestru dydaktycznego liczony od daty rozpoczęcia semestru.
_Avoid_: Tydzień przedmiotu, tydzień planu.

**Zakres tygodni zajęć**:
Oznaczenie w planie SGGW wskazujące okres realizacji przedmiotu (np. "1-5 tydzień zajęć", "od 6 tygodnia zajęć", "1. poł semestru").

## Formy Zajęć i Grupy

**Forma zajęć**:
Typ dydaktyczny zajęć: wykład (`wyklad`), ćwiczenia (`cwiczenia`), fakultet (`fakultet`) lub inne formy kliniczne/terenowe.
_Avoid_: Typ zajęć, rodzaj zajęć.

**Grupa ćwiczeniowa**:
Podstawowa grupa studencka na WMW SGGW (np. `gr. 1`, `gr. 2`, ..., `gr. 7`).
_Avoid_: Podgrupa, grupa mała.

**Wykład ogólny**:
Zajęcia wspólne dla całego rocznika / semestru (wszystkich grup ćwiczeniowych).
_Avoid_: Cały rok, audytorium.

## Źródło Danych i Integracja

**Arkusz Excel (SharePoint XLSX)**:
Publicznie udostępniany przez wydział plik arkusza kalkulacyjnego (`.xlsx`), stanowiący pierwotne źródło prawdy o siatce planu.

**Subskrypcja kalendarza**:
Dynamiczne połączenie za pośrednictwem protokołu `webcal://`, zapewniające automatyczne odświeżanie terminów zajęć w zewnętrznym kalendarzu użytkownika (Google Calendar, Apple Calendar itp.).

**Plik kalendarza**:
Statyczny plik w formacie iCalendar (`.ics`), reprezentujący jednorazową migawkę terminów zajęć w chwili pobrania.
