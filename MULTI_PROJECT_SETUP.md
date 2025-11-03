# 📁 System Multi-Projektowy - Instrukcja

System obsługuje wiele miejscowości (Czarna, Borowa, etc.) w jednej aplikacji. **Jeden kod - wiele projektów**.

## 🎯 Jak To Działa

### **DANE DLA INNYCH MIEJSCOWOŚCI = OSOBNE BAZY POSTGRESQL**

```
PostgreSQL Server:
├── mapa_czarna_db       ← Czarna + tabela 'projects' (zarządza wszystkimi)
├── borowa_db            ← Borowa (osobna baza)
├── trzebinia_db         ← Trzebinia (osobna baza)
└── ...                  ← Kolejne miejscowości
```

**Tabela `projects` w `mapa_czarna_db` przechowuje metadane wszystkich projektów:**
- ID, nazwa, powiat, województwo, okres danych, etc.
- Która baza jest aktywna

**Dane (właściciele, działki, genealogia) każdej miejscowości są w jej WŁASNEJ bazie PostgreSQL.**

## 🚀 Uruchomienie (SUPER PROSTE)

### Krok 1: Uruchom Launcher

```bash
cd launcher
python launcher_app.py
```

**TO WSZYSTKO!** Launcher automatycznie:
✅ Sprawdzi czy system projektów istnieje
✅ Jeśli nie - utworzy tabelę `projects`
✅ Doda Czarną jako pierwszy projekt
✅ Ustawi wszystko gotowe do pracy

### Krok 2: Uruchom Serwer

W launcherze kliknij: **"🚀 Uruchom Serwer Backend"**

Gotowe! System działa.

## 🆕 Dodawanie Nowej Miejscowości (np. Borowa)

### Metoda 1: Przez API (Najprostsze)

```bash
curl -X POST http://127.0.0.1:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "short_code": "borowa",
    "nazwa": "Borowa",
    "pelna_nazwa": "Gmina Borowa",
    "kontekst_czasowy": "XIX wiek",
    "rok_zrodlowy": 1880,
    "okres_danych": "1850-1900",
    "region": "Powiat Pilźnieński",
    "wojewodztwo": "Podkarpackie"
  }'
```

### Metoda 2: Przez PostgreSQL

```sql
INSERT INTO projects (
    short_code, nazwa, pelna_nazwa, kontekst_czasowy,
    rok_zrodlowy, region, wojewodztwo, db_name
) VALUES (
    'borowa', 'Borowa', 'Gmina Borowa', 'XIX wiek',
    1880, 'Powiat Pilźnieński', 'Podkarpackie', 'borowa_db'
);
```

## 📂 Import Danych Dla Nowej Miejscowości

Po utworzeniu projektu musisz zaimportować dane:

### Krok 1: Utwórz bazę danych (jeśli nie istnieje)

```sql
CREATE DATABASE borowa_db ENCODING 'UTF8';
```

### Krok 2: Zaimportuj strukturę tabel

```bash
# Skopiuj strukturę z Czarnej
pg_dump -s -U postgres mapa_czarna_db > struktura.sql

# Załaduj do nowej bazy
psql -U postgres borowa_db < struktura.sql
```

### Krok 3: Zaimportuj dane

**Opcja A: Z plików JSON**
```bash
# Przełącz na nowy projekt w bazie
UPDATE projects SET is_active = false;
UPDATE projects SET is_active = true WHERE short_code = 'borowa';

# Uruchom serwer (użyje bazy borowa_db)
cd backend
python app.py

# W innym terminalu - import danych
python migrate_data.py
```

**Opcja B: Z SQL dump**
```bash
psql -U postgres borowa_db < dane_borowej.sql
```

**Opcja C: Przez GUI**
- Uruchom launcher
- Kliknij "👥 Edytor Właścicieli"
- Wprowadź dane ręcznie

## 🔄 Przełączanie Między Miejscowościami

### Przez PostgreSQL (Najprostsze)

```sql
-- Zobacz wszystkie projekty
SELECT id, short_code, nazwa, is_active FROM projects;

-- Przełącz na inny projekt
UPDATE projects SET is_active = false;
UPDATE projects SET is_active = true WHERE short_code = 'borowa';
```

### Przez API

```bash
# Przełącz na projekt ID=2
curl -X POST http://127.0.0.1:5000/api/projects/switch/2
```

**POTEM: Zrestartuj serwer backend w launcherze!**

## 📋 API Endpointy

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/api/projects` | Lista wszystkich projektów |
| GET | `/api/projects/{id}` | Szczegóły projektu |
| POST | `/api/projects` | Utwórz nowy projekt |
| PUT | `/api/projects/{id}` | Aktualizuj projekt |
| DELETE | `/api/projects/{id}` | Usuń projekt |
| POST | `/api/projects/switch/{id}` | Przełącz aktywny projekt |
| GET | `/api/project-info` | Metadane aktywnego projektu |

## 💡 Pełny Przykład: Dodanie Borowej

```bash
# 1. Utwórz projekt (automatycznie przez API)
curl -X POST http://127.0.0.1:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"short_code": "borowa", "nazwa": "Borowa", "db_name": "borowa_db"}'

# 2. Utwórz bazę
createdb -U postgres borowa_db

# 3. Skopiuj strukturę
pg_dump -s -U postgres mapa_czarna_db | psql -U postgres borowa_db

# 4. Przełącz na Borową
curl -X POST http://127.0.0.1:5000/api/projects/switch/2

# 5. Zrestartuj serwer w launcherze

# 6. Zaimportuj dane
cd backend
python migrate_data.py  # Albo SQL dump
```

## ❓ FAQ

### Gdzie są dane dla Czarnej?
W bazie `mapa_czarna_db` (tak jak było wcześniej)

### Gdzie będą dane dla Borowej?
W NOWEJ bazie `borowa_db`

### Gdzie jest tabela `projects`?
W bazie master - `mapa_czarna_db`

### Czy muszę robić coś ręcznie przy pierwszym uruchomieniu?
**NIE!** Launcher automatycznie inicjalizuje system projektów.

### Jak zmienić aktywną miejscowość?
```sql
UPDATE projects SET is_active = false;
UPDATE projects SET is_active = true WHERE nazwa = 'Borowa';
```
Potem zrestartuj serwer.

### Czy mogę mieć wszystko w jednej bazie?
Tak, ustaw `use_separate_db = false` w projekcie, wtedy użyje schematów zamiast osobnych baz.

## 🎯 Najważniejsze

✅ **Launcher robi wszystko automatycznie** - nie trzeba ręcznie uruchamiać migracji
✅ **Każda miejscowość = osobna baza PostgreSQL** (domyślnie)
✅ **Tabela `projects` w `mapa_czarna_db`** zarządza wszystkimi
✅ **Przełączanie** = zmiana `is_active` w SQL + restart serwera
✅ **Frontend dynamicznie ładuje** metadane z API

## 📞 Problemy?

1. Sprawdź logi serwera Flask
2. Sprawdź konsolę launchera
3. Sprawdź czy baza PostgreSQL działa:
   ```bash
   psql -U postgres -l  # Lista baz
   ```
