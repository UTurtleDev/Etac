"""
Script pour tester l'API INSEE avec différents SIREN
et vérifier les clés disponibles selon le type d'entreprise
"""

import os
import requests
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le .env
load_dotenv()

# Récupère la clé API depuis le .env
INSEE_API_KEY = os.getenv('INSEE_API_KEY')


def afficher_dict(d, indent=0):
    """Affiche un dictionnaire de manière structurée avec indentation."""
    prefix = "  " * indent
    
    if isinstance(d, dict):
        for cle, valeur in d.items():
            if isinstance(valeur, (dict, list)):
                print(f"{prefix}{cle}:")
                afficher_dict(valeur, indent + 1)
            else:
                print(f"{prefix}{cle}: {valeur}")
    
    elif isinstance(d, list):
        for i, item in enumerate(d):
            if isinstance(item, (dict, list)):
                print(f"{prefix}[{i}]:")
                afficher_dict(item, indent + 1)
            else:
                print(f"{prefix}[{i}]: {item}")


def rechercher_siren(siren):
    """Recherche une entreprise par son SIREN via l'API INSEE."""
    siren = siren.replace(" ", "").strip()
    
    if not siren.isdigit() or len(siren) != 9:
        print(f"❌ SIREN invalide : {siren} (doit être 9 chiffres)")
        return None
    

    url = f'https://api.insee.fr/api-sirene/3.11/siren/{siren}'
    headers = {
        'X-INSEE-Api-Key-Integration': INSEE_API_KEY
    }

    
    try:
        print(f"\n🔍 Recherche du SIREN : {siren}...")
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ Entreprise trouvée !\n")
            return response.json()
        elif response.status_code == 404:
            print("❌ Entreprise non trouvée\n")
            return None
        else:
            print(f"❌ Erreur API : {response.status_code}\n")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion : {e}\n")
        return None


def afficher_infos_cles(data):
    """Affiche les informations clés pour le formulaire."""
    if not data or "uniteLegale" not in data:
        return
    
    print("\n" + "="*70)
    print("📋 INFORMATIONS CLÉS POUR LE FORMULAIRE")
    print("="*70)
    
    ul = data["uniteLegale"]
    
    print(f"\n🔢 SIREN: {ul.get('siren', 'N/A')}")
    print(f"📅 Date création: {ul.get('dateCreationUniteLegale', 'N/A')}")
    print(f"🏢 Catégorie: {ul.get('categorieEntreprise', 'N/A')}")
    print(f"📊 Code APE: {ul.get('activitePrincipaleNAF25UniteLegale', 'N/A')}")
    
    # Période actuelle
    if ul.get('periodesUniteLegale') and len(ul['periodesUniteLegale']) > 0:
        periode = ul['periodesUniteLegale'][0]
        
        print("\n📝 PÉRIODE ACTUELLE:")
        print(f"  ├─ nomUniteLegale: {periode.get('nomUniteLegale', 'N/A')}")
        print(f"  ├─ denominationUniteLegale: {periode.get('denominationUniteLegale', 'N/A')}")
        print(f"  ├─ denominationUsuelle1UniteLegale: {periode.get('denominationUsuelle1UniteLegale', 'N/A')}")
        print(f"  └─ etatAdministratifUniteLegale: {periode.get('etatAdministratifUniteLegale', 'N/A')}")
        
        # Détermine le nom à afficher
        if periode.get('denominationUniteLegale'):
            nom_a_afficher = periode['denominationUniteLegale']
            type_nom = "Société"
        elif periode.get('denominationUsuelle1UniteLegale'):
            nom_a_afficher = f"{periode.get('denominationUsuelle1UniteLegale')} ({periode.get('nomUniteLegale', '')})"
            type_nom = "Entreprise individuelle avec nom commercial"
        elif periode.get('nomUniteLegale'):
            prenom = ul.get('prenom1UniteLegale', '')
            nom_a_afficher = f"{prenom} {periode['nomUniteLegale']}".strip()
            type_nom = "Entreprise individuelle"
        else:
            nom_a_afficher = "N/A"
            type_nom = "Inconnu"
        
        print(f"\n💡 Type détecté: {type_nom}")
        print(f"💡 Nom à afficher dans le formulaire: {nom_a_afficher}")


def main():
    """Fonction principale."""
    print("="*70)
    print("🔍 TEST API INSEE - RECHERCHE D'ENTREPRISES")
    print("="*70)
    
    # Liste de SIREN à tester
    # Tu peux modifier cette liste pour tester d'autres SIREN
    sirens_a_tester = [
        "500309851",
        # Ajoute d'autres SIREN ici pour tester
    ]
    
    for siren in sirens_a_tester:
        data = rechercher_siren(siren)
        
        if data:
            # Affiche les infos clés
            afficher_infos_cles(data)
            
            # Demande si l'utilisateur veut voir toutes les données
            print("\n" + "="*70)
            reponse = input("📄 Afficher TOUTES les données brutes ? (o/n) : ").lower()
            
            if reponse == 'o':
                print("\n" + "="*70)
                print("📦 DONNÉES COMPLÈTES")
                print("="*70 + "\n")
                afficher_dict(data)
        
        print("\n" + "="*70 + "\n")
    
    # Mode interactif
    while True:
        print("="*70)
        siren = input("🔍 Entre un SIREN à tester (ou 'q' pour quitter) : ").strip()
        
        if siren.lower() == 'q':
            print("👋 Au revoir !")
            break
        
        data = rechercher_siren(siren)
        
        if data:
            afficher_infos_cles(data)
            
            print("\n" + "="*70)
            reponse = input("📄 Afficher TOUTES les données brutes ? (o/n) : ").lower()
            
            if reponse == 'o':
                print("\n" + "="*70)
                print("📦 DONNÉES COMPLÈTES")
                print("="*70 + "\n")
                afficher_dict(data)
        
        print("\n")


if __name__ == "__main__":
    main()
