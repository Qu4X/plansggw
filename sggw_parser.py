"""
Parser siatki planów zajęć SGGW z arkuszy Excel (.xlsx).
"""
import re
import os
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
import openpyxl

logger = logging.getLogger("sggw_parser")

DAY_NAME_MAP = {
    "poniedziałek": "PON",
    "poniedzialek": "PON",
    "wtorek": "WT",
    "środa": "ŚR",
    "sroda": "ŚR",
    "czwartek": "CZW",
    "piątek": "PT",
    "piatek": "PT"
}


def parse_time_bounds(text: str, default_start: str, default_end: str) -> Tuple[str, str]:
    """
    Wyznacza godziny rozpoczęcia i zakończenia zajęć.
    Jeśli w tekście podano jawne 'od XX:YY do AA:BB' lub 'od XX:YY' / 'do AA:BB', ma to priorytet.
    """
    start_time = default_start
    end_time = default_end

    # Format: od HH:MM do HH:MM lub HH:MM - HH:MM
    range_match = re.search(r'(?:od\s*)?(\d{1,2}[:.]\d{2})\s*(?:do|-)\s*(\d{1,2}[:.]\d{2})', text, re.IGNORECASE)
    if range_match:
        s = range_match.group(1).replace(".", ":")
        e = range_match.group(2).replace(".", ":")
        return (f"{int(s.split(':')[0]):02d}:{s.split(':')[1]}", f"{int(e.split(':')[0]):02d}:{e.split(':')[1]}")

    # Format: tylko "od HH:MM"
    from_match = re.search(r'\bod\s*(\d{1,2}[:.]\d{2})', text, re.IGNORECASE)
    if from_match:
        s = from_match.group(1).replace(".", ":")
        start_time = f"{int(s.split(':')[0]):02d}:{s.split(':')[1]}"

    # Format: tylko "do HH:MM"
    to_match = re.search(r'\bdo\s*(\d{1,2}[:.]\d{2})', text, re.IGNORECASE)
    if to_match:
        e = to_match.group(1).replace(".", ":")
        end_time = f"{int(e.split(':')[0]):02d}:{e.split(':')[1]}"

    return (start_time, end_time)


def extract_groups_from_text(text: str, all_groups: List[str]) -> List[str]:
    """
    Identyfikuje grupy ćwiczeniowe z tekstu komórki.
    Jeśli brak wzmianki o grupie (lub wykład dla rocznika/fakultet), zwraca wszystkie grupy.
    """
    clean_text = text.replace("\n", " ")
    
    # Wykrywanie wzorców grup: 'gr. 1, 2', 'Gr 3,4,7', 'gr. 5, 6', 'gr 1'
    group_matches = re.findall(r'(?:gr\.?|grupa|grup)\s*([0-9\s,]+)', clean_text, re.IGNORECASE)
    if group_matches:
        target_group_nums = set()
        for gm in group_matches:
            # Rozbicie po przecinkach i spacjach
            nums = re.findall(r'\b([1-9])\b', gm)
            target_group_nums.update(int(n) for n in nums)
        
        matched_groups = [f"gr. {n}" for n in sorted(target_group_nums) if f"gr. {n}" in all_groups]
        if matched_groups:
            return matched_groups

    # Jeśli nie wykryto żadnej specyficznej grupy -> zajęcia wspólne / dla wszystkich
    return list(all_groups)


def classify_sggw_form(text: str) -> str:
    """Klasyfikuje formę zajęć na podstawie treści komórki."""
    lower = text.lower()
    if "fakultet" in lower:
        return "fakultet"
    if "ćw" in lower or "ćwiczen" in lower:
        return "cwiczenia"
    if "wykład" in lower or "wyklad" in lower or lower.strip().endswith(" w.") or " w." in lower:
        return "wyklad"
    if "lab" in lower:
        return "laboratorium"
    return "cwiczenia"


ROOM_PATTERNS = [
    r'(\b\d{2,4}\s*/\s*Aula\s*\d*(?:\s*b\.?\s*\d+)?)',
    r'(Wolica\s*sala\s*\d+,\s*aula\s*\d+)',
    r'(Wolica\s*sala\s*\d+)',
    r'(sala\s*\d+,\s*aula\s*\d+)',
    r'(sala\s*109/ambulatorium/Obory)',
    r'(sala109/ambulatorium/Obory)',
    r'(06/ambul(?:\s*b\.?\s*\d+)?)',
    r'(sale\s*zakładu(?:\s*b\.?\s*\d+)?)',
    r'(sala\s*sekcyjna(?:\s*/\s*sala\s*ćwiczeniowa)?)',
    r'(aud\s*\d*(?:\s*b\.?\s*\d+)?)',
    r'(aud\s*b\.?\s*\d+)',
    r'(Aula\s*\d*(?:\s*b\.?\s*\d+)?)',
    r'(Audytorium(?:\s*b\.?\s*\d+)?)',
    r'((?:b\.?\s*\d+\s+)?sala\s*\d+(?:[a-z])?(?:/\d+)?(?:\s*b\.?\s*\d+)?)',
    r'(s\s*\d+\s*b\.?\s*\d+)',
    r'(\b\d{2,4}\s*w\s*b\.?\s*\d+)',
    r'(\b\d{2,4}\s*w\s*\d+)',
    r'(Wolica)',
    r'(Obory)',
    r'(b\.?\s*2[2-4])'
]

SUBJECT_METADATA_PATTERNS = [
    r'(\b\d{1,2}[:.]\d{2}\b|\bod\s*\d{1,2}[:.]\d{2}!?\b|\bdo\s*\d{1,2}[:.]\d{2}!?\b)',
    r'(od\s*\d+\s*tygodnia(?:\s*zaj[eę]ć)?|1-\d+\s*tydzień(?:\s*zaj[eę]ć)?|2\s*poł\s*semestru|1\.\s*poł\s*semestru|\b1/2\b|\b2/2\b)',
    r'\bgr\.?\s*[\d,\s]+|\bgr\s*[\d,\s]+',
    r'\b\d{2,4}\s*/\s*Aula\s*\d*(?:\s*b\.?\s*\d+)?',
    r'sala\s*sekcyjna(?:\s*/\s*sala\s*ćwiczeniowa)?|sale\s*zakładu(?:\s*b\.?\s*\d+)?|(?:b\.?\s*\d+\s+)?sala\s*\d+[a-z]?(?:/\d+)?(?:\s*b\.?\s*\d+)?|aula\s*\d*|audytorium|aud\s*\d*|ambulatorium|ambul',
    r'\b\d{2,4}\s*w\s*b\.?\s*\d+|\b\d{2,4}\s*w\s*\d+|\bs\s*\d+\s*b\.?\s*\d+|\b06/ambul\b',
    r'b\.?\s*\d+',
    r'\bWolica\b|\bObory\b',
    r'\bćw\.?|\bćwiczenia|\bwykład\b|\bwyklad\b|\bfakultet\.?|\bw\.(?!\w)|\bw\b'
]


def extract_room_and_subject(text: str) -> Tuple[str, str, str]:
    """
    Wyodrębnia nazwę przedmiotu, salę oraz uwagi z tekstu komórki.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return ("", "", "")

    full_text = " ".join(lines)

    # 1. Wykrywanie sali
    room = ""
    for rp in ROOM_PATTERNS:
        m = re.search(rp, full_text, re.IGNORECASE)
        if m:
            room = m.group(1).strip()
            break

    # 2. Wyodrębnienie i oczyszczenie nazwy przedmiotu
    first_line = lines[0]
    subject = first_line
    for pat in SUBJECT_METADATA_PATTERNS:
        subject = re.sub(pat, '', subject, flags=re.IGNORECASE)
    subject = re.sub(r'[*!,;:/()]+', ' ', subject)
    subject = ' '.join(subject.split()).strip()
    subject = re.sub(r'\s+[1-9]$', '', subject).strip()
    subject = re.sub(r'^[.\-\s]+|[.\-\s]+$', '', subject)

    if not subject:
        # Fallback do pierwszej linii bez dopisku formy
        subject = re.sub(r'\s*(?:wykład|wyklad|ćw\.?|cw\.?|ćwiczenia|fakultet).*$', '', first_line, flags=re.IGNORECASE).strip()
        if not subject:
            subject = first_line

    # 3. Uwagi / tygodnie
    notes = ""
    week_notes = re.findall(r'(?:od\s*\d+\s*tygodnia|1-\d+\s*tydzień|2\s*poł\s*semestru|1\.\s*poł\s*semestru|od\s*\d+:\d+!)', full_text, re.IGNORECASE)
    if week_notes:
        notes = ", ".join(week_notes)

    return (subject, room, notes)


def parse_sggw_excel(wb_or_path: Union[str, openpyxl.Workbook]) -> Dict[str, Dict[str, Dict[int, Any]]]:
    """
    Główna funkcja parsująca arkusz planu zajęć SGGW.
    Zwraca słownik:
    {
       "gr. 1": { "PON": { slot: lesson, ... }, "WT": ... },
       ...
       "gr. 7": ...
    }
    """
    if isinstance(wb_or_path, str):
        wb = openpyxl.load_workbook(wb_or_path, data_only=True)
    else:
        wb = wb_or_path

    sheet = wb.active

    # 1. Odczyt kolumn czasowych z wiersza 2
    time_columns: Dict[int, Tuple[str, str]] = {}
    for col in range(3, sheet.max_column + 1):
        v = sheet.cell(2, col).value
        if v:
            v_str = str(v).strip()
            m = re.search(r'(\d{1,2}[:.]\d{2})\s*-\s*(\d{1,2}[:.]\d{2})', v_str)
            if m:
                s = m.group(1).replace(".", ":")
                e = m.group(2).replace(".", ":")
                sh = f"{int(s.split(':')[0]):02d}:{s.split(':')[1]}"
                eh = f"{int(e.split(':')[0]):02d}:{e.split(':')[1]}"
                time_columns[col] = (sh, eh)

    # 2. Wykrycie liczby grup (z wiersza 1 lub domyślnie 7)
    title_val = str(sheet.cell(1, 2).value or "")
    m_groups = re.search(r'(\d+)\s*grup', title_val, re.IGNORECASE)
    total_groups_num = int(m_groups.group(1)) if m_groups else 7
    all_groups = [f"gr. {i}" for i in range(1, total_groups_num + 1)]

    # Przygotowanie struktury wyjściowej dla każdej grupy
    result: Dict[str, Dict[str, Dict[int, Any]]] = {
        g: {d: {} for d in ["PON", "WT", "ŚR", "CZW", "PT"]} for g in all_groups
    }

    # 3. Indeksowanie scalonych komórek
    merged_map: Dict[Tuple[int, int], Tuple[int, int, int, int]] = {}
    for rng in sheet.merged_cells.ranges:
        for r in range(rng.min_row, rng.max_row + 1):
            for c in range(rng.min_col, rng.max_col + 1):
                merged_map[(r, c)] = (rng.min_row, rng.min_col, rng.max_row, rng.max_col)

    # 4. Przejście po wierszach i dniach tygodnia
    current_day = ""
    processed_top_lefts = set()

    for r in range(3, sheet.max_row + 1):
        # Sprawdzenie dnia w kolumnie B (2)
        day_cell = sheet.cell(r, 2).value
        if day_cell:
            day_text = str(day_cell).strip().lower()
            if day_text in DAY_NAME_MAP:
                current_day = DAY_NAME_MAP[day_text]

        if not current_day:
            continue

        for c in range(3, sheet.max_column + 1):
            cell_val = sheet.cell(r, c).value
            if not cell_val or not str(cell_val).strip():
                continue

            content = str(cell_val).strip()
            # Ignorowanie legendy / przypisów na dole
            if content.startswith("* Szczegółowy") or content.startswith("Plan zajęć"):
                continue

            # Sprawdzenie czy komórka jest częścią zakresu scalonego
            if (r, c) in merged_map:
                min_r, min_c, max_r, max_c = merged_map[(r, c)]
                if (min_r, min_c) in processed_top_lefts:
                    continue
                processed_top_lefts.add((min_r, min_c))
                start_col = min_c
                end_col = max_c
            else:
                start_col = c
                end_col = c

            # Wyznaczenie domyślnych godzin z kolumn
            def_start = time_columns.get(start_col, ("08:00", "09:00"))[0]
            def_end = time_columns.get(end_col, ("09:00", "10:00"))[1]

            actual_start, actual_end = parse_time_bounds(content, def_start, def_end)
            godziny_str = f"{actual_start} - {actual_end}"

            # Slot bazowy liczony jako minuty od 07:00 / 5
            try:
                sh_val, sm_val = map(int, actual_start.split(":"))
                eh_val, em_val = map(int, actual_end.split(":"))
                base_slot = ((sh_val - 7) * 60 + sm_val) // 5
                duration_min = (eh_val * 60 + em_val) - (sh_val * 60 + sm_val)
                height = duration_min // 5
            except Exception:
                base_slot = (start_col - 3) * 12 + 12
                height = (end_col - start_col + 1) * 12

            # Wyodrębnienie grup, przedmiotu i sali
            target_groups = extract_groups_from_text(content, all_groups)
            forma = classify_sggw_form(content)
            subject, room, notes = extract_room_and_subject(content)

            # Tygodnie i cykle
            weeks = 15
            co_ile = 1
            od_tyg = 1
            polowa_sem = None
            if "1-5 tydzień" in content or "1-5 tyg" in content:
                weeks = 5
            elif "od 6 tygodnia" in content:
                weeks = 10
                od_tyg = 6
            elif "1. poł semestru" in content or "1 poł sem" in content:
                weeks = 7
                polowa_sem = 1
            elif "2 poł semestru" in content or "2 poł sem" in content:
                weeks = 8
                polowa_sem = 2

            lesson_dict = {
                "przedmiot": subject,
                "raw_przedmiot": subject,
                "prowadzacy": "",
                "godziny": godziny_str,
                "sala": room or "brak sali",
                "height": height,
                "colspan": 1,
                "data_start": "2026-10-01",
                "tygodnie": weeks,
                "co_ile": co_ile,
                "od_tyg": od_tyg,
                "polowa_sem": polowa_sem,
                "forma": forma,
                "uwagi": notes
            }

            # Zapisanie do każdej zainteresowanej grupy
            for grp in target_groups:
                day_slots = result[grp][current_day]
                # Obsługa ewentualnych kolizji slotów (np. 2 zajęcia o tej samej godzinie)
                if base_slot not in day_slots:
                    day_slots[base_slot] = lesson_dict
                else:
                    existing = day_slots[base_slot]
                    if isinstance(existing, dict) and "przedmiot" in existing:
                        day_slots[base_slot] = {0: existing, 1: lesson_dict}
                    elif isinstance(existing, dict):
                        existing[len(existing)] = lesson_dict

    return result
