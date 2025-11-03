"""
================================================================================
Plik: project_selector.py
Moduł GUI do zarządzania projektami w launcherze
================================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Dodaj ścieżkę do backendu
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

try:
    from project_manager import ProjectManager
except ImportError:
    ProjectManager = None


class ProjectSelectorFrame(ttk.Frame):
    """Widget do wyboru i zarządzania projektami."""

    def __init__(self, parent, db_config, on_project_change=None):
        """
        Args:
            parent: Rodzic widgetu
            db_config: Konfiguracja połączenia z bazą danych
            on_project_change: Callback wywoływany przy zmianie projektu
        """
        super().__init__(parent)
        self.db_config = db_config
        self.on_project_change = on_project_change
        self.project_manager = None

        # Inicjalizuj manager
        self._init_project_manager()

        # Utwórz interfejs
        self._create_widgets()

        # Załaduj projekty
        self.refresh_projects()

    def _init_project_manager(self):
        """Inicjalizuje menedżera projektów."""
        if ProjectManager is None:
            print("⚠️ Moduł ProjectManager niedostępny")
            return

        try:
            self.project_manager = ProjectManager(self.db_config)
        except Exception as e:
            print(f"⚠️ Nie można zainicjalizować ProjectManager: {e}")
            self.project_manager = None

    def _create_widgets(self):
        """Tworzy widgety interfejsu."""
        # Główny kontener
        container = ttk.Frame(self)
        container.pack(fill=tk.X, padx=5, pady=5)

        # Sprawdź czy system projektów jest dostępny
        if not self.project_manager:
            self._create_initialization_widget(container)
            return

        # Label
        label = ttk.Label(container, text="📁 Projekt:", font=('Arial', 10, 'bold'))
        label.pack(side=tk.LEFT, padx=(0, 5))

        # Dropdown projektów
        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(
            container,
            textvariable=self.project_var,
            state='readonly',
            width=30
        )
        self.project_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.project_combo.bind('<<ComboboxSelected>>', self._on_project_selected)

        # Przycisk odświeżania
        refresh_btn = ttk.Button(
            container,
            text="🔄",
            width=3,
            command=self.refresh_projects
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Przycisk nowego projektu
        new_btn = ttk.Button(
            container,
            text="➕ Nowy",
            command=self._open_new_project_dialog
        )
        new_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Przycisk edycji
        edit_btn = ttk.Button(
            container,
            text="⚙️ Edytuj",
            command=self._open_edit_project_dialog
        )
        edit_btn.pack(side=tk.LEFT)

    def _create_initialization_widget(self, container):
        """Tworzy widget informujący o braku systemu projektów."""
        # Ikona i komunikat
        info_frame = ttk.Frame(container)
        info_frame.pack(fill=tk.X)

        label = ttk.Label(
            info_frame,
            text="⚠️ System projektów nie jest zainicjalizowany",
            font=('Arial', 10, 'bold'),
            foreground='orange'
        )
        label.pack(side=tk.LEFT, padx=(0, 10))

        # Przycisk inicjalizacji
        init_btn = ttk.Button(
            info_frame,
            text="🔧 Uruchom Migrację",
            command=self._run_migration
        )
        init_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Przycisk pomocy
        help_btn = ttk.Button(
            info_frame,
            text="❓ Pomoc",
            command=self._show_help
        )
        help_btn.pack(side=tk.LEFT)

    def _run_migration(self):
        """Uruchamia script migracyjny."""
        response = messagebox.askyesno(
            "Inicjalizacja systemu projektów",
            "Czy chcesz uruchomić migrację do systemu multi-projektowego?\n\n"
            "To utworzy:\n"
            "• Tabelę 'projects' w bazie danych\n"
            "• Dodanie 'Czarna' jako pierwszy projekt\n"
            "• Ustawienie Czarnej jako aktywny projekt\n\n"
            "Istniejące dane pozostaną nietknięte."
        )

        if not response:
            return

        import subprocess
        import os

        # Znajdź ścieżkę do scriptu migracyjnego
        backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
        migration_script = os.path.join(backend_dir, 'migrations', 'migrate_to_multi_project.py')

        if not os.path.exists(migration_script):
            messagebox.showerror(
                "Błąd",
                f"Nie znaleziono scriptu migracyjnego:\n{migration_script}"
            )
            return

        try:
            # Uruchom migrację
            result = subprocess.run(
                ['python', migration_script],
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                messagebox.showinfo(
                    "Sukces",
                    "Migracja zakończona pomyślnie!\n\n"
                    "System projektów jest teraz aktywny.\n"
                    "Uruchom ponownie launcher aby zobaczyć zmiany."
                )
            else:
                messagebox.showerror(
                    "Błąd migracji",
                    f"Migracja zakończyła się błędem:\n\n{result.stderr}"
                )
        except subprocess.TimeoutExpired:
            messagebox.showerror("Błąd", "Migracja przekroczyła limit czasu (30s)")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można uruchomić migracji:\n{e}")

    def _show_help(self):
        """Pokazuje okno pomocy."""
        help_text = """
System Multi-Projektowy - Pomoc

System projektów pozwala zarządzać wieloma instancjami
miejscowości (Czarna, Borowa, etc.) w jednej aplikacji.

Aby zainicjalizować system:

1. Kliknij "🔧 Uruchom Migrację"
2. Potwierdź uruchomienie migracji
3. Poczekaj na zakończenie
4. Uruchom ponownie launcher

Alternatywnie możesz uruchomić ręcznie:
cd backend
python migrations/migrate_to_multi_project.py

Więcej informacji w pliku MULTI_PROJECT_SETUP.md
"""
        messagebox.showinfo("Pomoc - System Projektów", help_text.strip())

    def refresh_projects(self):
        """Odświeża listę projektów."""
        if not self.project_manager:
            return

        try:
            projects = self.project_manager.get_all_projects(force_refresh=True)

            # Przygotuj listę do wyświetlenia
            project_names = []
            self.projects_map = {}  # Mapowanie nazwy -> projekt

            for proj in projects:
                display_name = f"{proj['nazwa']}"
                if proj['status'] == 'archiwum':
                    display_name += " (archiwum)"

                project_names.append(display_name)
                self.projects_map[display_name] = proj

            # Zaktualizuj combobox
            self.project_combo['values'] = project_names

            # Zaznacz aktywny projekt
            active_project = self.project_manager.get_active_project()
            if active_project:
                for name, proj in self.projects_map.items():
                    if proj['id'] == active_project['id']:
                        self.project_var.set(name)
                        break
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można załadować projektów:\n{e}")

    def _on_project_selected(self, event=None):
        """Obsługuje wybór projektu z dropdowna."""
        selected_name = self.project_var.get()
        if not selected_name or selected_name not in self.projects_map:
            return

        selected_project = self.projects_map[selected_name]

        # Sprawdź czy to inny projekt niż aktywny
        active = self.project_manager.get_active_project()
        if active and active['id'] == selected_project['id']:
            return  # Ten sam projekt - nic nie rób

        # Potwierdź zmianę
        response = messagebox.askyesno(
            "Przełączenie projektu",
            f"Czy chcesz przełączyć się na projekt:\n\n"
            f"{selected_project['nazwa']}\n\n"
            f"Wymaga to ponownego uruchomienia serwera."
        )

        if response:
            try:
                self.project_manager.switch_project(selected_project['id'])
                messagebox.showinfo(
                    "Sukces",
                    f"Przełączono na projekt: {selected_project['nazwa']}\n\n"
                    f"Uruchom ponownie serwer, aby zmiany zostały zastosowane."
                )

                # Wywołaj callback
                if self.on_project_change:
                    self.on_project_change(selected_project)

            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można przełączyć projektu:\n{e}")
                self.refresh_projects()  # Przywróć poprzedni wybór
        else:
            self.refresh_projects()  # Przywróć poprzedni wybór

    def _open_new_project_dialog(self):
        """Otwiera okno dialogowe tworzenia nowego projektu."""
        dialog = ProjectEditorDialog(
            self,
            self.project_manager,
            title="Nowy Projekt",
            on_save=self.refresh_projects
        )

    def _open_edit_project_dialog(self):
        """Otwiera okno dialogowe edycji projektu."""
        selected_name = self.project_var.get()
        if not selected_name or selected_name not in self.projects_map:
            messagebox.showwarning("Brak wyboru", "Wybierz projekt do edycji")
            return

        project = self.projects_map[selected_name]
        dialog = ProjectEditorDialog(
            self,
            self.project_manager,
            title="Edytuj Projekt",
            project_data=project,
            on_save=self.refresh_projects
        )


class ProjectEditorDialog(tk.Toplevel):
    """Okno dialogowe do tworzenia/edycji projektu."""

    def __init__(self, parent, project_manager, title="Projekt", project_data=None, on_save=None):
        """
        Args:
            parent: Okno rodzic
            project_manager: Instancja ProjectManager
            title: Tytuł okna
            project_data: Dane projektu (None dla nowego projektu)
            on_save: Callback po zapisaniu
        """
        super().__init__(parent)
        self.project_manager = project_manager
        self.project_data = project_data
        self.on_save = on_save
        self.is_new = project_data is None

        self.title(title)
        self.geometry("600x700")
        self.resizable(False, False)

        # Wyśrodkuj okno
        self.transient(parent)
        self.grab_set()

        self._create_widgets()

        # Załaduj dane jeśli edycja
        if not self.is_new:
            self._load_project_data()

    def _create_widgets(self):
        """Tworzy widgety formularza."""
        # Główny kontener z scrollem
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Pola formularza
        self.fields = {}

        # Sekcja: Podstawowe
        self._add_section(scrollable_frame, "Podstawowe")
        self.fields['short_code'] = self._add_field(scrollable_frame, "Kod projektu*", "np. czarna")
        self.fields['nazwa'] = self._add_field(scrollable_frame, "Nazwa krótka*", "np. Czarna")
        self.fields['pelna_nazwa'] = self._add_field(scrollable_frame, "Pełna nazwa", "np. Gmina Czarna")
        self.fields['opis'] = self._add_text_field(scrollable_frame, "Opis", height=3)

        # Sekcja: Kontekst czasowy
        self._add_section(scrollable_frame, "Kontekst czasowy")
        self.fields['kontekst_czasowy'] = self._add_field(scrollable_frame, "Wiek/Epoka", "np. XIX wiek")
        self.fields['rok_zrodlowy'] = self._add_field(scrollable_frame, "Rok źródłowy", "np. 1880")
        self.fields['okres_danych'] = self._add_field(scrollable_frame, "Okres danych", "np. 1850-1900")

        # Sekcja: Geograficzne
        self._add_section(scrollable_frame, "Geograficzne")
        self.fields['region'] = self._add_field(scrollable_frame, "Region", "np. Powiat Mielecki")
        self.fields['wojewodztwo'] = self._add_field(scrollable_frame, "Województwo", "np. Podkarpackie")

        # Sekcja: Dodatkowe
        self._add_section(scrollable_frame, "Dodatkowe")
        self.fields['jezyk_zrodel'] = self._add_field(scrollable_frame, "Język źródeł", "np. Polski")
        self.fields['uwagi'] = self._add_text_field(scrollable_frame, "Uwagi", height=3)

        # Status (tylko dla edycji)
        if not self.is_new:
            self._add_section(scrollable_frame, "Status")
            self.fields['status'] = self._add_combo_field(
                scrollable_frame,
                "Status",
                values=['aktywny', 'archiwum']
            )

        # Przyciski
        btn_frame = ttk.Frame(scrollable_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=20)

        ttk.Button(
            btn_frame,
            text="💾 Zapisz",
            command=self._save_project
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="❌ Anuluj",
            command=self.destroy
        ).pack(side=tk.LEFT, padx=5)

        if not self.is_new:
            ttk.Button(
                btn_frame,
                text="🗑️ Usuń projekt",
                command=self._delete_project
            ).pack(side=tk.RIGHT, padx=5)

    def _add_section(self, parent, title):
        """Dodaje nagłówek sekcji."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=(15, 5))
        label = ttk.Label(frame, text=title, font=('Arial', 10, 'bold'))
        label.pack(anchor='w')
        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=5)

    def _add_field(self, parent, label_text, placeholder=""):
        """Dodaje pole tekstowe."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=5)

        label = ttk.Label(frame, text=label_text, width=20, anchor='w')
        label.pack(side=tk.LEFT)

        entry = ttk.Entry(frame)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Nie wstawiaj placeholderów jako wartości domyślnych
        # entry.insert(0, placeholder)

        return entry

    def _add_text_field(self, parent, label_text, height=3):
        """Dodaje pole tekstowe wieloliniowe."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=5)

        label = ttk.Label(frame, text=label_text, width=20, anchor='nw')
        label.pack(side=tk.LEFT, anchor='n')

        text = tk.Text(frame, height=height, width=40)
        text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        return text

    def _add_combo_field(self, parent, label_text, values):
        """Dodaje pole wyboru."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, padx=10, pady=5)

        label = ttk.Label(frame, text=label_text, width=20, anchor='w')
        label.pack(side=tk.LEFT)

        combo = ttk.Combobox(frame, values=values, state='readonly')
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        return combo

    def _load_project_data(self):
        """Ładuje dane projektu do formularza."""
        if not self.project_data:
            return

        for field_name, widget in self.fields.items():
            value = self.project_data.get(field_name, '')
            if value is None:
                value = ''

            if isinstance(widget, tk.Text):
                widget.delete('1.0', tk.END)
                widget.insert('1.0', str(value))
            elif isinstance(widget, ttk.Combobox):
                widget.set(str(value))
            else:
                widget.delete(0, tk.END)
                widget.insert(0, str(value))

        # Zablokuj kod projektu przy edycji
        if not self.is_new and 'short_code' in self.fields:
            self.fields['short_code'].config(state='disabled')

    def _get_form_data(self):
        """Pobiera dane z formularza."""
        data = {}

        for field_name, widget in self.fields.items():
            if isinstance(widget, tk.Text):
                value = widget.get('1.0', tk.END).strip()
            elif isinstance(widget, ttk.Combobox):
                value = widget.get()
            else:
                value = widget.get().strip()

            # Konwersja typów
            if field_name == 'rok_zrodlowy' and value:
                try:
                    value = int(value)
                except ValueError:
                    pass

            data[field_name] = value if value else None

        return data

    def _save_project(self):
        """Zapisuje projekt."""
        data = self._get_form_data()

        # Walidacja
        if self.is_new:
            if not data.get('short_code'):
                messagebox.showerror("Błąd", "Kod projektu jest wymagany")
                return
            if not data.get('nazwa'):
                messagebox.showerror("Błąd", "Nazwa projektu jest wymagana")
                return

        try:
            if self.is_new:
                # Nowy projekt
                self.project_manager.create_project(data)
                messagebox.showinfo("Sukces", "Projekt został utworzony pomyślnie")
            else:
                # Aktualizacja
                self.project_manager.update_project(self.project_data['id'], data)
                messagebox.showinfo("Sukces", "Projekt został zaktualizowany")

            # Callback
            if self.on_save:
                self.on_save()

            self.destroy()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zapisać projektu:\n{e}")

    def _delete_project(self):
        """Usuwa projekt."""
        if self.is_new:
            return

        response = messagebox.askyesnocancel(
            "Usunięcie projektu",
            f"Czy na pewno chcesz usunąć projekt:\n\n"
            f"{self.project_data['nazwa']}?\n\n"
            f"UWAGA: To usunie tylko metadane.\n"
            f"Baza danych projektu pozostanie nietknięta."
        )

        if not response:
            return

        try:
            self.project_manager.delete_project(self.project_data['id'])
            messagebox.showinfo("Sukces", "Projekt został usunięty")

            # Callback
            if self.on_save:
                self.on_save()

            self.destroy()

        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można usunąć projektu:\n{e}")
