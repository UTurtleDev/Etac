import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


# Mapping des messages d'erreur techniques vers messages user-friendly
ERROR_MESSAGES = {
    'Entreprise non trouvée': 'Ce numéro SIREN n\'existe pas dans la base des entreprises françaises. Vérifiez qu\'il est correct (9 chiffres).',
    'Délai d\'attente dépassé': 'Le service de vérification des entreprises ne répond pas. Veuillez réessayer dans quelques instants.',
    'Erreur de connexion à l\'API INSEE': 'Impossible de vérifier le SIREN pour le moment. Veuillez réessayer ultérieurement.',
    'Erreur technique': 'Une erreur technique est survenue. Si le problème persiste, contactez le support.',
}


def get_company_info(siren):
    """
    Récupère les informations d'une entreprise via l'API INSEE Sirene 3.11.
    Utilise le cache pour économiser les appels (24h).

    Args:
        siren (str): Numéro SIREN de l'entreprise (9 chiffres)

    Returns:
        dict: {
            'success': bool,
            'nom': str (si succès),
            'siren': str (si succès),
            'error': str|None
        }
    """
    # Vérifier le cache
    cache_key = f'insee_siren_{siren}'
    cached = cache.get(cache_key)
    if cached:
        logger.info(f'API INSEE - Cache hit for SIREN {siren}')
        return cached

    # Validation format SIREN
    if not siren or len(siren) != 9 or not siren.isdigit():
        return {
            'success': False,
            'error': 'Le SIREN doit contenir exactement 9 chiffres'
        }

    # Appel API INSEE avec nouvelle version 3.11
    url = f'https://api.insee.fr/api-sirene/3.11/siren/{siren}'
    headers = {
        'X-INSEE-Api-Key-Integration': settings.INSEE_API_KEY
    }

    try:
        logger.info(f'API INSEE - Calling API for SIREN {siren}')
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            # Extraction du nom de l'entreprise
            unite = data.get('uniteLegale', {})
            periodes = unite.get('periodesUniteLegale', [{}])
            periode = periodes[0] if periodes else {}

            # Logique de récupération du nom selon la priorité
            denomination = periode.get('denominationUniteLegale')
            if denomination:
                nom = denomination
            else:
                denomination_usuelle = periode.get('denominationUsuelle1UniteLegale')
                nom_legale = periode.get('nomUniteLegale', '')
                prenom_usuel = unite.get('prenomUsuelUniteLegale', '')

                if denomination_usuelle:
                    # Format: denominationUsuelle1UniteLegale (nomUniteLegale prenomUsuelUniteLegale)
                    complement = f"{nom_legale} {prenom_usuel}".strip()
                    nom = f"{denomination_usuelle} ({complement})" if complement else denomination_usuelle
                else:
                    # Format: nomUniteLegale prenomUsuelUniteLegale
                    nom = f"{nom_legale} {prenom_usuel}".strip()

            result = {
                'success': True,
                'nom': nom,
                'siren': siren,
                'error': None
            }

            # Mise en cache 24h (86400 secondes)
            cache.set(cache_key, result, 86400)
            logger.info(f'API INSEE - Success for SIREN {siren}: {nom}')
            return result

        elif response.status_code == 404:
            logger.warning(f'API INSEE - SIREN not found: {siren}')
            error_key = 'Entreprise non trouvée'
            return {
                'success': False,
                'error': ERROR_MESSAGES.get(error_key, error_key)
            }
        else:
            logger.error(f'API INSEE - Error {response.status_code} for SIREN {siren}')
            error_key = 'Erreur de connexion à l\'API INSEE'
            return {
                'success': False,
                'error': ERROR_MESSAGES.get(error_key, error_key)
            }

    except requests.Timeout:
        logger.error(f'API INSEE - Timeout for SIREN {siren}')
        error_key = 'Délai d\'attente dépassé'
        return {
            'success': False,
            'error': ERROR_MESSAGES.get(error_key, error_key)
        }
    except Exception as e:
        logger.error(f'API INSEE - Exception for SIREN {siren}: {str(e)}')
        error_key = 'Erreur technique'
        return {
            'success': False,
            'error': ERROR_MESSAGES.get(error_key, error_key)
        }
