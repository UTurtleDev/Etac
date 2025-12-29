import requests
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


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
            nom = (
                unite.get('denominationUniteLegale') or
                unite.get('denominationUsuelle1UniteLegale') or
                f"{unite.get('prenomUsuelUniteLegale', '')} {unite.get('nomUniteLegale', '')}".strip()
            )

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
            return {
                'success': False,
                'error': 'Entreprise non trouvée'
            }
        else:
            logger.error(f'API INSEE - Error {response.status_code} for SIREN {siren}')
            return {
                'success': False,
                'error': 'Erreur de connexion à l\'API INSEE'
            }

    except requests.Timeout:
        logger.error(f'API INSEE - Timeout for SIREN {siren}')
        return {
            'success': False,
            'error': 'Délai d\'attente dépassé'
        }
    except Exception as e:
        logger.error(f'API INSEE - Exception for SIREN {siren}: {str(e)}')
        return {
            'success': False,
            'error': 'Erreur technique'
        }
