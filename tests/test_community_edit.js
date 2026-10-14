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

const CommunityEdit = require(path.join(ROOT_DIR, "web/js/community-edit.js"));
const { renderLessonCard, state } = require(path.join(ROOT_DIR, "web/app.js"));

console.log("\n🧪 Running Community Edit & Supabase Integration TDD Tests...\n");

(async () => {
  // --- Test 1: Voter Token ---
  console.log("-- Test 1: getVoterToken generuje trwały unikalny identyfikator");
  const token1 = CommunityEdit.getVoterToken();
  assert.ok(token1 && token1.startsWith("voter_"), "Token powinien zaczynać się od voter_");
  const token2 = CommunityEdit.getVoterToken();
  assert.strictEqual(token1, token2, "Kolejne wywołanie powinno zwrócić ten sam token z localStorage");
  console.log("✅ [PASS] getVoterToken działa prawidłowo.");

  // --- Test 2: fetchProposals ---
  console.log("\n-- Test 2: fetchProposals poprawnie konstruuje zapytanie REST");
  let capturedUrl = "";
  let capturedHeaders = {};
  global.fetch = async (url, options = {}) => {
    capturedUrl = url;
    capturedHeaders = options.headers || {};
    return {
      ok: true,
      json: async () => [
        {
          id: "prop-123",
          plan_id: "plan-wet-sem-7",
          group_name: "gr. 1",
          subject: "Chirurgia ogólna",
          original_day: "PON",
          original_hours: "08:15 - 10:00",
          new_day: "WT",
          new_hours: "10:15 - 12:00",
          new_room: "Sala 106",
          votes_count: 3,
          status: "pending"
        }
      ]
    };
  };

  const proposals = await CommunityEdit.fetchProposals("plan-wet-sem-7", "gr. 1");
  assert.strictEqual(proposals.length, 1);
  assert.strictEqual(proposals[0].id, "prop-123");
  assert.ok(capturedUrl.includes("plan_id=eq.plan-wet-sem-7"));
  assert.ok(capturedUrl.includes("group_name=eq.gr.%201"));
  assert.ok(capturedHeaders["apikey"], "Powinien przekazywać klucz apikey");
  console.log("✅ [PASS] fetchProposals prawidłowo odpytuje endpoint Supabase.");

  // --- Test 3: fetchUserVotes ---
  console.log("\n-- Test 3: fetchUserVotes zwraca Set z identyfikatorami propozycji");
  global.fetch = async (url) => {
    return {
      ok: true,
      json: async () => [{ proposal_id: "prop-123" }]
    };
  };

  const userVotes = await CommunityEdit.fetchUserVotes(["prop-123", "prop-456"]);
  assert.ok(userVotes.has("prop-123"), "Powinien zawierać oddany głos na prop-123");
  assert.strictEqual(userVotes.has("prop-456"), false);
  console.log("✅ [PASS] fetchUserVotes poprawnie parsuje głosy.");

  // --- Test 4: submitProposal ---
  console.log("\n-- Test 4: submitProposal wysyła propozycję i automatycznie oddaje głos twórcy");
  let postPayload = null;
  let voteCalled = false;
  global.fetch = async (url, options = {}) => {
    if (url.includes("/proposals")) {
      postPayload = JSON.parse(options.body);
      return {
        ok: true,
        json: async () => [{ id: "new-prop-999", ...postPayload }]
      };
    }
    if (url.includes("/votes")) {
      voteCalled = true;
      return { ok: true, json: async () => ({}) };
    }
    return { ok: true, json: async () => [] };
  };

  const created = await CommunityEdit.submitProposal({
    planId: "plan-wet-sem-7",
    groupName: "gr. 1",
    subject: "Farmakologia",
    originalDay: "ŚR",
    originalHours: "12:15 - 14:00",
    newDay: "CZW",
    newHours: "14:15 - 16:00",
    newRoom: "Sala 22",
    reason: "Kolokwium z anatomii"
  });

  assert.strictEqual(created.id, "new-prop-999");
  assert.strictEqual(postPayload.subject, "Farmakologia");
  assert.strictEqual(postPayload.status, "pending");
  assert.strictEqual(voteCalled, true, "submitProposal powinien automatycznie wywołać głosowanie dla twórcy");
  console.log("✅ [PASS] submitProposal poprawnie tworzy propozycję i oddaje głos twórcy.");

  // --- Test 5: UI Renderowanie — propozycja oczekująca (pending) ---
  console.log("\n-- Test 5: renderLessonCard renderuje przycisk i banner głosowania");
  state.communityProposals = [
    {
      id: "prop-pending-1",
      subject: "Rozród zwierząt",
      original_day: "PON",
      original_hours: "08:15 - 10:00",
      new_day: "WT",
      new_hours: "10:15 - 12:00",
      new_room: "Audytorium",
      votes_count: 4,
      status: "pending"
    }
  ];
  state.userVotes = new Set();

  const lesson = {
    przedmiot: "Rozród zwierząt",
    sourceDay: "PON",
    godziny: "08:15 - 10:00",
    sala: "Klinika",
    prowadzacy: "Dr Kowalski"
  };

  const htmlPending = renderLessonCard(lesson);
  assert.ok(htmlPending.includes("btn-propose-change"), "Powinien zawierać przycisk proponowania zmiany");
  assert.ok(htmlPending.includes("proposal-banner"), "Powinien zawierać banner propozycji");
  assert.ok(htmlPending.includes("WT 10:15 - 12:00"), "Powinien wskazywać proponowany nowy termin");
  assert.ok(htmlPending.includes("Popieram (4/10)"), "Powinien zawierać przycisk głosowania z licznikiem");

  // Po oddaniu głosu przycisk powinien pokazywać stan zatwierdzony
  state.userVotes.add("prop-pending-1");
  const htmlVoted = renderLessonCard(lesson);
  assert.ok(htmlVoted.includes("✓ Poparto (4/10)"), "Przycisk powinien pokazywać stan Poparto");
  assert.ok(htmlVoted.includes("disabled"), "Przycisk powinien być zablokowany po oddaniu głosu");
  console.log("✅ [PASS] renderLessonCard poprawnie wyświetla oczekującą propozycję.");

  // --- Test 6: UI Renderowanie — zatwierdzona zmiana terminu (approved, >=10 głosów) ---
  console.log("\n-- Test 6: renderLessonCard podmienia godziny i salę przy zatwierdzonej propozycji (10/10)");
  state.communityProposals = [
    {
      id: "prop-approved-1",
      subject: "Rozród zwierząt",
      original_day: "PON",
      original_hours: "08:15 - 10:00",
      new_day: "WT",
      new_hours: "11:15 - 13:00",
      new_room: "Sala Nowa 200",
      votes_count: 10,
      status: "approved"
    }
  ];

  const htmlApproved = renderLessonCard(lesson);
  assert.ok(htmlApproved.includes("11:15 - 13:00"), "Wyświetlana godzina powinna zostać podmieniona na zatwierdzoną");
  assert.ok(htmlApproved.includes("Sala Nowa 200"), "Wyświetlana sala powinna zostać podmieniona na nową");
  assert.ok(htmlApproved.includes("Przesunięto decyzją grupy"), "Powinien wyświetlać banner zatwierdzenia przez grupę");
  console.log("✅ [PASS] renderLessonCard poprawnie aktualizuje plan po zebraniu 10 głosów.");

  console.log("\n🎉 Wszystkie testy Community Edit zakończone sukcesem (100% PASS)!\n");
  process.exit(0);
})().catch(err => {
  console.error("❌ [FAIL]", err);
  process.exit(1);
});
