"""
================================================================================
Plik: project_manager.py
System Zarządzania Projektami - Multi-instancja
================================================================================
Moduł zarządzający wieloma projektami/instancjami miejscowości.
Obsługuje dynamiczne przełączanie połączeń do różnych baz danych.
================================================================================
"""

import os
import psycopg2
import psycopg2.extras
from typing import Dict, Optional, List
from datetime import datetime
import json

class ProjectManager:
    """Menedżer zarządzający projektami i dynamicznym przełączaniem baz danych."""

    def __init__(self, master_db_config: Dict[str, str]):
        """
        Inicjalizacja managera projektów.

        Args:
            master_db_config: Konfiguracja połączenia z bazą master (zarządzającą)
        """
        self.master_db_config = master_db_config
        self.active_project_id = None
        self.active_project_config = None
        self.current_db_config = None

        # Cache projektów w pamięci
        self._projects_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minut

        # Załaduj aktywny projekt przy inicjalizacji
        self._load_active_project()

    def get_master_connection(self):
        """Tworzy połączenie z bazą master."""
        conn = psycopg2.connect(**self.master_db_config)
        conn.set_client_encoding('UTF8')
        return conn

    def get_project_connection(self, project_id: Optional[int] = None):
        """
        Tworzy połączenie z bazą danych konkretnego projektu.

        Args:
            project_id: ID projektu (jeśli None, użyje aktywnego projektu)

        Returns:
            Połączenie psycopg2 do bazy projektu
        """
        if project_id is None:
            project_id = self.active_project_id

        if project_id is None:
            raise ValueError("Brak aktywnego projektu. Użyj switch_project() aby wybrać projekt.")

        # Pobierz konfigurację projektu
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Projekt o ID {project_id} nie istnieje.")

        # Zbuduj konfigurację połączenia
        db_config = self.master_db_config.copy()

        if project['use_separate_db']:
            # Osobna baza danych
            db_config['dbname'] = project['db_name']
        else:
            # Ten sam dbname, ale inny schemat
            db_config['dbname'] = self.master_db_config['dbname']

        conn = psycopg2.connect(**db_config)
        conn.set_client_encoding('UTF8')

        # Jeśli używamy schematów, ustaw search_path
        if not project['use_separate_db']:
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {project['db_schema']}, public;")
            conn.commit()

        return conn

    def _load_active_project(self):
        """Wczytuje informację o aktywnym projekcie z bazy master."""
        try:
            conn = self.get_master_connection()
            try:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Sprawdź czy tabele istnieją
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = 'projects'
                        );
                    """)
                    if not cur.fetchone()['exists']:
                        print("⚠️ Tabela 'projects' nie istnieje. System projektów nie został zainicjowany.")
                        return

                    # Pobierz aktywny projekt
                    cur.execute("""
                        SELECT * FROM projects
                        WHERE is_active = true
                        LIMIT 1;
                    """)
                    active_project = cur.fetchone()

                    if active_project:
                        self.active_project_id = active_project['id']
                        self.active_project_config = dict(active_project)
                        print(f"✅ Aktywny projekt: {active_project['nazwa']} (ID: {active_project['id']})")
                    else:
                        print("⚠️ Brak aktywnego projektu. Użyj switch_project() aby wybrać projekt.")
            finally:
                conn.close()
        except Exception as e:
            print(f"❌ Błąd przy ładowaniu aktywnego projektu: {e}")

    def get_all_projects(self, force_refresh: bool = False) -> List[Dict]:
        """
        Pobiera listę wszystkich projektów.

        Args:
            force_refresh: Czy wymusić odświeżenie cache

        Returns:
            Lista słowników z danymi projektów
        """
        # Sprawdź cache
        if not force_refresh and self._projects_cache and self._cache_timestamp:
            elapsed = datetime.now().timestamp() - self._cache_timestamp
            if elapsed < self._cache_ttl:
                return list(self._projects_cache.values())

        # Pobierz z bazy
        conn = self.get_master_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM projects
                    ORDER BY status ASC, nazwa ASC;
                """)
                projects = [dict(row) for row in cur.fetchall()]

                # Zapisz do cache
                self._projects_cache = {p['id']: p for p in projects}
                self._cache_timestamp = datetime.now().timestamp()

                return projects
        finally:
            conn.close()

    def get_project(self, project_id: int) -> Optional[Dict]:
        """
        Pobiera dane konkretnego projektu.

        Args:
            project_id: ID projektu

        Returns:
            Słownik z danymi projektu lub None
        """
        # Sprawdź cache
        if project_id in self._projects_cache:
            return self._projects_cache[project_id]

        conn = self.get_master_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM projects WHERE id = %s;", (project_id,))
                project = cur.fetchone()
                if project:
                    project = dict(project)
                    self._projects_cache[project_id] = project
                return project
        finally:
            conn.close()

    def get_project_by_code(self, short_code: str) -> Optional[Dict]:
        """
        Pobiera projekt po kodzie.

        Args:
            short_code: Krótki kod projektu (np. "czarna")

        Returns:
            Słownik z danymi projektu lub None
        """
        conn = self.get_master_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM projects WHERE short_code = %s;", (short_code,))
                project = cur.fetchone()
                return dict(project) if project else None
        finally:
            conn.close()

    def create_project(self, project_data: Dict) -> Dict:
        """
        Tworzy nowy projekt.

        Args:
            project_data: Słownik z danymi projektu

        Returns:
            Słownik z danymi utworzonego projektu
        """
        required_fields = ['short_code', 'nazwa']
        for field in required_fields:
            if field not in project_data:
                raise ValueError(f"Brak wymaganego pola: {field}")

        # Domyślne wartości
        defaults = {
            'db_name': f"{project_data['short_code']}_db",
            'db_schema': 'public',
            'use_separate_db': True,
            'status': 'aktywny',
            'is_active': False
        }

        # Połącz z domyślnymi
        full_data = {**defaults, **project_data}

        conn = self.get_master_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                columns = ', '.join(full_data.keys())
                placeholders = ', '.join(['%s'] * len(full_data))

                cur.execute(f"""
                    INSERT INTO projects ({columns})
                    VALUES ({placeholders})
                    RETURNING *;
                """, list(full_data.values()))

                new_project = dict(cur.fetchone())
                conn.commit()

                # Wyczyść cache
                self._projects_cache = {}

                print(f"✅ Utworzono projekt: {new_project['nazwa']} (ID: {new_project['id']})")
                return new_project
        except psycopg2.IntegrityError as e:
            conn.rollback()
            raise ValueError(f"Projekt o kodzie '{project_data['short_code']}' już istnieje.")
        finally:
            conn.close()

    def update_project(self, project_id: int, project_data: Dict) -> Dict:
        """
        Aktualizuje dane projektu.

        Args:
            project_id: ID projektu
            project_data: Słownik z danymi do aktualizacji

        Returns:
            Zaktualizowany projekt
        """
        # Pola które można aktualizować
        allowed_fields = [
            'nazwa', 'pelna_nazwa', 'opis', 'kontekst_czasowy',
            'rok_zrodlowy', 'okres_danych', 'region', 'wojewodztwo',
            'jezyk_zrodel', 'uwagi', 'status'
        ]

        # Filtruj tylko dozwolone pola
        update_data = {k: v for k, v in project_data.items() if k in allowed_fields}

        if not update_data:
            raise ValueError("Brak danych do aktualizacji")

        conn = self.get_master_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                set_clause = ', '.join([f"{k} = %s" for k in update_data.keys()])
                values = list(update_data.values()) + [project_id]

                cur.execute(f"""
                    UPDATE projects
                    SET {set_clause}
                    WHERE id = %s
                    RETURNING *;
                """, values)

                updated_project = cur.fetchone()
                if not updated_project:
                    raise ValueError(f"Projekt o ID {project_id} nie istnieje.")

                conn.commit()

                # Wyczyść cache
                self._projects_cache = {}

                updated_project = dict(updated_project)
                print(f"✅ Zaktualizowano projekt: {updated_project['nazwa']}")

                return updated_project
        finally:
            conn.close()

    def delete_project(self, project_id: int) -> bool:
        """
        Usuwa projekt (tylko metadane, nie usuwa bazy danych).

        Args:
            project_id: ID projektu

        Returns:
            True jeśli usunięto
        """
        if project_id == self.active_project_id:
            raise ValueError("Nie można usunąć aktywnego projektu. Przełącz się najpierw na inny.")

        conn = self.get_master_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM projects WHERE id = %s RETURNING id;", (project_id,))
                deleted = cur.fetchone()
                conn.commit()

                if deleted:
                    # Wyczyść cache
                    self._projects_cache = {}
                    print(f"✅ Usunięto projekt o ID: {project_id}")
                    return True
                return False
        finally:
            conn.close()

    def switch_project(self, project_id: int) -> Dict:
        """
        Przełącza aktywny projekt.

        Args:
            project_id: ID projektu do aktywacji

        Returns:
            Dane aktywowanego projektu
        """
        conn = self.get_master_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Sprawdź czy projekt istnieje
                cur.execute("SELECT * FROM projects WHERE id = %s;", (project_id,))
                project = cur.fetchone()
                if not project:
                    raise ValueError(f"Projekt o ID {project_id} nie istnieje.")

                # Dezaktywuj wszystkie projekty
                cur.execute("UPDATE projects SET is_active = false;")

                # Aktywuj wybrany projekt
                cur.execute("""
                    UPDATE projects
                    SET is_active = true
                    WHERE id = %s
                    RETURNING *;
                """, (project_id,))

                active_project = dict(cur.fetchone())
                conn.commit()

                # Zaktualizuj stan managera
                self.active_project_id = active_project['id']
                self.active_project_config = active_project

                # Wyczyść cache
                self._projects_cache = {}

                print(f"✅ Przełączono na projekt: {active_project['nazwa']} (ID: {active_project['id']})")
                return active_project
        finally:
            conn.close()

    def get_active_project(self) -> Optional[Dict]:
        """
        Zwraca dane aktywnego projektu.

        Returns:
            Słownik z danymi aktywnego projektu lub None
        """
        if self.active_project_config:
            return self.active_project_config

        self._load_active_project()
        return self.active_project_config

    def ensure_project_database(self, project_id: int, template_sql_path: Optional[str] = None) -> bool:
        """
        Upewnia się że baza danych projektu istnieje i ma odpowiednią strukturę.

        Args:
            project_id: ID projektu
            template_sql_path: Ścieżka do pliku SQL z szablonem struktury tabel

        Returns:
            True jeśli baza jest gotowa
        """
        project = self.get_project(project_id)
        if not project:
            raise ValueError(f"Projekt o ID {project_id} nie istnieje.")

        if project['use_separate_db']:
            # Sprawdź czy baza istnieje, jeśli nie - utwórz
            conn = self.get_master_connection()
            conn.autocommit = True
            try:
                with conn.cursor() as cur:
                    # Sprawdź czy baza istnieje
                    cur.execute("""
                        SELECT 1 FROM pg_database
                        WHERE datname = %s;
                    """, (project['db_name'],))

                    if not cur.fetchone():
                        # Utwórz bazę
                        cur.execute(f"CREATE DATABASE {project['db_name']} ENCODING 'UTF8';")
                        print(f"✅ Utworzono bazę danych: {project['db_name']}")

                        # Załaduj strukturę jeśli podano szablon
                        if template_sql_path and os.path.exists(template_sql_path):
                            self._load_database_structure(project['db_name'], template_sql_path)
                    else:
                        print(f"✓ Baza danych już istnieje: {project['db_name']}")
            finally:
                conn.close()
        else:
            # Używamy schematów - sprawdź czy schemat istnieje
            conn = self.get_project_connection(project_id)
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT schema_name FROM information_schema.schemata
                        WHERE schema_name = %s;
                    """, (project['db_schema'],))

                    if not cur.fetchone():
                        cur.execute(f"CREATE SCHEMA {project['db_schema']};")
                        conn.commit()
                        print(f"✅ Utworzono schemat: {project['db_schema']}")

                        if template_sql_path and os.path.exists(template_sql_path):
                            self._load_database_structure(project['db_name'], template_sql_path, project['db_schema'])
                    else:
                        print(f"✓ Schemat już istnieje: {project['db_schema']}")
            finally:
                conn.close()

        return True

    def _load_database_structure(self, db_name: str, sql_file: str, schema: str = 'public'):
        """Wczytuje strukturę bazy z pliku SQL."""
        print(f"📂 Ładowanie struktury bazy z: {sql_file}")
        # TODO: Implementacja ładowania SQL
        # Można użyć psql lub psycopg2 do wykonania pliku SQL
        pass
