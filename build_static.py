#!/usr/bin/env python3
"""
SGGW Schedule Static Site Generator
Pobiera i parsuje plany zajęć SGGW z SharePoint XLSX, generuje pliki JSON + ICS oraz stronę statyczną do dist/
"""

import os
import re
import sys
import json
import shutil
import argparse
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build_static")

from sggw_client import DEFAULT_WMW_PLANS, discover_wmw_plans, download_plan_file
from sggw_parser import parse_sggw_excel
from ics_export import generuj_ics, load_academic_calendar
from models import LessonDict, RoomScheduleEntry, TeacherScheduleEntry

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_DIR = os.path.join(BASE_DIR, "cache")
WEB_DIR = os.path.join(BASE_DIR, "web")
DIST_DIR = os.path.join(BASE_DIR, "dist")
DATA_DIR = os.path.join(DIST_DIR, "data")
SCHEDULES_DIR = os.path.join(DATA_DIR, "schedules")
CALENDARS_DIR = os.path.join(DIST_DIR, "calendars")


def _get_data_path(filename: str) -> str:
    """Zwraca ścieżkę do pliku danych referencyjnych."""
    p = os.path.join(SRC_DATA_DIR, filename)
    if os.path.exists(p):
        return p
    return os.path.join(BASE_DIR, filename)


def setup_dist_directories():
    """Tworzy katalogi wyjściowe w dist/."""
    os.makedirs(SCHEDULES_DIR, exist_ok=True)
    os.makedirs(CALENDARS_DIR, exist_ok=True)
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Sync app version from package.json into sw.js and index.html
    try:
        from scripts.sync_version import sync_version
        sync_version()
    except Exception as e:
        logger.warning(f"Version sync skipped: {e}")


def copy_web_assets():
    """Kopiuje pliki statyczne z web/ do dist/."""
    logger.info("Copying web assets to dist/...")
    if not os.path.exists(WEB_DIR):
        logger.warning(f"Katalog {WEB_DIR} nie istnieje!")
        return

    for item in os.listdir(WEB_DIR):
        src = os.path.join(WEB_DIR, item)
        dst = os.path.join(DIST_DIR, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    logger.info("Web assets copied successfully.")


def copy_reference_data():
    """Kopiuje pliki konfiguracyjne do dist/data/."""
    logger.info("Copying reference data to dist/data/...")
    os.makedirs(DATA_DIR, exist_ok=True)

    cal_src = _get_data_path("academic_calendar.json")
    cal_dst = os.path.join(DATA_DIR, "academic_calendar.json")
    if os.path.exists(cal_src):
        shutil.copy2(cal_src, cal_dst)
        logger.info("Copied academic_calendar.json -> dist/data/")

    events_src = _get_data_path("events.json")
    events_dst = os.path.join(DATA_DIR, "events.json")
    if os.path.exists(events_src):
        shutil.copy2(events_src, events_dst)
        logger.info("Copied events.json -> dist/data/")


def get_plan_sort_key(plan_entry: tuple) -> tuple:
    """Klucz naturalnego sortowania planów."""
    pid, pdata = plan_entry
    name = (pdata.get("clean_name") or pdata.get("name") or "") if isinstance(pdata, dict) else str(pdata)
    m_sem = re.search(r'\bsem\.?\s*(\d+)\b', name, re.IGNORECASE)
    sem_num = int(m_sem.group(1)) if m_sem else 0
    clean_major = re.sub(r'\bsem\.?\s*\d+\b', '', name, flags=re.IGNORECASE).strip()
    return (clean_major.lower(), sem_num, name)


def build_static(limit: Optional[int] = None, filter_query: Optional[str] = None):
    """Główna funkcja budująca serwis statyczny SGGW."""
    start_time = datetime.now()
    setup_dist_directories()
    copy_web_assets()
    copy_reference_data()

    logger.info("1. Pobieranie / weryfikacja planów SGGW...")
    plans_catalog = DEFAULT_WMW_PLANS

    plans_metadata = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "plans": {}
    }

    total_groups_processed = 0
    discovered_subjects = {}

    for plan_id, plan_info in plans_catalog.items():
        plan_name = plan_info["name"]
        logger.info(f"Przetwarzanie planu: {plan_id} ({plan_name})...")
        
        # Pobieranie lub użycie lokalnego pliku
        cache_xlsx = os.path.join(CACHE_DIR, f"{plan_id}.xlsx")
        temp_xlsx = os.path.join(BASE_DIR, "temp", "semestr_7.xlsx")
        
        if os.path.exists(temp_xlsx) and plan_id == "wmw_sem_7":
            local_xlsx = temp_xlsx
        elif not os.path.exists(cache_xlsx):
            logger.info(f"Pobieranie {plan_id} z SharePoint...")
            download_plan_file(plan_info["sharepoint_url"], cache_xlsx)
            local_xlsx = cache_xlsx
        else:
            local_xlsx = cache_xlsx

        if not os.path.exists(local_xlsx):
            logger.error(f"Brak pliku XLSX dla {plan_id}. Pomijanie.")
            continue

        # Parsowanie arkusza Excel
        parsed_groups_schedule = parse_sggw_excel(local_xlsx)
        def _group_sort_key(g_name: str):
            parts = re.split(r'(\d+)', g_name)
            return [int(p) if p.isdigit() else p.lower() for p in parts]

        groups_list = sorted(list(parsed_groups_schedule.keys()), key=_group_sort_key)

        plan_entry = {
            "name": plan_name,
            "clean_name": plan_name,
            "published_at": datetime.now().strftime("%Y-%m-%d"),
            "version": "1.0",
            "groups": groups_list,
            "mode": "stacjonarne"
        }
        plans_metadata["plans"][plan_id] = plan_entry

        # Zapisanie harmonogramów grup i kalendarzy ICS
        for group_name, schedule_dict in parsed_groups_schedule.items():
            safe_group = re.sub(r'[^\w-]', '_', group_name)
            safe_group_filename = f"{plan_id}_{safe_group}.json"
            json_path = os.path.join(SCHEDULES_DIR, safe_group_filename)
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(schedule_dict, jf, ensure_ascii=False, indent=2)

            # Generowanie kalendarza ICS
            ics_text = generuj_ics(schedule_dict, group_name)
            ics_filename = f"{plan_id}_{safe_group}.ics"
            ics_path = os.path.join(CALENDARS_DIR, ics_filename)
            with open(ics_path, "w", encoding="utf-8") as icsf:
                icsf.write(ics_text)

            total_groups_processed += 1

            # Zbieranie przedmiotów
            for day_slots in schedule_dict.values():
                for lesson_entry in day_slots.values():
                    lessons_list = lesson_entry.values() if (isinstance(lesson_entry, dict) and "przedmiot" not in lesson_entry) else [lesson_entry]
                    for l in lessons_list:
                        raw_sub = l.get("raw_przedmiot")
                        res_sub = l.get("przedmiot")
                        if raw_sub:
                            discovered_subjects[raw_sub] = res_sub

    # Zapis plans.json
    plans_json_path = os.path.join(DATA_DIR, "plans.json")
    with open(plans_json_path, "w", encoding="utf-8") as f:
        json.dump(plans_metadata, f, ensure_ascii=False, indent=2)

    # Indeksy cross-reference (sale, wykładowcy, przedmioty)
    build_cross_reference_indexes(plans_metadata)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Build ukończony w {elapsed:.1f}s!")
    logger.info(f"Zbudowano {len(plans_metadata['plans'])} planów, {total_groups_processed} harmonogramów grup w dist/")


def build_cross_reference_indexes(plans_metadata=None, schedules_dir=SCHEDULES_DIR, output_path=None):
    """Tworzy indeksy wyszukiwania dla Sal, Wykładowców i Przedmiotów."""
    if not os.path.exists(schedules_dir) or not any(f.endswith(".json") for f in os.listdir(schedules_dir)):
        logger.error(f"Katalog harmonogramów '{schedules_dir}' jest pusty.")
        return False

    out_file = output_path or os.path.join(DATA_DIR, "cross_reference.json")
    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)

    teachers_idx = {}
    rooms_idx = {}
    subjects_idx = {}

    plans_info = (plans_metadata or {}).get("plans", {})

    for fname in os.listdir(schedules_dir):
        if not fname.endswith(".json") or fname == "cross_reference.json":
            continue
        base_name = os.path.splitext(fname)[0]
        matched_plan_id = None
        group_raw = "all"
        if plans_info:
            for pid in sorted(plans_info.keys(), key=len, reverse=True):
                if base_name.startswith(pid + "_"):
                    matched_plan_id = pid
                    group_raw = base_name[len(pid) + 1:]
                    break
        if not matched_plan_id:
            parts = base_name.split("_", 1)
            matched_plan_id = parts[0]
            group_raw = parts[1] if len(parts) > 1 else "all"

        plan_id = matched_plan_id
        group_display = group_raw.replace("__", ". ").replace("_", " ")
        if group_display.startswith("gr.  "):
            group_display = group_display.replace("gr.  ", "gr. ")

        plan_meta = plans_info.get(plan_id, {})
        plan_name = plan_meta.get("clean_name") or plan_meta.get("name") or plan_id

        fpath = os.path.join(schedules_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                sched = json.load(f)
        except Exception as e:
            continue

        for day, slots in sched.items():
            if isinstance(slots, dict):
                slot_pairs = slots.items()
            elif isinstance(slots, list):
                slot_pairs = [(i, l) for i, l in enumerate(slots)]
            else:
                continue

            for slot_key, l_data in slot_pairs:
                items = l_data.values() if (isinstance(l_data, dict) and "przedmiot" not in l_data) else [l_data]
                for lesson in items:
                    if not isinstance(lesson, dict):
                        continue
                    sub = lesson.get("przedmiot")
                    room = lesson.get("sala")
                    teacher = lesson.get("prowadzacy")
                    hours = lesson.get("godziny", "")

                    if sub:
                        if sub not in subjects_idx:
                            subjects_idx[sub] = []
                        subjects_idx[sub].append({
                            "plan_id": plan_id,
                            "plan_name": plan_name,
                            "group": group_display,
                            "day": day,
                            "hours": hours,
                            "room": room,
                            "forma": lesson.get("forma", "")
                        })

                    if room and room != "brak sali":
                        if room not in rooms_idx:
                            rooms_idx[room] = {}
                        if day not in rooms_idx[room]:
                            rooms_idx[room][day] = []
                        rooms_idx[room][day].append({
                            "slot": int(slot_key) if str(slot_key).isdigit() else 0,
                            "hours": hours,
                            "subject": sub,
                            "teacher": teacher,
                            "groups": [group_display],
                            "plan_id": plan_id,
                            "plan_name": plan_name,
                            "weeks": lesson.get("tygodnie", 15),
                            "data_start": lesson.get("data_start", "2026-10-01"),
                            "co_ile": lesson.get("co_ile", 1)
                        })

    result_data = {
        "generated_at": datetime.now().isoformat(),
        "teachers": teachers_idx,
        "rooms": rooms_idx,
        "subjects": subjects_idx
    }

    with open(out_file, "w", encoding="utf-8") as out_f:
        json.dump(result_data, out_f, ensure_ascii=False, indent=2)

    logger.info(f"Wygenerowano indeksy cross-reference w {out_file}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generator strony statycznej Plan SGGW")
    parser.add_argument("--limit", type=int, default=None, help="Limit przetwarzanych planów")
    parser.add_argument("--filter", type=str, default=None, help="Filtr nazwy planu")
    args = parser.parse_args()

    build_static(limit=args.limit, filter_query=args.filter)
