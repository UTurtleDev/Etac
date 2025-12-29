/**
 * Fonctions principales de l'application
 */

// Auto-disparition des messages Django après 5 secondes
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.3s';
            setTimeout(function() {
                alert.remove();
            }, 300);
        });
    }, 5000);
});

// Confirmation avant de quitter une page avec formulaire modifié
let formModified = false;

document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');

    forms.forEach(function(form) {
        form.addEventListener('change', function() {
            formModified = true;
        });

        form.addEventListener('submit', function() {
            formModified = false;
        });
    });
});

window.addEventListener('beforeunload', function(e) {
    if (formModified) {
        e.preventDefault();
        e.returnValue = 'Vous avez des modifications non sauvegardées';
    }
});

// Validation SIREN en temps réel (sans HTMX)
function validateSirenInput(input) {
    const value = input.value.trim();
    const errorDiv = input.nextElementSibling;

    // Supprimer les caractères non numériques
    input.value = value.replace(/\D/g, '');

    if (input.value.length > 0 && input.value.length !== 9) {
        if (errorDiv && errorDiv.classList.contains('error-message')) {
            errorDiv.textContent = 'Le SIREN doit contenir exactement 9 chiffres';
            input.classList.add('error');
        }
    } else {
        if (errorDiv && errorDiv.classList.contains('error-message')) {
            errorDiv.textContent = '';
            input.classList.remove('error');
        }
    }
}

// Appliquer la validation aux inputs SIREN
document.addEventListener('DOMContentLoaded', function() {
    const sirenInputs = document.querySelectorAll('input[name="siren"]');
    sirenInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            validateSirenInput(this);
        });
    });
});
