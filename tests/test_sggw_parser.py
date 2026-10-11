"""
Testy TDD parsera arkuszy Excel SGGW (sggw_parser.py).
Run with: .venv\\Scripts\\python.exe tests/test_sggw_parser.py
"""
import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sggw_parser import parse_sggw_excel, extract_groups_from_text, parse_time_bounds


class TestSGGWParser(unittest.TestCase):
    def setUp(self):
        self.sample_xlsx = os.path.join(REPO_ROOT, "temp", "semestr_7.xlsx")

    def test_extract_groups_from_text(self):
        all_groups = [f"gr. {i}" for i in range(1, 8)]
        # Wykład ogólny (brak wzmianki o grupie) -> wszystkie grupy
        self.assertEqual(extract_groups_from_text("Badanie zw rzeźnych wykład", all_groups), all_groups)
        # Pojedyncza grupa
        self.assertEqual(extract_groups_from_text("Chirurgia gr. 1 Wolica", all_groups), ["gr. 1"])
        # Wiele grup: gr. 1, 2
        self.assertEqual(extract_groups_from_text("Badanie mięsa ćw. gr. 1, 2 sale", all_groups), ["gr. 1", "gr. 2"])
        # Wiele grup: Gr 3,4,7
        self.assertEqual(extract_groups_from_text("ćw. Gr 3,4,7 sale", all_groups), ["gr. 3", "gr. 4", "gr. 7"])
        # Wiele grup: gr 5,6
        self.assertEqual(extract_groups_from_text("ćw. gr 5,6 Wolica", all_groups), ["gr. 5", "gr. 6"])

    def test_parse_time_bounds(self):
        # Jawny zakres w tekście "od 8:30 do 10:45"
        self.assertEqual(parse_time_bounds("ćw. od 8:30 do 10:45", "08:15", "11:00"), ("08:30", "10:45"))
        # Jawny start "od 12:30"
        self.assertEqual(parse_time_bounds("ćw. od 12:30", "12:00", "14:00"), ("12:30", "14:00"))
        # Jawny koniec "do 10:45"
        self.assertEqual(parse_time_bounds("ćw. do 10:45", "08:15", "11:00"), ("08:15", "10:45"))
        # Brak jawnego czasu w tekście -> użycie kolumn
        self.assertEqual(parse_time_bounds("Wykład ogólny", "08:15", "09:00"), ("08:15", "09:00"))

    def test_parse_semestr_7_real_file(self):
        if not os.path.exists(self.sample_xlsx):
            self.skipTest(f"Plik fixture {self.sample_xlsx} nie istnieje")

        parsed = parse_sggw_excel(self.sample_xlsx)
        self.assertIsInstance(parsed, dict)
        # Oczekujemy 7 grup
        expected_groups = [f"gr. {i}" for i in range(1, 8)]
        for g in expected_groups:
            self.assertIn(g, parsed, f"Brak grupy {g} w wyniku parsera")
            # Każda grupa ma dni robocze
            g_schedule = parsed[g]
            for day in ["PON", "WT", "ŚR", "CZW", "PT"]:
                self.assertIn(day, g_schedule)

        # Sprawdzenie wykładu wspólnego w PON o 8:15
        for g in expected_groups:
            pon_slots = parsed[g]["PON"]
            all_lessons = [l for slot in pon_slots.values() for l in (slot.values() if isinstance(slot, dict) and "przedmiot" not in slot else [slot])]
            meat_lecture = [l for l in all_lessons if "Badanie zw" in l.get("przedmiot", "")]
            self.assertTrue(len(meat_lecture) > 0, f"Grupa {g} powinna mieć wykład z badania mięsa")
            self.assertEqual(meat_lecture[0]["godziny"], "08:15 - 09:00")
            self.assertEqual(meat_lecture[0]["forma"], "wyklad")

        # Sprawdzenie ćwiczeń gr. 1 w PON (Badanie mięsa 9:00 - 12:00)
        gr1_pon = parsed["gr. 1"]["PON"]
        gr1_lessons = []
        for slot in gr1_pon.values():
            if isinstance(slot, dict) and "przedmiot" in slot:
                gr1_lessons.append(slot)
            elif isinstance(slot, dict):
                gr1_lessons.extend(slot.values())
        gr1_meat = [l for l in gr1_lessons if l.get("forma") == "cwiczenia" and "Badanie zwierząt" in l.get("przedmiot", "")]
        self.assertTrue(len(gr1_meat) > 0, f"Gr. 1 powinna mieć ćwiczenia z badania mięsa w poniedziałek: {gr1_lessons}")


if __name__ == "__main__":
    unittest.main()
