/**
 * Gestion des cookies RGPD
 */

function acceptCookies() {
    // Stocker le consentement dans localStorage
    localStorage.setItem('cookies-accepted', 'true');
    localStorage.setItem('cookies-accepted-date', new Date().toISOString());

    // Masquer la bannière
    document.getElementById('cookie-banner').style.display = 'none';
}

function checkCookieConsent() {
    const accepted = localStorage.getItem('cookies-accepted');
    const acceptedDate = localStorage.getItem('cookies-accepted-date');

    if (accepted && acceptedDate) {
        // Vérifier la validité du consentement (13 mois)
        const consentDate = new Date(acceptedDate);
        const now = new Date();
        const monthsDiff = (now - consentDate) / (1000 * 60 * 60 * 24 * 30);

        if (monthsDiff > 13) {
            // Consentement expiré
            localStorage.removeItem('cookies-accepted');
            localStorage.removeItem('cookies-accepted-date');
            document.getElementById('cookie-banner').style.display = 'block';
        } else {
            // Consentement valide
            document.getElementById('cookie-banner').style.display = 'none';
        }
    } else {
        // Pas de consentement
        document.getElementById('cookie-banner').style.display = 'block';
    }
}

// Vérifier au chargement de la page
document.addEventListener('DOMContentLoaded', checkCookieConsent);
