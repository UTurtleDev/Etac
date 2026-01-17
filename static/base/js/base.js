/**
 * Cabinet ETAC - JavaScript de base
 * Fichier JS commun à toutes les applications du site
 */

/* ============================================================================
   GESTION DES COOKIES RGPD
   ============================================================================ */

/**
 * Crée un cookie avec une durée d'expiration
 */
function setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = "expires=" + date.toUTCString();
    document.cookie = name + "=" + value + ";" + expires + ";path=/;SameSite=Lax";
}

/**
 * Récupère la valeur d'un cookie
 */
function getCookie(name) {
    const nameEQ = name + "=";
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let cookie = cookies[i];
        while (cookie.charAt(0) === ' ') {
            cookie = cookie.substring(1);
        }
        if (cookie.indexOf(nameEQ) === 0) {
            return cookie.substring(nameEQ.length, cookie.length);
        }
    }
    return null;
}

/**
 * Accepte les cookies RGPD
 */
function acceptCookies() {
    // Créer un cookie Django valide 13 mois (environ 395 jours)
    setCookie('cookies_accepted', 'true', 395);
    setCookie('cookies_accepted_date', new Date().toISOString(), 395);

    // Masquer la bannière
    const banner = document.getElementById('cookie-banner');
    if (banner) {
        banner.style.display = 'none';
    }
}

/**
 * Vérifie le consentement cookies au chargement
 */
function checkCookieConsent() {
    const banner = document.getElementById('cookie-banner');
    if (!banner) return;

    const accepted = getCookie('cookies_accepted');
    const acceptedDate = getCookie('cookies_accepted_date');

    if (accepted && acceptedDate) {
        // Vérifier la validité du consentement (13 mois)
        const consentDate = new Date(acceptedDate);
        const now = new Date();
        const monthsDiff = (now - consentDate) / (1000 * 60 * 60 * 24 * 30);

        if (monthsDiff > 13) {
            // Consentement expiré, afficher la bannière
            banner.style.display = 'block';
        } else {
            // Consentement valide, masquer la bannière
            banner.style.display = 'none';
        }
    } else {
        // Pas de consentement, afficher la bannière
        banner.style.display = 'block';
    }
}

// Vérifier au chargement de la page
document.addEventListener('DOMContentLoaded', checkCookieConsent);
