/**
 * Barre de progression pour les questionnaires
 * Calcule automatiquement la progression en fonction des champs requis remplis
 */

(function() {
    'use strict';

    let progressBar = null;
    let progressText = null;
    let totalRequiredFields = 0;

    /**
     * Initialiser la barre de progression
     */
    function initProgressBar() {
        const form = document.getElementById('questionnaire-form');
        if (!form) return;

        // Créer la barre de progression
        createProgressBar(form);

        // Compter les champs requis
        totalRequiredFields = form.querySelectorAll('[required]').length;

        // Mettre à jour la progression au chargement
        updateProgress();

        // Mettre à jour lors des changements
        form.addEventListener('change', updateProgress);
        form.addEventListener('input', debounce(updateProgress, 500));
    }

    /**
     * Créer l'élément barre de progression
     */
    function createProgressBar(form) {
        const container = document.createElement('div');
        container.className = 'progress-container';
        container.innerHTML = `
            <div class="progress-header">
                <span class="progress-label">Progression du questionnaire</span>
                <span class="progress-percentage">0%</span>
            </div>
            <div class="progress-bar-wrapper">
                <div class="progress-bar-fill"></div>
            </div>
            <p class="progress-help">
                <small>Tous les champs marqués d'un <span class="required">*</span> sont obligatoires</small>
            </p>
        `;

        // Insérer au début du formulaire
        form.insertBefore(container, form.firstChild);

        progressBar = container.querySelector('.progress-bar-fill');
        progressText = container.querySelector('.progress-percentage');
    }

    /**
     * Mettre à jour la progression
     */
    function updateProgress() {
        const form = document.getElementById('questionnaire-form');
        if (!form || !progressBar) return;

        // Compter les champs requis remplis
        let filledFields = 0;
        const requiredFields = form.querySelectorAll('[required]');

        requiredFields.forEach(field => {
            if (isFieldFilled(field)) {
                filledFields++;
            }
        });

        // Calculer le pourcentage
        const percentage = totalRequiredFields > 0
            ? Math.round((filledFields / totalRequiredFields) * 100)
            : 0;

        // Mettre à jour l'affichage
        progressBar.style.width = percentage + '%';
        progressText.textContent = percentage + '%';

        // Changer la couleur en fonction de la progression
        if (percentage < 33) {
            progressBar.style.background = 'var(--erreur)';
        } else if (percentage < 66) {
            progressBar.style.background = 'var(--avertissement)';
        } else if (percentage < 100) {
            progressBar.style.background = 'var(--vert-clair)';
        } else {
            progressBar.style.background = 'var(--vert-moyen)';
        }
    }

    /**
     * Vérifier si un champ est rempli
     */
    function isFieldFilled(field) {
        const type = field.type;
        const tagName = field.tagName.toLowerCase();

        if (type === 'radio') {
            // Pour les radio, vérifier si au moins un est coché
            const name = field.name;
            const radios = document.querySelectorAll(`input[name="${name}"]`);
            return Array.from(radios).some(r => r.checked);
        } else if (type === 'checkbox') {
            return field.checked;
        } else if (tagName === 'select') {
            return field.value !== '';
        } else if (tagName === 'textarea' || type === 'text' || type === 'email' || type === 'number') {
            return field.value.trim() !== '';
        }

        return false;
    }

    /**
     * Debounce pour éviter trop d'appels
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Initialiser au chargement de la page
    document.addEventListener('DOMContentLoaded', initProgressBar);

})();
