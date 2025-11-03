# 📁 System Multi-Projektowy - Instrukcja Uruchomienia

System został rozbudowany o możliwość obsługi wielu instancji/projektów miejscowości (Czarna, Borowa, etc.) z dynamicznym przełączaniem i edycją metadanych.

## 🎯 Kluczowe Funkcje

✅ **Jeden kod, wiele projektów** - aplikacja obsługuje wiele projektów bez duplikacji kodu
✅ **Dynamiczne przełączanie** - łatwa zmiana aktywnego projektu z GUI lub API
✅ **Izolacja danych** - dane projektów są całkowicie oddzielone
✅ **Tryb legacy** - system działa z istniejącymi danymi bez zmian
✅ **API zarządzania** - pełne API REST do zarządzania projektami

## 📋 Wymagania

- Python 3.8+
- PostgreSQL 12+
- Zainstalowane zależności: `pip install -r requirements.txt`

## 🚀 Uruchomienie Systemu Multi-Projektowego

### Krok 1: Migracja Istniejących Danych

Uruchom skrypt migracyjny, który:
- Utworzy tabelę `projects` w bazie master
- Doda "Czarna" jako pierwszy projekt
- Ustawi Czarną jako aktywny projekt

```bash
cd backend
python migrations/migrate_to_multi_project.py
```

### Krok 2: Uruchom Serwer Backend

```bash
cd backend
python app.py
```

Serwer uruchomi się z systemem projektów i automatycznie załaduje aktywny projekt (Czarna).

### Krok 3: Sprawdź Status Projektu

Otwórz przeglądarkę i sprawdź:

```
http://127.0.0.1:5000/api/project-info
```

Powinno zwrócić metadane aktywnego projektu.

### Krok 4: Uruchom Launcher z Zarządzaniem Projektami

```bash
cd launcher
python launcher_app.py
```

W górnej części launchera zobaczysz nową sekcję "📁 Zarządzanie Projektami" z:
- Dropdown wyboru projektu
- Przycisk "➕ Nowy" - tworzenie nowego projektu
- Przycisk "⚙️ Edytuj" - edycja metadanych projektu

## 📊 Struktura Projektów

```
projekt-czarna/
├── backend/
│   ├── app.py                    # Backend z obsługą projektów
│   ├── project_manager.py        # Manager projektów
│   └── migrations/
│       ├── 001_create_projects_table.sql
│       └── migrate_to_multi_project.py
├── launcher/
│   ├── launcher_app.py           # Launcher z GUI projektów
│   └── project_selector.py       # Widget selektora projektów
├── projects/                     # Folder z danymi projektów
│   └── czarna/
│       ├── data/
│       ├── geojson/
│       └── backups/
└── assets/
    └── js/
        └── project-loader.js     # Frontend loader metadanych
```

## 🆕 Tworzenie Nowego Projektu

### Opcja 1: Przez Launcher GUI

1. Otwórz launcher
2. Kliknij "➕ Nowy" w sekcji zarządzania projektami
3. Wypełnij formularz:
   - **Kod projektu*** - unikalny kod (np. "borowa")
   - **Nazwa krótka*** - nazwa wyświetlana (np. "Borowa")
   - **Pełna nazwa** - pełna nazwa miejscowości
   - **Kontekst czasowy** - epoka/wiek (np. "XIX wiek")
   - **Rok źródłowy** - główny rok danych
   - **Okres danych** - zakres lat (np. "1850-1900")
   - **Region** - region geograficzny
   - **Województwo** - województwo
4. Kliknij "💾 Zapisz"

### Opcja 2: Przez API

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
    "region": "Powiat Mielecki",
    "wojewodztwo": "Podkarpackie",
    "jezyk_zrodel": "Polski",
    "opis": "System mapy katastralnej dla Borowej"
  }'
```

### Opcja 3: Przez PostgreSQL

```sql
INSERT INTO projects (
    short_code, nazwa, pelna_nazwa, kontekst_czasowy,
    rok_zrodlowy, okres_danych, region, wojewodztwo
) VALUES (
    'borowa', 'Borowa', 'Gmina Borowa', 'XIX wiek',
    1880, '1850-1900', 'Powiat Mielecki', 'Podkarpackie'
);
```

## 🔄 Przełączanie Między Projektami

### Przez Launcher

1. W dropdownie "📁 Projekt:" wybierz inny projekt
2. Potwierdź przełączenie
3. Zrestartuj serwer backend (launcher zapyta o restart)

### Przez API

```bash
curl -X POST http://127.0.0.1:5000/api/projects/switch/2
```

(gdzie 2 to ID projektu do aktywacji)

## 📝 API Endpointy

| Metoda | Endpoint | Opis |
|--------|----------|------|
| GET | `/api/projects` | Lista wszystkich projektów |
| GET | `/api/projects/{id}` | Szczegóły projektu |
| POST | `/api/projects` | Utwórz nowy projekt |
| PUT | `/api/projects/{id}` | Aktualizuj projekt |
| DELETE | `/api/projects/{id}` | Usuń projekt |
| POST | `/api/projects/switch/{id}` | Przełącz aktywny projekt |
| GET | `/api/project-info` | Metadane aktywnego projektu |

## 🎨 Frontend - Dynamiczne Metadane

### Auto-inicjalizacja

Dodaj atrybut `data-project-auto-init` do `<html>`:

```html
<!DOCTYPE html>
<html lang="pl" data-project-auto-init>
<head>
    <script src="/assets/js/project-loader.js"></script>
    ...
```

### Ręczna inicjalizacja

```javascript
// Załaduj metadane projektu
ProjectLoader.initializePage({
    updateTitle: true,
    onLoad: (project) => {
        console.log('Załadowano projekt:', project.nazwa);
    }
});
```

### Używanie klas CSS

Użyj klas CSS do automatycznego podstawienia:

```html
<h1>Mapa Katastrophalna - <span class="project-name"></span></h1>
<p>Kontekst czasowy: <span class="project-context"></span></p>
<p>Region: <span class="project-region"></span></p>
```

Dostępne klasy:
- `.project-name` - nazwa projektu
- `.project-full-name` - pełna nazwa
- `.project-context` - kontekst czasowy
- `.project-year` - rok źródłowy
- `.project-period` - okres danych
- `.project-region` - region
- `.project-voivodeship` - województwo
- `.project-description` - opis

## 🗄️ Bazy Danych

System obsługuje dwa tryby:

### Tryb 1: Osobne Bazy (domyślne)

Każdy projekt ma własną bazę danych:
- `mapa_czarna_db` - baza master + dane Czarnej
- `borowa_db` - dane Borowej
- `inna_miejscowosc_db` - itd.

### Tryb 2: Schematy w Jednej Bazie

Wszystkie projekty w jednej bazie, osobne schematy:
- Schema `public` - baza master
- Schema `czarna` - dane Czarnej
- Schema `borowa` - dane Borowej

Wybór trybu: pole `use_separate_db` w tabeli `projects` (true/false)

## 🔧 Edycja Metadanych Projektu

### Przez Launcher

1. Wybierz projekt w dropdownie
2. Kliknij "⚙️ Edytuj"
3. Zmień pola w formularzu
4. Kliknij "💾 Zapisz"

### Przez API

```bash
curl -X PUT http://127.0.0.1:5000/api/projects/1 \
  -H "Content-Type: application/json" \
  -d '{
    "pelna_nazwa": "Gmina Czarna - Aktualizacja",
    "uwagi": "Dodatkowe informacje"
  }'
```

## ⚠️ Ważne Informacje

### Bezpieczeństwo

- Endpointy zarządzania projektami wymagają autoryzacji admina (jeśli `ADMIN_AUTH_ENABLED=1`)
- Dane między projektami są całkowicie izolowane
- Usunięcie projektu z tabeli `projects` NIE usuwa bazy danych

### Tryb Legacy

Jeśli tabela `projects` nie istnieje:
- System działa w trybie legacy (bez projektów)
- Połączenie zawsze idzie do bazy master (`DB_NAME` z .env)
- API `/api/project-info` zwraca domyślne dane dla Czarnej

### Migracja Danych

Obecne dane Czarnej:
- ✅ Pozostają w bazie `mapa_czarna_db`
- ✅ Są automatycznie używane dla projektu "Czarna"
- ✅ Nie wymagają przenoszenia/kopiowania

## 🧪 Testowanie

### Test API

```bash
# Lista projektów
curl http://127.0.0.1:5000/api/projects

# Aktywny projekt
curl http://127.0.0.1:5000/api/project-info

# Utwórz testowy projekt
curl -X POST http://127.0.0.1:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{"short_code": "test", "nazwa": "Test"}'
```

### Test Frontendu

1. Otwórz: http://127.0.0.1:5000/strona_glowna/index.html
2. Sprawdź konsolę przeglądarki: "✅ Załadowano metadane projektu"
3. Tytuł strony powinien zawierać nazwę projektu

## 📚 Dodatkowe Zasoby

- **Schema bazy**: `backend/migrations/001_create_projects_table.sql`
- **Manager projektów**: `backend/project_manager.py`
- **Frontend loader**: `assets/js/project-loader.js`
- **GUI selector**: `launcher/project_selector.py`

## 🐛 Rozwiązywanie Problemów

### Problem: "System projektów nie jest zainicjalizowany"

**Rozwiązanie**: Uruchom migrację:
```bash
python backend/migrations/migrate_to_multi_project.py
```

### Problem: Launcher nie pokazuje selektora projektów

**Rozwiązanie**:
1. Sprawdź czy `project_selector.py` istnieje w `launcher/`
2. Sprawdź logi konsoli launchera

### Problem: Frontend nie ładuje metadanych

**Rozwiązanie**:
1. Sprawdź czy `project-loader.js` jest dostępny pod `/assets/js/project-loader.js`
2. Sprawdź konsolę przeglądarki (F12)
3. Sprawdź czy endpoint `/api/project-info` działa

## 📞 Wsparcie

W razie problemów sprawdź:
1. Logi serwera Flask
2. Konsolę launchera
3. Konsolę przeglądarki (F12)
