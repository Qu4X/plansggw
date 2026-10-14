const assert = require("assert");
const path = require("path");
const ROOT_DIR = path.resolve(__dirname, "..");

// Mock DOM & localStorage dla środowiska Node.js
const mockStorage = new Map();
global.localStorage = {
  getItem: (key) => mockStorage.get(key) || null,
  setItem: (key, val) => mockStorage.set(key, String(val)),
  removeItem: (key) => mockStorage.delete(key),
  clear: () => mockStorage.clear()
};

const app = require(path.join(ROOT_DIR, "web/app.js"));
const {
  getElectiveSlotKey,
  loadHiddenElectiveSlots,
  saveHiddenElectiveSlots,
  toggleElectiveSlotHidden,
  restoreAllElectiveSlots,
  collectAllElectiveSlots,
  renderLessonCard,
  state
} = app;

console.log("\n🧪 Running Personalized Electives Management TDD Tests...\n");

(async () => {
  // --- Test 1: getElectiveSlotKey ---
  console.log("-- Test 1: getElectiveSlotKey generuje stabilny klucz dla konkretnego terminu");
  const slot1 = {
    przedmiot: "Immunologia kliniczna",
    sourceDay: "WT",
    godziny: "08:15 - 10:00",
    forma: "fakultet"
  };
  const slot2 = {
    przedmiot: "Immunologia kliniczna",
    sourceDay: "WT",
    godziny: "14:00 - 16:00",
    forma: "fakultet"
  };
  const slot3 = {
    przedmiot: "Immunologia kliniczna",
    sourceDay: "CZW",
    godziny: "08:15 - 10:00",
    forma: "fakultet"
  };

  const key1 = getElectiveSlotKey(slot1);
  const key2 = getElectiveSlotKey(slot2);
  const key3 = getElectiveSlotKey(slot3);

  assert.strictEqual(key1, "immunologia_kliniczna__wt__08:15_-_10:00");
  assert.strictEqual(key2, "immunologia_kliniczna__wt__14:00_-_16:00");
  assert.strictEqual(key3, "immunologia_kliniczna__czw__08:15_-_10:00");
  assert.notStrictEqual(key1, key2, "Dwa różne terminy tego samego przedmiotu muszą mieć różne klucze");
  console.log("✅ [PASS] getElectiveSlotKey generuje unikalne klucze dla różnych terminów.");

  // --- Test 2: Persystencja w localStorage ---
  console.log("\n-- Test 2: loadHiddenElectiveSlots i saveHiddenElectiveSlots");
  mockStorage.clear();
  const testSet = new Set([key2, key3]);
  saveHiddenElectiveSlots("wmw_sem_7", "gr. 1", testSet);

  const loadedSet = loadHiddenElectiveSlots("wmw_sem_7", "gr. 1");
  assert.strictEqual(loadedSet.size, 2);
  assert.ok(loadedSet.has(key2));
  assert.ok(loadedSet.has(key3));
  assert.strictEqual(loadedSet.has(key1), false);

  // Inna grupa powinna mieć pusty zestaw
  const otherGroupSet = loadHiddenElectiveSlots("wmw_sem_7", "gr. 2");
  assert.strictEqual(otherGroupSet.size, 0);
  console.log("✅ [PASS] Persystencja w localStorage działa prawidłowo i jest izolowana per grupa.");

  // --- Test 3: Toggle i Restore All ---
  console.log("\n-- Test 3: toggleElectiveSlotHidden oraz restoreAllElectiveSlots");
  state.selectedPlanId = "wmw_sem_7";
  state.selectedGroup = "gr. 1";
  state.hiddenElectiveSlots = new Set([key2]);

  // Ukrywamy dodatkowo slot3
  toggleElectiveSlotHidden(slot3, true);
  assert.ok(state.hiddenElectiveSlots.has(key3));

  // Odkrywamy slot2
  toggleElectiveSlotHidden(slot2, false);
  assert.strictEqual(state.hiddenElectiveSlots.has(key2), false);

  // Przywracamy wszystko
  restoreAllElectiveSlots("wmw_sem_7", "gr. 1");
  assert.strictEqual(state.hiddenElectiveSlots.size, 0);
  console.log("✅ [PASS] toggleElectiveSlotHidden i restoreAllElectiveSlots działają poprawnie.");

  // --- Test 4: renderLessonCard z przyciskiem ukrywania fakultetu ---
  console.log("\n-- Test 4: renderLessonCard dodaje przycisk ukrycia tylko dla formy fakultet");
  const facultyLesson = {
    przedmiot: "Immunologia kliniczna",
    sourceDay: "WT",
    godziny: "08:15 - 10:00",
    sala: "105 w b. 22",
    forma: "fakultet"
  };
  const regularLesson = {
    przedmiot: "Chirurgia ogólna",
    sourceDay: "WT",
    godziny: "10:15 - 12:00",
    sala: "Klinika",
    forma: "cwiczenia"
  };

  const htmlFaculty = renderLessonCard(facultyLesson);
  assert.ok(htmlFaculty.includes("btn-hide-elective"), "Fakultet powinien mieć przycisk .btn-hide-elective");
  assert.ok(htmlFaculty.includes(key1), "Przycisk powinien zawierać data-slot-key");

  const htmlRegular = renderLessonCard(regularLesson);
  assert.strictEqual(htmlRegular.includes("btn-hide-elective"), false, "Zwykłe ćwiczenia nie powinny mieć przycisku ukrywania");
  console.log("✅ [PASS] renderLessonCard warunkowo renderuje przycisk ukrywania tylko dla fakultetów.");

  // --- Test 5: collectAllElectiveSlots z planu ---
  console.log("\n-- Test 5: collectAllElectiveSlots grupuje wszystkie wystąpienia fakultetów");
  const mockSchedule = {
    "WT": {
      "08:15": slot1,
      "14:00": slot2
    },
    "CZW": {
      "08:15": slot3,
      "10:15": regularLesson
    }
  };

  const grouped = collectAllElectiveSlots(mockSchedule);
  assert.ok(grouped["Immunologia kliniczna"], "Powinien zawierać grupę Immunologia kliniczna");
  assert.strictEqual(grouped["Immunologia kliniczna"].length, 3, "Powinien zawierać 3 terminy Immunologii");
  assert.strictEqual(grouped["Chirurgia ogólna"], undefined, "Nie powinien zawierać przedmiotów niebędących fakultetami");
  console.log("✅ [PASS] collectAllElectiveSlots prawidłowo agreguje i grupuje fakultety z planu.");

  console.log("\n🎉 Wszystkie testy Personalized Electives zakończone sukcesem (100% PASS)!\n");
  process.exit(0);
})().catch(err => {
  console.error("❌ [FAIL]", err);
  process.exit(1);
});
