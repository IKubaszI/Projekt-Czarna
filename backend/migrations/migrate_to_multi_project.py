#!/usr/bin/env python3
"""
================================================================================
Script Migracyjny: Migracja do systemu multi-projektowego
================================================================================
Ten skrypt migruje istniejący system Czarnej do nowej architektury
obsługującej wiele projektów.

Wykonuje:
1. Utworzenie tabeli 'projects' w bazie master
2. Dodanie Czarnej jako pierwszego projektu
3. Oznaczenie Czarnej jako aktywnego projektu
================================================================================
"""

import sys
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe
load_dotenv()

def get_db_config():
    """Pobiera konfigurację bazy danych z .env"""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "dbname": os.getenv("DB_NAME", "mapa_czarna_db"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "1234"),
        "port": os.getenv("DB_PORT", "5432")
    }

def run_sql_file(conn, sql_file_path):
    """Wykonuje plik SQL."""
    print(f"📂 Wykonywanie: {sql_file_path}")

    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    with conn.cursor() as cur:
        cur.execute(sql)

    conn.commit()
    print("✅ Plik SQL wykonany pomyślnie")

def check_table_exists(conn, table_name):
    """Sprawdza czy tabela istnieje."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %s
            );
        """, (table_name,))
        return cur.fetchone()[0]

def migrate():
    """Główna funkcja migracji."""
    print("=" * 80)
    print("MIGRACJA DO SYSTEMU MULTI-PROJEKTOWEGO")
    print("=" * 80)
    print()

    # Połączenie z bazą
    db_config = get_db_config()
    print(f"🔗 Łączenie z bazą danych: {db_config['dbname']} @ {db_config['host']}")

    try:
        conn = psycopg2.connect(**db_config)
        conn.set_client_encoding('UTF8')
        print("✅ Połączono z bazą danych")
        print()
    except Exception as e:
        print(f"❌ BŁĄD: Nie można połączyć się z bazą danych: {e}")
        return False

    try:
        # Krok 1: Sprawdź czy tabela projects już istnieje
        print("🔍 Sprawdzanie czy tabela 'projects' istnieje...")
        if check_table_exists(conn, 'projects'):
            print("⚠️  Tabela 'projects' już istnieje!")
            response = input("   Czy chcesz kontynuować? (t/n): ")
            if response.lower() != 't':
                print("❌ Migracja anulowana")
                return False
        else:
            print("✓ Tabela 'projects' nie istnieje - można utworzyć")
        print()

        # Krok 2: Wykonaj skrypt tworzący tabelę projects
        print("📊 KROK 1: Tworzenie struktury tabel...")
        sql_file = os.path.join(
            os.path.dirname(__file__),
            '001_create_projects_table.sql'
        )

        if not os.path.exists(sql_file):
            print(f"❌ BŁĄD: Nie znaleziono pliku: {sql_file}")
            return False

        run_sql_file(conn, sql_file)
        print()

        # Krok 3: Dodaj Czarną jako pierwszy projekt
        print("📍 KROK 2: Dodawanie projektu 'Czarna'...")

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Sprawdź czy Czarna już istnieje
            cur.execute("SELECT id FROM projects WHERE short_code = 'czarna';")
            existing = cur.fetchone()

            if existing:
                print("⚠️  Projekt 'Czarna' już istnieje w bazie")
                project_id = existing['id']
            else:
                # Dodaj Czarną
                cur.execute("""
                    INSERT INTO projects (
                        short_code, nazwa, pelna_nazwa, opis,
                        kontekst_czasowy, rok_zrodlowy, okres_danych,
                        region, wojewodztwo, jezyk_zrodel,
                        status, db_name, use_separate_db, is_active
                    ) VALUES (
                        'czarna',
                        'Czarna',
                        'Gmina Czarna',
                        'System mapy katastralnej dla miejscowości Czarna z protokołami właścicieli i danymi genealogicznymi',
                        'XIX wiek',
                        1880,
                        '1850-1900',
                        'Powiat Mielecki',
                        'Podkarpackie',
                        'Polski',
                        'aktywny',
                        'mapa_czarna_db',
                        true,
                        true
                    )
                    RETURNING id;
                """)

                project_id = cur.fetchone()['id']
                conn.commit()
                print(f"✅ Dodano projekt 'Czarna' (ID: {project_id})")
        print()

        # Krok 4: Ustaw Czarną jako aktywny projekt
        print("🎯 KROK 3: Ustawianie 'Czarna' jako aktywny projekt...")
        with conn.cursor() as cur:
            # Dezaktywuj wszystkie
            cur.execute("UPDATE projects SET is_active = false;")

            # Aktywuj Czarną
            cur.execute("UPDATE projects SET is_active = true WHERE short_code = 'czarna';")
            conn.commit()
        print("✅ Czarna ustawiona jako aktywny projekt")
        print()

        # Podsumowanie
        print("=" * 80)
        print("✅ MIGRACJA ZAKOŃCZONA POMYŚLNIE")
        print("=" * 80)
        print()
        print("📋 Podsumowanie:")
        print(f"   • Utworzono strukturę tabel dla systemu projektów")
        print(f"   • Dodano projekt 'Czarna' (ID: {project_id})")
        print(f"   • Czarna ustawiona jako aktywny projekt")
        print()
        print("💡 Następne kroki:")
        print("   1. Uruchom serwer Flask: python backend/app.py")
        print("   2. Sprawdź API: http://127.0.0.1:5000/api/project-info")
        print("   3. Sprawdź listę projektów: http://127.0.0.1:5000/api/projects")
        print()
        print("⚠️  UWAGA: Istniejące dane Czarnej pozostały w bazie 'mapa_czarna_db'")
        print("   System automatycznie używa tej bazy dla projektu Czarna.")
        print()

        return True

    except Exception as e:
        print(f"❌ BŁĄD podczas migracji: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print()
    success = migrate()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
