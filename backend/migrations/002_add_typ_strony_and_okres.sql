-- Migracja: Dodanie typu strony i okresu do projektów

-- Dodaj kolumnę typ_strony (enum)
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS typ_strony VARCHAR(50) DEFAULT 'projekt_inzynierski';

-- Dodaj kolumnę okres (np. "XIX", "XX")
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS okres VARCHAR(20);

-- Zaktualizuj istniejące projekty
UPDATE projects
SET okres = 'XIX'
WHERE okres IS NULL AND kontekst_czasowy LIKE '%XIX%';

UPDATE projects
SET okres = 'XX'
WHERE okres IS NULL AND kontekst_czasowy LIKE '%XX%';

-- Dodaj komentarze
COMMENT ON COLUMN projects.typ_strony IS 'Typ strony: projekt_inzynierski lub standardowa';
COMMENT ON COLUMN projects.okres IS 'Okres czasu np. XIX, XX (bez słowa "wiek")';
