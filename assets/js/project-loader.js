/**
 * ================================================================================
 * Moduł: project-loader.js
 * System dynamicznego ładowania metadanych projektów
 * ================================================================================
 * Ten moduł ładuje metadane aktywnego projektu z API i udostępnia je dla stron.
 */

// Singleton cache dla metadanych projektu
const ProjectLoader = (function() {
    let projectData = null;
    let isLoading = false;
    let loadPromise = null;

    /**
     * Pobiera metadane aktywnego projektu z API
     * @returns {Promise<Object>} Dane projektu
     */
    async function loadProjectInfo() {
        // USUNIĘTO CACHE - zawsze pobieraj świeże dane
        // if (projectData) {
        //     return projectData;
        // }

        if (isLoading) {
            return loadPromise;
        }

        isLoading = true;
        // Dodaj timestamp do URL aby wyłączyć cache
        const cacheBuster = `?_=${new Date().getTime()}`;
        loadPromise = fetch(`/api/project-info${cacheBuster}`, {
                cache: 'no-store',  // Wyłącz cache przeglądarki
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'success' && data.project) {
                    projectData = data.project;
                    console.log('✅ Załadowano metadane projektu:', projectData.nazwa);
                    return projectData;
                } else {
                    throw new Error('Nieprawidłowa odpowiedź API');
                }
            })
            .catch(error => {
                console.error('❌ Błąd ładowania metadanych projektu:', error);
                // Fallback do domyślnych danych (Czarna)
                projectData = {
                    nazwa: 'Czarna',
                    pelna_nazwa: 'Gmina Czarna',
                    kontekst_czasowy: 'XIX wiek',
                    rok_zrodlowy: 1880,
                    okres_danych: '1850-1900',
                    region: 'Powiat Mielecki',
                    wojewodztwo: 'Podkarpackie',
                    opis: 'System mapy katastralnej dla miejscowości Czarna'
                };
                console.warn('⚠️ Użyto domyślnych danych projektu');
                return projectData;
            })
            .finally(() => {
                isLoading = false;
            });

        return loadPromise;
    }

    /**
     * Pobiera aktualnie załadowane metadane (synchronicznie)
     * @returns {Object|null} Dane projektu lub null jeśli nie załadowano
     */
    function getCurrentProject() {
        return projectData;
    }

    /**
     * Wymusza ponowne załadowanie metadanych
     * @returns {Promise<Object>} Nowe dane projektu
     */
    function reloadProject() {
        projectData = null;
        isLoading = false;
        loadPromise = null;
        return loadProjectInfo();
    }

    /**
     * Podstawia metadane projektu do elementów HTML
     * @param {Object} project - Dane projektu
     * @param {Object} selectors - Mapa selektorów do pól projektu
     */
    function updatePageElements(project, selectors = {}) {
        const defaultSelectors = {
            '.project-name': 'nazwa',
            '.project-full-name': 'pelna_nazwa',
            '.project-context': 'kontekst_czasowy',
            '.project-year': 'rok_zrodlowy',
            '.project-period': 'okres_danych',
            '.project-region': 'region',
            '.project-voivodeship': 'wojewodztwo',
            '.project-description': 'opis'
        };

        const allSelectors = {...defaultSelectors, ...selectors};

        for (const [selector, field] of Object.entries(allSelectors)) {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                const value = project[field];
                if (value !== null && value !== undefined) {
                    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                        el.value = value;
                    } else {
                        el.textContent = value;
                    }
                }
            });
        }
    }

    /**
     * Zastępuje placeholdery w tytule strony
     * @param {Object} project - Dane projektu
     */
    function updatePageTitle(project) {
        const currentTitle = document.title;

        // Zastąp znane placeholdery
        let newTitle = currentTitle
            .replace(/Czarna/g, project.nazwa || 'Czarna')
            .replace(/XIX wiek/g, project.kontekst_czasowy || 'XIX wiek')
            .replace(/Gmina Czarna/g, project.pelna_nazwa || project.nazwa || 'Czarna');

        // Jeśli tytuł się zmienił, zaktualizuj
        if (newTitle !== currentTitle) {
            document.title = newTitle;
        }
    }

    /**
     * Inicjalizuje stronę z metadanymi projektu
     * @param {Object} options - Opcje inicjalizacji
     * @param {Object} options.selectors - Niestandardowe selektory
     * @param {boolean} options.updateTitle - Czy aktualizować tytuł (domyślnie true)
     * @param {Function} options.onLoad - Callback po załadowaniu
     * @returns {Promise<Object>} Dane projektu
     */
    async function initializePage(options = {}) {
        const {
            selectors = {},
            updateTitle = true,
            onLoad = null
        } = options;

        try {
            const project = await loadProjectInfo();

            // Aktualizuj elementy strony
            updatePageElements(project, selectors);

            // Aktualizuj tytuł
            if (updateTitle) {
                updatePageTitle(project);
            }

            // Wywołaj callback jeśli podano
            if (onLoad && typeof onLoad === 'function') {
                onLoad(project);
            }

            return project;
        } catch (error) {
            console.error('❌ Błąd inicjalizacji strony:', error);
            throw error;
        }
    }

    /**
     * Tworzy tekst opisowy z metadanych projektu
     * @param {Object} project - Dane projektu
     * @returns {string} Opis projektu
     */
    function createProjectDescription(project) {
        const parts = [];

        if (project.pelna_nazwa) {
            parts.push(project.pelna_nazwa);
        }

        if (project.kontekst_czasowy) {
            parts.push(project.kontekst_czasowy);
        }

        if (project.okres_danych) {
            parts.push(`dane z lat ${project.okres_danych}`);
        }

        if (project.region) {
            parts.push(project.region);
        }

        if (project.wojewodztwo) {
            parts.push(`woj. ${project.wojewodztwo}`);
        }

        return parts.join(' • ');
    }

    // Publiczne API
    return {
        load: loadProjectInfo,
        getCurrent: getCurrentProject,
        reload: reloadProject,
        initializePage: initializePage,
        updateElements: updatePageElements,
        updateTitle: updatePageTitle,
        createDescription: createProjectDescription
    };
})();

// Auto-inicjalizacja jeśli strona ma atrybut data-auto-init
document.addEventListener('DOMContentLoaded', () => {
    const html = document.documentElement;
    if (html.hasAttribute('data-project-auto-init')) {
        ProjectLoader.initializePage()
            .then(project => {
                console.log('✅ Strona zainicjalizowana z projektem:', project.nazwa);
            })
            .catch(error => {
                console.error('❌ Błąd auto-inicjalizacji:', error);
            });
    }
});

// Eksportuj do globalnego scope
window.ProjectLoader = ProjectLoader;
