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

    def test_extract_room_and_subject(self):
        from sggw_parser import extract_room_and_subject
        # Sala w nazwie zajęć (Wolica sala 106, aula 3)
        sub, room, notes = extract_room_and_subject("Rozród zwierząt gospodarskich Wolica* gr 1 Wolica sala 106, aula 3")
        self.assertEqual(sub, "Rozród zwierząt gospodarskich")
        self.assertEqual(room, "Wolica sala 106, aula 3")

        # Wykład z salą aud 7 b. 24 w drugiej linii
        sub2, room2, _ = extract_room_and_subject("Higiena pasz w.\naud 7 b. 24")
        self.assertEqual(sub2, "Higiena pasz")
        self.assertEqual(room2, "aud 7 b. 24")

        # Zajęcia z grupą i salą w b. 22
        sub3, room3, _ = extract_room_and_subject("Diagn. Obrazowa małych zw. Gr 1,2 06/ambul b. 22 do 10:45")
        self.assertEqual(sub3, "Diagn. Obrazowa małych zw")
        self.assertEqual(room3, "06/ambul b. 22")

        # Zajęcia z salą z ukośnikiem i budynkiem przed salą (Sala 6/7 b. 22)
        sub4, room4, _ = extract_room_and_subject("Choroby zakaźne zwierząt gospodarskich ćw. gr. 1,2 b. 22 Sala  6/7  od 11:00 do 13:15")
        self.assertEqual(sub4, "Choroby zakaźne zwierząt gospodarskich")
        self.assertIn("6/7", room4)

        # Fakultet z 1/2 semestru i salą typu 2131/Aula3 b. 23
        sub5, room5, _ = extract_room_and_subject("Farrmakologia fakultet 1/2  2131/Aula3 b. 23")
        self.assertEqual(sub5, "Farrmakologia")
        self.assertIn("2131/Aula3", room5)

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

    def test_second_half_semester_and_week_restrictions(self):
        if not os.path.exists(self.sample_xlsx):
            self.skipTest(f"Plik fixture {self.sample_xlsx} nie istnieje")

        parsed = parse_sggw_excel(self.sample_xlsx)
        # 1. Środa: Molekularne podstawy (2 poł semestru)
        sr_slots = parsed["gr. 1"]["ŚR"]
        mol_lessons = []
        for slot in sr_slots.values():
            items = slot.values() if isinstance(slot, dict) and "przedmiot" not in slot else [slot]
            for l in items:
                if "Molekularne podstawy" in l.get("przedmiot", ""):
                    mol_lessons.append(l)
        self.assertTrue(len(mol_lessons) > 0, "Powinny istnieć zajęcia z Molekularnych podstaw")
        self.assertEqual(mol_lessons[0].get("polowa_sem"), 2)
        self.assertEqual(mol_lessons[0].get("data_start"), "2026-11-23")
        self.assertEqual(mol_lessons[0].get("tygodnie"), 8)

        # 2. Poniedziałek: Diagn. Obrazowa dużych zw (od 6 tygodnia)
        pon_slots = parsed["gr. 1"]["PON"]
        diag_lessons = []
        for slot in pon_slots.values():
            items = slot.values() if isinstance(slot, dict) and "przedmiot" not in slot else [slot]
            for l in items:
                if "Diagn. Obrazowa dużych zw" in l.get("przedmiot", ""):
                    diag_lessons.append(l)
        self.assertTrue(len(diag_lessons) > 0, "Powinny istnieć zajęcia z Diagn. Obrazowej dużych zw")
        self.assertEqual(diag_lessons[0].get("od_tyg"), 6)
        self.assertEqual(diag_lessons[0].get("data_start"), "2026-11-09")
        self.assertEqual(diag_lessons[0].get("tygodnie"), 10)

    def test_parse_semestr_11_rotations(self):
        sem11_file = os.path.join(REPO_ROOT, "cache", "wmw_sem_11.xlsx")
        if not os.path.exists(sem11_file):
            self.skipTest("cache/wmw_sem_11.xlsx nie istnieje")

        parsed = parse_sggw_excel(sem11_file)
        self.assertIsInstance(parsed, dict)
        # Oczekujemy 14 grup stażowych (1a-7b) + 7 grup dziekańskich (1-7)
        for i in range(1, 8):
            self.assertIn(f"gr. {i}", parsed)
            self.assertIn(f"gr. {i}a", parsed)
            self.assertIn(f"gr. {i}b", parsed)

        # Sprawdzenie wykładu ZZS dla grupy 1a w czwartek
        gr1a_czw = parsed["gr. 1a"]["CZW"]
        self.assertIn("wyklad_zzs", gr1a_czw)
        self.assertEqual(gr1a_czw["wyklad_zzs"]["przedmiot"], "Wykłady ZZS")
        self.assertEqual(gr1a_czw["wyklad_zzs"]["forma"], "wyklad")

        # Sprawdzenie istnienia staży klinicznych
        gr1a_pon = parsed["gr. 1a"]["PON"]
        staz_lessons = [l for k, l in gr1a_pon.items() if l.get("forma") == "staz"]
        self.assertTrue(len(staz_lessons) > 0, "Grupa 1a powinna mieć staże kliniczne w poniedziałki")
        self.assertTrue(any("Staż" in l["przedmiot"] for l in staz_lessons))

    def test_all_cached_semesters_parse_successfully(self):
        expected_min_groups = {
            "wmw_sem_1": 10,
            "wmw_sem_3": 8,
            "wmw_sem_5": 9,
            "wmw_sem_7": 7,
            "wmw_sem_9": 8,
            "wmw_sem_11": 14,
        }
        for plan_id, min_g in expected_min_groups.items():
            fpath = os.path.join(REPO_ROOT, "cache", f"{plan_id}.xlsx")
            if os.path.exists(fpath):
                res = parse_sggw_excel(fpath)
                self.assertGreaterEqual(len(res), min_g, f"{plan_id} powinien mieć co najmniej {min_g} grup")


    def test_extract_groups_ranges_and_slashes(self):
        all_groups = [f"gr. {i}" for i in range(1, 11)]
        # Zakres 1-3
        self.assertEqual(extract_groups_from_text("Anat. zw. gr.  1-3\nprosektorium b. 24", all_groups), ["gr. 1", "gr. 2", "gr. 3"])
        # Zakres 4-7
        self.assertEqual(extract_groups_from_text("Anat. zw. gr.  4-7\nprosektorium b. 24", all_groups), ["gr. 4", "gr. 5", "gr. 6", "gr. 7"])
        # Zakres 8-10 (z 10)
        self.assertEqual(extract_groups_from_text("Anat. zw. gr.  8-10\nprosektorium b. 24", all_groups), ["gr. 8", "gr. 9", "gr. 10"])
        # Slash 1/2 i gwiazdka
        self.assertEqual(extract_groups_from_text("Język łaciński (*)gr. 1/2 s. 35", all_groups), ["gr. 1", "gr. 2"])
        # Slash 4/7
        self.assertEqual(extract_groups_from_text("Język łaciński *\ngr.  4/7 s. 35", all_groups), ["gr. 4", "gr. 7"])
        # Slash 9/10
        self.assertEqual(extract_groups_from_text("Język łaciński (*) gr  9/10 s. 35", all_groups), ["gr. 9", "gr. 10"])
        # 'i' spójnik: gr 1 i 2
        self.assertEqual(extract_groups_from_text("Biologia Kom gr 1 i 2 sala 33", all_groups), ["gr. 1", "gr. 2"])
        # Grupy 1-10
        self.assertEqual(extract_groups_from_text("Technologia informacyjna Grupy 1-10", all_groups), all_groups)
        # grupy 1,2,3,4
        self.assertEqual(extract_groups_from_text("Choroby wewnętrzne grupy 1,2,3,4 Sala 6", all_groups), ["gr. 1", "gr. 2", "gr. 3", "gr. 4"])
        # gr. 1,2– 1071 (1071 to sala, nie grupa)
        self.assertEqual(extract_groups_from_text("Chów i hodowla zwierząt ćw. gr. 1,2– 1071", all_groups), ["gr. 1", "gr. 2"])
        # .3,4 po nazwie
        self.assertEqual(extract_groups_from_text("Choroby zakaźne małych zwierząt.3,4\nSala 119", all_groups), ["gr. 3", "gr. 4"])

    def test_extract_room_and_subject_fixes_sem1(self):
        from sggw_parser import extract_room_and_subject
        # 1. Biofizyka parter -> parter usunięty z nazwy
        sub, room, _ = extract_room_and_subject("Biofizyka wykład                      Aula 7 B. 24 parter")
        self.assertEqual(sub, "Biofizyka")
        self.assertIn("Aula 7", room)
        self.assertNotIn("parter", sub)

        # 2. Anat. zw. gr. 1-3 -> nazwa nie ma -3, znormalizowana do Anatomia zwierząt
        sub, room, _ = extract_room_and_subject("Anat. zw. gr.  1-3\nprosektorium b. 24/parter")
        self.assertEqual(sub, "Anatomia zwierząt")
        self.assertNotIn("-3", sub)
        self.assertIn("prosektorium", room.lower())

        # 3. Język łaciński s. 35 parter -> sala s. 35 b.24, brak s. 35 i parter w tytule
        sub, room, _ = extract_room_and_subject("Język łaciński (*)gr. 1/2 s. 35 b.24/parter")
        self.assertEqual(sub, "Język łaciński")
        self.assertIn("35", room)
        self.assertNotIn("parter", sub)
        self.assertNotIn("s. 35", sub)

        # 4. Psychologia yt 7 1 poł semestru -> likwidacja yt 7, brak 1 poł semestru w tytule
        sub, room, notes = extract_room_and_subject("Psychologia fakultet Audyt 7 b. 24 1 poł semestru")
        self.assertEqual(sub, "Psychologia")
        self.assertIn("Audyt", room)
        self.assertNotIn("yt", sub)
        self.assertNotIn("1 poł semestru", sub)

        # 5. Ekofilozofia 2 piętro -> piętro w sali, nie w tytule
        sub, room, _ = extract_room_and_subject("Ekofilozofia fakultet sala 2065 b 23/ 2 piętro")
        self.assertEqual(sub, "Ekofilozofia")
        self.assertIn("2065", room)
        self.assertNotIn("piętro", sub)

        # 6. Myślenie krytyczne 7 parter -> brak 7 i parter w tytule
        sub, room, _ = extract_room_and_subject("Myślenie krytyczne fakultet  Audytorium 7 b.24/ parter")
        self.assertEqual(sub, "Myślenie krytyczne")
        self.assertIn("Audytorium 7", room)
        self.assertNotIn("parter", sub)
        self.assertNotIn("7", sub)

        # 7. Technologia informacyjna - e-learning stacjonarnie -> sala online, brak e-learning w tytule
        sub, room, _ = extract_room_and_subject("Technologia informacyjna - ćw. e-learning/stacjonarnie\nGrupy 1-10 ( 2-ga połowa semestru)")
        self.assertEqual(sub, "Technologia informacyjna")
        self.assertEqual(room, "online")
        self.assertNotIn("e-learning", sub)
        self.assertNotIn("stacjonarnie", sub)

        # 8. Orientation day
        sub, room, notes = extract_room_and_subject('"Orientation day"  02.10.2026 Aula 1 w budynku 24 godzina 8.00-10.00 (obecność obowiązkowa !!!!!)')
        self.assertEqual(sub, '"Orientation day"')
        self.assertIn("Aula 1", room)
        self.assertNotIn("2026", sub)
        self.assertNotIn("godzina", sub)
        self.assertNotIn("obowiązkowa", sub)

        # 9. Komunikowanie społ. -> Komunikowanie społeczne
        sub, room, _ = extract_room_and_subject("Komunikowanie społ.\nfakultet\nAudyt 1 b. 24/ I pietro")
        self.assertEqual(sub, "Komunikowanie społeczne")
        self.assertIn("Audyt 1", room)

    def test_extract_room_and_subject_fixes_sem3_5_9(self):
        from sggw_parser import extract_room_and_subject
        # Sem 3: Epidemiologia s. 2004 i 50
        sub, room, _ = extract_room_and_subject("Epidemiologia ćw              s.  2004 b. 23 i  50 b. 22 gr 1,2\n8:15-9:45")
        self.assertEqual(sub, "Epidemiologia")
        self.assertIn("2004", room)

        # Sem 3: Fizjologia – s.232
        sub, room, _ = extract_room_and_subject("Fizjologia – ćw.  s.232 b. 24\ngr. 6,7")
        self.assertEqual(sub, "Fizjologia")
        self.assertIn("232", room)

        # Sem 3: Anatomia porównawcza - Prosekt
        sub, room, _ = extract_room_and_subject("Anatomia porównawcza fakultet - ćw. Prosekt b.24\n3 grupy")
        self.assertEqual(sub, "Anatomia porównawcza")
        self.assertIn("Prosekt", room)

        # Sem 3: Mikrobiol -> Mikrobiologia
        sub, room, _ = extract_room_and_subject("Mikrobiol ćw. b.23\ngr.1,2 od 5/6.XI.26")
        self.assertEqual(sub, "Mikrobiologia")

        # Sem 5: FARMAKOLOGIA A2072 2131
        sub, room, _ = extract_room_and_subject("FARMAKOLOGIA ćw. A2072/ 2131 b. 23 gr. 5,6")
        self.assertEqual(sub, "FARMAKOLOGIA")
        self.assertIn("A2072", room)

        # Sem 5: PATOFIZJOLOGIA . 104 105
        sub, room, _ = extract_room_and_subject("PATOFIZJOLOGIA ćw.                             gr 1,2 . 104/105 b 22")
        self.assertEqual(sub, "PATOFIZJOLOGIA")
        self.assertIn("104", room)

        # Sem 5: Jak zarządzać emocjami... 1004 Wyk
        sub, room, _ = extract_room_and_subject("Jak zarządzać emocjami i budować odp psych. fakultet  1004 b.23 Wyk.")
        self.assertEqual(sub, "Jak zarządzać emocjami i budować odp psych.")
        self.assertIn("1004", room)

        # Sem 5: DIAGNOSTYKA... ambulatoria nie ucięte do atoria
        sub, room, _ = extract_room_and_subject("DIAGNOSTYKA KLINICZNA I LABORATORYJNA ćw. 7 grup; Realizacja przedmiotu zgodnie z grafikiem zakładu. b.22  ambulatoria, zajęcia terenowe (Wolica/Obory)")
        self.assertNotIn("atoria", sub)

        # Sem 5: Fakultet 1 zachowany
        sub, room, _ = extract_room_and_subject("Fakultet 1 ćw gr c 2-6 tydz;")
        self.assertTrue(sub.startswith("Fakultet 1"), f"Powinno zaczynać się od Fakultet 1, a jest: {sub}")

        # Sem 9: Fakultety / Toksykologia (nie 'y')
        sub, room, _ = extract_room_and_subject("Fakultety\nToksykologia Kliniczna równolegle\n10 tyg x 3 h\n2072/2004 b 23 od 17:30")
        self.assertNotEqual(sub, "y")
        self.assertIn("Toksykologia Kliniczna", sub)

        # Sem 9: Admin weter s 340 35 -> Administracja weterynaryjna
        sub, room, _ = extract_room_and_subject("Admin weter gr. 3,4 340/35 b.24")
        self.assertEqual(sub, "Administracja weterynaryjna")
        self.assertIn("340/35", room)


if __name__ == "__main__":
    unittest.main()


