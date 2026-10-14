/**
 * CommunityEdit — Moduł edycji społecznościowej i głosowania nad zmianami w planie
 * Plan WMW SGGW
 * Komunikacja z Supabase przez czyste REST API (PostgREST) bez zewnętrznych zależności
 */

(function (root, factory) {
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = factory();
  } else {
    root.CommunityEdit = factory();
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {

  const SUPABASE_URL = "https://ukmxfgmtjhhfmqfhxoft.supabase.co";
  const SUPABASE_ANON_KEY = "sb_publishable_AwUd888lZhVUEVSuMQ4Txw_VSeut73k";

  // Pobranie lub wygenerowanie unikalnego tokenu studenta
  function getVoterToken() {
    const STORAGE_KEY = "plan_wmw_voter_token";
    let token = null;
    try {
      token = localStorage.getItem(STORAGE_KEY);
      if (!token) {
        token = "voter_" + (crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2) + Date.now().toString(36));
        localStorage.setItem(STORAGE_KEY, token);
      }
    } catch (e) {
      token = "voter_anon_" + Math.random().toString(36).substring(2);
    }
    return token;
  }

  const defaultHeaders = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": `Bearer ${SUPABASE_ANON_KEY}`,
    "Content-Type": "application/json",
    "Prefer": "return=representation"
  };

  /**
   * Pobiera wszystkie aktywne i zatwierdzone propozycje dla danego planu i grupy
   */
  async function fetchProposals(planId, groupName) {
    if (!planId || !groupName) return [];
    try {
      const url = `${SUPABASE_URL}/rest/v1/proposals?plan_id=eq.${encodeURIComponent(planId)}&group_name=eq.${encodeURIComponent(groupName)}&select=*&order=created_at.desc`;
      const resp = await fetch(url, { headers: defaultHeaders });
      if (!resp.ok) {
        console.warn("Błąd pobierania propozycji z Supabase:", resp.status);
        return [];
      }
      return await resp.json();
    } catch (err) {
      console.warn("Błąd sieci podczas pobierania propozycji:", err);
      return [];
    }
  }

  /**
   * Sprawdza, na które propozycje dany użytkownik już oddał głos
   */
  async function fetchUserVotes(proposalIds) {
    if (!proposalIds || proposalIds.length === 0) return new Set();
    const token = getVoterToken();
    try {
      const idsParam = `(${proposalIds.map(id => `"${id}"`).join(",")})`;
      const url = `${SUPABASE_URL}/rest/v1/votes?proposal_id=in.${idsParam}&voter_token=eq.${encodeURIComponent(token)}&select=proposal_id`;
      const resp = await fetch(url, { headers: defaultHeaders });
      if (!resp.ok) return new Set();
      const votes = await resp.json();
      return new Set(votes.map(v => v.proposal_id));
    } catch (e) {
      return new Set();
    }
  }

  /**
   * Tworzy nową propozycję zmiany terminu zajęć
   */
  async function submitProposal(proposalData) {
    const token = getVoterToken();
    const payload = {
      plan_id: proposalData.planId,
      group_name: proposalData.groupName,
      subject: proposalData.subject,
      scope: proposalData.scope || "single", // "single" lub "permanent"
      target_date: proposalData.targetDate || null,
      original_day: proposalData.originalDay,
      original_hours: proposalData.originalHours,
      new_day: proposalData.newDay,
      new_hours: proposalData.newHours,
      new_room: proposalData.newRoom || "",
      reason: proposalData.reason || "",
      votes_count: 1,
      status: "pending"
    };

    const resp = await fetch(`${SUPABASE_URL}/rest/v1/proposals`, {
      method: "POST",
      headers: defaultHeaders,
      body: JSON.stringify(payload)
    });

    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(`Nie udało się zgłosić propozycji: ${errText}`);
    }

    const created = await resp.json();
    const proposal = created[0];

    // Automatycznie oddaj pierwszy głos twórcy
    if (proposal && proposal.id) {
      try {
        await castVote(proposal.id);
      } catch (e) {
        // Ignoruj błąd głosu inicjującego
      }
    }

    return proposal;
  }

  /**
   * Oddaje głos na propozycję
   */
  async function castVote(proposalId) {
    const token = getVoterToken();
    const resp = await fetch(`${SUPABASE_URL}/rest/v1/votes`, {
      method: "POST",
      headers: defaultHeaders,
      body: JSON.stringify({
        proposal_id: proposalId,
        voter_token: token
      })
    });

    if (!resp.ok) {
      if (resp.status === 409) {
        throw new Error("Już oddałeś głos na tę propozycję!");
      }
      throw new Error(`Błąd oddawania głosu: ${resp.statusText}`);
    }

    return true;
  }

  return {
    getVoterToken,
    fetchProposals,
    fetchUserVotes,
    submitProposal,
    castVote
  };
});
