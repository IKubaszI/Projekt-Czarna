-- ================================================================================
-- Migracja 001: Utworzenie tabeli projektów
-- System obsługi wielu instancji miejscowości
-- ================================================================================

-- Tabela główna projektów (przechowywana w bazie master)
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    short_code VARCHAR(50) UNIQUE NOT NULL,  -- np. "czarna", "borowa"
    nazwa VARCHAR(100) NOT NULL,              -- Nazwa krótka projektu
    pelna_nazwa VARCHAR(255),                 -- Pełna nazwa miejscowości
    opis TEXT,                                -- Opis króki projektu

    -- Kontekst czasowy
    kontekst_czasowy VARCHAR(100),            -- np. "XIX wiek"
    rok_zrodlowy INTEGER,                     -- np. 1880
    okres_danych VARCHAR(100),                -- np. "1850-1900"

    -- Geograficzne
    region VARCHAR(100),                      -- np. "Powiat Mielecki"
    wojewodztwo VARCHAR(100),                 -- np. "Podkarpackie"

    -- Dodatkowe
    jezyk_zrodel VARCHAR(100),                -- np. "Polski"
    uwagi TEXT,                               -- Dodatkowe informacje

    -- Status i konfiguracja
    status VARCHAR(20) DEFAULT 'aktywny',     -- aktywny / archiwum
    db_name VARCHAR(100),                     -- Nazwa bazy danych projektu
    db_schema VARCHAR(100) DEFAULT 'public',  -- Schemat w bazie (jeśli używamy jednej bazy)
    use_separate_db BOOLEAN DEFAULT true,     -- Czy osobna baza czy schemat

    -- Metadane systemowe
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT false           -- Czy projekt jest obecnie aktywny
);

-- Indeksy
CREATE INDEX IF NOT EXISTS idx_projects_short_code ON projects(short_code);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_is_active ON projects(is_active);

-- Tabela konfiguracji globalnej systemu (która baza jest aktywna)
CREATE TABLE IF NOT EXISTS system_config (
    klucz VARCHAR(100) PRIMARY KEY,
    wartosc JSONB,
    opis TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wstaw konfigurację aktywnego projektu
INSERT INTO system_config (klucz, wartosc, opis)
VALUES ('active_project_id', 'null', 'ID aktualnie aktywnego projektu')
ON CONFLICT (klucz) DO NOTHING;

-- Funkcja aktualizacji timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger dla aktualizacji timestamp
DROP TRIGGER IF EXISTS update_projects_modtime ON projects;
CREATE TRIGGER update_projects_modtime
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_modified_column();

-- Komentarze
COMMENT ON TABLE projects IS 'Tabela zarządzająca wszystkimi projektami/instancjami miejscowości';
COMMENT ON COLUMN projects.short_code IS 'Unikalny kod projektu używany w URL i ścieżkach';
COMMENT ON COLUMN projects.is_active IS 'Tylko jeden projekt może być aktywny na raz';
