-- ==============================================================================
-- Plan WMW SGGW — Supabase Setup & Trigger Fix for Community Edit
-- ==============================================================================

-- 1. Tabela propozycji przesunięcia zajęć
CREATE TABLE IF NOT EXISTS proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    plan_id TEXT NOT NULL,
    group_name TEXT NOT NULL,
    subject TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT 'single',
    target_date DATE,
    original_day TEXT NOT NULL,
    original_hours TEXT NOT NULL,
    new_day TEXT NOT NULL,
    new_hours TEXT NOT NULL,
    new_room TEXT,
    reason TEXT,
    votes_count INT DEFAULT 1,
    status TEXT DEFAULT 'pending'
);

-- 2. Tabela oddanych głosów
CREATE TABLE IF NOT EXISTS votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    proposal_id UUID REFERENCES proposals(id) ON DELETE CASCADE,
    voter_token TEXT NOT NULL,
    UNIQUE(proposal_id, voter_token)
);

-- 3. Row Level Security (RLS)
ALTER TABLE proposals ENABLE ROW LEVEL SECURITY;
ALTER TABLE votes ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public read proposals') THEN
        CREATE POLICY "Public read proposals" ON proposals FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public read votes') THEN
        CREATE POLICY "Public read votes" ON votes FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public insert proposals') THEN
        CREATE POLICY "Public insert proposals" ON proposals FOR INSERT WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Public insert votes') THEN
        CREATE POLICY "Public insert votes" ON votes FOR INSERT WITH CHECK (true);
    END IF;
END $$;

-- 4. Automatyczny licznik głosów i statusu z SECURITY DEFINER
-- WAŻNE: SECURITY DEFINER pozwala triggerowi zaktualizować tabelę proposals
-- z uprawnieniami administratora bazy, omijając brak uprawnień UPDATE dla roli anon.
CREATE OR REPLACE FUNCTION update_proposal_vote_count()
RETURNS TRIGGER 
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    target_proposal_id UUID;
    v_count INT;
BEGIN
    target_proposal_id := COALESCE(NEW.proposal_id, OLD.proposal_id);

    SELECT COUNT(*) INTO v_count 
    FROM votes 
    WHERE proposal_id = target_proposal_id;

    UPDATE proposals
    SET 
        votes_count = v_count,
        status = CASE 
            WHEN v_count >= 10 THEN 'approved'
            ELSE 'pending'
        END
    WHERE id = target_proposal_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 5. Trigger wywoływany przy dodaniu lub usunięciu głosu
DROP TRIGGER IF EXISTS on_vote_added ON votes;
CREATE TRIGGER on_vote_added
AFTER INSERT OR DELETE ON votes
FOR EACH ROW
EXECUTE FUNCTION update_proposal_vote_count();

-- 6. Jednorazowe zsynchronizowanie stanu proposals z aktualnymi głosami w votes
UPDATE proposals p
SET 
    votes_count = (SELECT COUNT(*) FROM votes v WHERE v.proposal_id = p.id),
    status = CASE 
        WHEN (SELECT COUNT(*) FROM votes v WHERE v.proposal_id = p.id) >= 10 THEN 'approved'
        ELSE 'pending'
    END;
