# Instrukcja Testowania Ładowania .env

## Co Zostało Zmienione

### 1. System ładowania .env z katalogów projektów
- `app.py` teraz automatycznie ładuje `.env` z katalogu aktywnego projektu
- Kolejność ładowania:
  1. Domyślny `.env` (backend/.env lub główny katalog)
  2. Sprawdzenie aktywnego projektu w bazie
  3. Załadowanie `.env` projektu z `backup/{Nazwa}/.env`

### 2. Obsługa błędów
- Aplikacja **NIE crashuje** gdy dane w .env są błędne
- Wyświetla ostrzeżenia i działa w trybie awaryjnym
- Pozwala na sprawdzenie i poprawienie konfiguracji

## Struktura Plików .env

```
backup/
├── Czarna/
│   ├── .env               ← Konfiguracja dla Czarnej
│   └── .env.test-bad      ← Przykład z błędnymi danymi
└── Borowa/
    └── .env               ← Konfiguracja dla Borowej
```

## Testowanie z Poprawnymi Danymi

### 1. Czarna (domyślny projekt)

Plik: `backup/Czarna/.env`
```env
DB_HOST=localhost
DB_NAME=mapa_czarna_db
DB_USER=postgres
DB_PASSWORD=1234
DB_PORT=5432
PROJECT_SHORT_CODE=czarna
```

**Uruchom serwer:**
```bash
cd backend
python app.py
```

**Oczekiwany output:**
```
================================================================================
🔧 ŁADOWANIE KONFIGURACJI PROJEKTU
================================================================================
⚠️ Brak domyślnego .env - używam zmiennych systemowych

📊 Konfiguracja bazy master:
   Host: localhost:5432
   Database: mapa_czarna_db
   User: postgres

🔌 Próba połączenia z bazą master...
✅ Znaleziono aktywny projekt: Czarna (czarna)
✅ Załadowano .env projektu z: /home/user/Projekt-Czarna/backup/Czarna/.env
✅ Połączenie z bazą OK
================================================================================
```

## Testowanie z Błędnymi Danymi

### 1. Użyj pliku testowego z błędnymi danymi

```bash
# Skopiuj plik testowy jako aktywny .env
cp backup/Czarna/.env.test-bad backup/Czarna/.env

# Uruchom serwer
cd backend
python app.py
```

**Oczekiwany output:**
```
================================================================================
🔧 ŁADOWANIE KONFIGURACJI PROJEKTU
================================================================================
⚠️ Brak domyślnego .env - używam zmiennych systemowych

📊 Konfiguracja bazy master:
   Host: localhost:5432
   Database: NIEPOPRAWNA_BAZA_TESTOWA
   User: ZLYUSER

🔌 Próba połączenia z bazą master...

❌ BŁĄD POŁĄCZENIA Z BAZĄ DANYCH!
   Szczegóły: FATAL:  password authentication failed for user "ZLYUSER"
   ⚠️ Aplikacja będzie działać w trybie awaryjnym
   ⚠️ Sprawdź plik .env i upewnij się że PostgreSQL działa

💡 Możesz teraz sprawdzić/poprawić konfigurację w .env
================================================================================

⚠️ Nie można zainicjalizować systemu projektów: ...
⚠️ System będzie działać w trybie legacy (bez obsługi projektów)

 * Running on http://127.0.0.1:5000
```

**Ważne:** Aplikacja się uruchomi mimo błędnych danych! Możesz:
- Sprawdzić logi i zobaczyć błąd
- Poprawić plik `.env`
- Zrestartować serwer

### 2. Test z różnymi bazami dla Czarnej i Borowej

**Czarna:** `backup/Czarna/.env`
```env
DB_NAME=mapa_czarna_db
DB_USER=postgres
DB_PASSWORD=1234
```

**Borowa:** `backup/Borowa/.env`
```env
DB_NAME=borowa_db
DB_USER=postgres
DB_PASSWORD=1234
```

**Przełącz aktywny projekt w PostgreSQL:**
```sql
-- Przełącz na Czarną
UPDATE projects SET is_active = false;
UPDATE projects SET is_active = true WHERE short_code = 'czarna';
```

**Zrestartuj serwer** - automatycznie załaduje `.env` z `backup/Czarna/.env`

```sql
-- Przełącz na Borową
UPDATE projects SET is_active = false;
UPDATE projects SET is_active = true WHERE short_code = 'borowa';
```

**Zrestartuj serwer** - automatycznie załaduje `.env` z `backup/Borowa/.env`

## Sprawdzanie Co Zostało Załadowane

Po uruchomieniu serwera, sprawdź logi startowe:
```
================================================================================
🔧 ŁADOWANIE KONFIGURACJI PROJEKTU
================================================================================
```

W tej sekcji zobaczysz:
- Czy załadowano domyślny .env
- Z jakiej bazy próbuje się połączyć
- Który projekt jest aktywny
- Czy załadowano .env projektu
- Czy połączenie z bazą działa

## Debugowanie

### Problem: "Brak domyślnego .env"
**Rozwiązanie:** To normalne, jeśli nie ma pliku `.env` w `backend/` lub głównym katalogu. System użyje zmiennych systemowych lub wartości z `.env` projektu.

### Problem: "BŁĄD POŁĄCZENIA Z BAZĄ"
**Rozwiązanie:**
1. Sprawdź czy PostgreSQL działa: `psql -U postgres -l`
2. Sprawdź dane w pliku `.env` projektu
3. Sprawdź hasło: `DB_PASSWORD=...`

### Problem: "Brak aktywnego projektu"
**Rozwiązanie:**
```sql
-- Ustaw Czarną jako aktywną
UPDATE projects SET is_active = false;
UPDATE projects SET is_active = true WHERE short_code = 'czarna';
```

### Problem: "Tabela projects nie istnieje"
**Rozwiązanie:** Uruchom launcher:
```bash
cd launcher
python launcher_app.py
```

## Podsumowanie

✅ **System działa!**
- Każdy projekt ma swój `.env` w `backup/{Nazwa}/.env`
- Automatyczne ładowanie na podstawie aktywnego projektu
- Obsługa błędów - aplikacja nie crashuje
- Łatwe przełączanie między projektami (zmiana `is_active` w bazie + restart)

✅ **Można testować z błędnymi danymi!**
- Użyj pliku `.env.test-bad`
- Aplikacja się uruchomi z ostrzeżeniami
- Możesz sprawdzić i poprawić konfigurację
