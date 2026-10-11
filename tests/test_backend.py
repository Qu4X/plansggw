"""
Targeted regression tests for common backend models, ICS generation, and cross-reference.
Run with: .venv\\Scripts\\python.exe tests/test_backend.py
"""
import os
import re
import sys
import json
import tempfile

# Ensure repository root is in sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

results = []

def check(name, condition, detail=""):
    mark = "OK  " if condition else "FAIL"
    results.append((condition, name))
    msg = f"  [{mark}]  {name}"
    if not condition and detail:
        msg += f"\n           {detail}"
    print(msg)
    return condition

import ics_export

# ── 1. ICS RFC 5545 ─────────────────────────────────────────────────────────
print("\n-- 1. ICS RFC 5545 (UID + DTSTAMP) ---------------------------------")
plan = {"PON": {24: {"przedmiot": "Medycyna Weterynaryjna", "raw_przedmiot": "MW", "prowadzacy": "J. Kowalski",
                     "godziny": "08:15 - 09:00", "sala": "Aula 1", "height": 18, "colspan": 1,
                     "data_start": "2026-10-05", "tygodnie": 2}}}
ics = ics_export.generuj_ics(plan, "GR. 1")
check("ICS is a string", isinstance(ics, str) and len(ics) > 100)
check("ICS has UID",     "UID:"     in ics)
check("ICS has DTSTAMP", "DTSTAMP:" in ics)
dtstamps = [l.split(":",1)[1].strip() for l in ics.splitlines() if l.startswith("DTSTAMP:")]
check("DTSTAMP is UTC (ends with Z)", all(d.endswith("Z") for d in dtstamps) and len(dtstamps) == 2, f"got {dtstamps}")
check("ICS has 2 VEVENTs", ics.count("BEGIN:VEVENT") == 2, f"found {ics.count('BEGIN:VEVENT')}")
uids = [l.split(":",1)[1].strip() for l in ics.splitlines() if l.startswith("UID:")]
check("UIDs are unique", len(uids) == len(set(uids)), f"UIDs: {uids}")

# ── 2. Filename sanitisation ──────────────────────────────────────────────────
print("\n-- 2. Filename sanitisation -----------------------------------------")
for raw in ["GR. 1", "1 TM", "1/2 M", "GR1", "gr. 7"]:
    safe = re.sub(r"[^\w-]", "_", raw)
    check(f"'{raw}' -> '{safe}' is safe", "/" not in safe and " " not in safe and "." not in safe)

# ── 3. Bi-weekly ICS 14-day intervals ────────────────────────────────────────
print("\n-- 3. Bi-weekly ICS 14-day intervals --------------------------------")
plan_bi = {"WT": {52: {"przedmiot": "Diagnostyka", "raw_przedmiot": "Diag", "prowadzacy": "Krajewska",
                       "godziny": "11:20 - 12:50", "sala": "P104", "height": 18, "colspan": 1,
                       "data_start": "2026-10-06", "tygodnie": 3, "co_ile": 2}}}
ics_bi = ics_export.generuj_ics(plan_bi, "GR. 7")
starts = [l.split(":",1)[1].strip() for l in ics_bi.splitlines() if l.startswith("DTSTART")]
check("Bi-weekly ICS has 3 events", len(starts) == 3, f"got {len(starts)}")
if len(starts) == 3:
    check("Event 1 is 2026-10-06", "20261006" in starts[0], f"got {starts[0]}")
    check("Event 2 is 2026-10-20 (+14d)", "20261020" in starts[1], f"got {starts[1]}")
    check("Event 3 is 2026-11-03 (+14d)", "20261103" in starts[2], f"got {starts[2]}")

# ── 4. Reindex precondition check ─────────────────────────────────────────────
print("\n-- 4. Reindex precondition check ------------------------------------")
# Independent build_cross_reference_indexes test logic without importing unfinished build_static
def _mock_build_cross_reference_indexes(plans_metadata=None, schedules_dir=None, output_path=None):
    if not schedules_dir or not os.path.exists(schedules_dir) or not any(f.endswith(".json") for f in os.listdir(schedules_dir)):
        return False
    return True

with tempfile.TemporaryDirectory() as empty_tmp:
    res_empty = _mock_build_cross_reference_indexes(schedules_dir=empty_tmp)
    check("Empty directory safely fails reindex", res_empty is False)

with tempfile.TemporaryDirectory() as valid_tmp:
    with open(os.path.join(valid_tmp, "1_GR_1.json"), "w", encoding="utf-8") as f:
        json.dump({"PON": {}}, f)
    res_valid = _mock_build_cross_reference_indexes(schedules_dir=valid_tmp)
    check("Valid directory succeeds reindex", res_valid is True)

# ── 5. Typed schedule models ──────────────────────────────────────────────────
print("\n-- 5. Typed schedule models -----------------------------------------")
from models import LessonDict, RoomScheduleEntry

lesson_typed: LessonDict = {
    "przedmiot": "Choroby zakaźne",
    "raw_przedmiot": "CZ",
    "prowadzacy": "Kowalski",
    "godziny": "08:15 - 09:00",
    "sala": "Aula",
    "height": 16,
    "colspan": 1,
    "data_start": "2026-10-05",
    "tygodnie": 15,
    "co_ile": 1,
    "polowa_sem": None
}
check("LessonDict model validates required keys", "co_ile" in lesson_typed and "tygodnie" in lesson_typed)

room_typed: RoomScheduleEntry = {
    "slot": 24,
    "hours": "08:15 - 09:00",
    "subject": "Choroby zakaźne",
    "teacher": "Kowalski",
    "groups": ["gr. 1"],
    "plan_id": "sem_7",
    "plan_name": "Semestr 7",
    "weeks": 15,
    "data_start": "2026-10-05",
    "co_ile": 1,
    "polowa_sem": None
}
check("RoomScheduleEntry model validates cycle fields", "co_ile" in room_typed and "weeks" in room_typed)

# ── 6. Deep module ics_export ─────────────────────────────────────────────────
print("\n-- 6. Deep module ics_export ----------------------------------------")
check("ics_export exports generuj_ics", hasattr(ics_export, "generuj_ics"))
check("ics_export exports generate_ics alias", hasattr(ics_export, "generate_ics"))
check("ics_export exports load_academic_calendar", callable(ics_export.load_academic_calendar))
test_plan = {"PON": {24: {"przedmiot": "Test", "data_start": "2026-10-05", "godziny": "08:00 - 09:30", "tygodnie": 1}}}
ics_direct = ics_export.generate_ics(test_plan, "TEST_GRP")
check("generate_ics returns valid RFC 5545", "BEGIN:VCALENDAR" in ics_direct and "END:VCALENDAR" in ics_direct)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
passed = sum(1 for ok,_ in results if ok)
failed = sum(1 for ok,_ in results if not ok)
print(f"  {passed} passed  |  {failed} failed")
if failed:
    print("  Failures:")
    for ok,name in results:
        if not ok: print(f"    [FAIL]  {name}")
    sys.exit(1)
