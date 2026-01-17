/**
 * Autosave questionnaire dans localStorage
 * Sauvegarde automatique toutes les 30 secondes
 */

(function() {
    'use strict';

    const AUTOSAVE_INTERVAL = 30000; // 30 secondes
    let autosaveTimer = null;
    let formId = null;

    /**
     * Initialiser l'autosave pour un formulaire
     */
    function initAutosave(formElement) {
        if (!formElement) return;

        formId = formElement.id || 'questionnaire-form';
        const storageKey = `autosave_${formId}_${window.location.pathname}`;

        // Charger les données sauvegardées au chargement
        loadAutosavedData(formElement, storageKey);

        // Afficher un indicateur si des données ont été restaurées
        const savedData = localStorage.getItem(storageKey);
        if (savedData) {
            showAutosaveNotification('Données restaurées depuis la dernière sauvegarde automatique.');
        }

        // Sauvegarder toutes les 30 secondes
        autosaveTimer = setInterval(() => {
            saveFormData(formElement, storageKey);
        }, AUTOSAVE_INTERVAL);

        // Sauvegarder avant de quitter la page
        window.addEventListener('beforeunload', () => {
            saveFormData(formElement, storageKey);
        });

        // Nettoyer la sauvegarde lors de la soumission du formulaire
        formElement.addEventListener('submit', () => {
            localStorage.removeItem(storageKey);
            if (autosaveTimer) {
                clearInterval(autosaveTimer);
            }
        });

        // Ajouter un bouton pour vider la sauvegarde
        addClearAutosaveButton(formElement, storageKey);
    }

    /**
     * Sauvegarder les données du formulaire
     */
    function saveFormData(form, storageKey) {
        const formData = new FormData(form);
        const data = {};

        // Collecter toutes les données du formulaire (sauf le token CSRF)
        for (let [key, value] of formData.entries()) {
            // Ne pas sauvegarder le token CSRF
            if (key === 'csrfmiddlewaretoken') continue;

            if (data[key]) {
                // Si la clé existe déjà, c'est un champ multiple (checkbox)
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }

        // Sauvegarder dans localStorage
        try {
            localStorage.setItem(storageKey, JSON.stringify({
                data: data,
                timestamp: new Date().toISOString()
            }));
            showAutosaveIndicator();
        } catch (e) {
            console.error('Erreur lors de la sauvegarde automatique:', e);
        }
    }

    /**
     * Charger les données sauvegardées
     */
    function loadAutosavedData(form, storageKey) {
        try {
            const saved = localStorage.getItem(storageKey);
            if (!saved) return;

            const { data, timestamp } = JSON.parse(saved);

            // Vérifier que la sauvegarde n'est pas trop ancienne (24h)
            const savedDate = new Date(timestamp);
            const now = new Date();
            const hoursDiff = (now - savedDate) / (1000 * 60 * 60);

            if (hoursDiff > 24) {
                localStorage.removeItem(storageKey);
                return;
            }

            // Restaurer les données dans le formulaire
            for (let [key, value] of Object.entries(data)) {
                const field = form.elements[key];
                if (!field) continue;

                if (field.type === 'radio') {
                    // Radio buttons
                    const radio = form.querySelector(`input[name="${key}"][value="${value}"]`);
                    if (radio) radio.checked = true;
                } else if (field.type === 'checkbox') {
                    // Checkboxes
                    if (Array.isArray(value)) {
                        value.forEach(v => {
                            const checkbox = form.querySelector(`input[name="${key}"][value="${v}"]`);
                            if (checkbox) checkbox.checked = true;
                        });
                    } else {
                        if (field.value === value || value === '1' || value === 'on') {
                            field.checked = true;
                        }
                    }
                } else {
                    // Champs texte, textarea, select
                    field.value = value;
                }
            }

        } catch (e) {
            console.error('Erreur lors du chargement de la sauvegarde:', e);
            localStorage.removeItem(storageKey);
        }
    }

    /**
     * Afficher un indicateur de sauvegarde
     */
    function showAutosaveIndicator() {
        let indicator = document.getElementById('autosave-indicator');

        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'autosave-indicator';
            indicator.style.cssText = `
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: var(--vert-moyen);
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
                z-index: 1000;
                opacity: 0;
                transition: opacity 0.3s;
            `;
            indicator.textContent = '✓ Sauvegarde automatique';
            document.body.appendChild(indicator);
        }

        // Afficher puis masquer
        indicator.style.opacity = '1';
        setTimeout(() => {
            indicator.style.opacity = '0';
        }, 2000);
    }

    /**
     * Afficher une notification de restauration
     */
    function showAutosaveNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--info);
            color: white;
            padding: 10px 20px;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            z-index: 1000;
            opacity: 0;
            transition: opacity 0.3s;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);

        // Afficher la notification
        setTimeout(() => {
            notification.style.opacity = '1';
        }, 10);

        // Masquer puis supprimer
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }

    /**
     * Ajouter un bouton pour vider la sauvegarde automatique
     */
    function addClearAutosaveButton(form, storageKey) {
        // Vérifier s'il y a des données sauvegardées
        const saved = localStorage.getItem(storageKey);
        if (!saved) return;

        // Créer le bouton
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-link';
        button.style.cssText = 'margin-top: 10px; font-size: 0.9rem;';
        button.textContent = 'Vider la sauvegarde automatique';
        button.onclick = () => {
            if (confirm('Êtes-vous sûr de vouloir supprimer la sauvegarde automatique ?')) {
                localStorage.removeItem(storageKey);
                button.remove();
                form.reset();
                alert('Sauvegarde automatique supprimée.');
            }
        };

        // Insérer le bouton après les actions du formulaire
        const formActions = form.querySelector('.form-actions');
        if (formActions) {
            formActions.appendChild(button);
        }
    }

    // Initialiser l'autosave au chargement de la page
    document.addEventListener('DOMContentLoaded', function() {
        const form = document.getElementById('questionnaire-form');
        if (form) {
            initAutosave(form);
        }
    });

})();
