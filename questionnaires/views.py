from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import csv
from .models import Entreprise, QuestionnaireClient, QuestionnaireCollaborateur
from .utils import get_company_info


def home(request):
    """Page d'accueil avec les 2 CTA"""
    return render(request, 'questionnaires/home.html')


def mentions_legales(request):
    """Page mentions légales et RGPD"""
    return render(request, 'questionnaires/mentions_legales.html')


# ============================================================================
# PARCOURS CLIENT
# ============================================================================

def client_introduction(request):
    """Page d'introduction du parcours client"""
    return render(request, 'questionnaires/client/introduction.html')


def client_identification(request):
    """Page d'identification avec SIREN"""
    if request.method == 'POST':
        siren = request.POST.get('siren', '').strip()

        # Validation SIREN
        if not siren:
            messages.error(request, 'Veuillez saisir un numéro SIREN')
            return render(request, 'questionnaires/client/identification.html')

        # Appel API INSEE
        result = get_company_info(siren)

        if not result['success']:
            messages.error(request, result['error'])
            return render(request, 'questionnaires/client/identification.html', {
                'siren': siren
            })

        # Vérifier si un questionnaire existe déjà
        try:
            entreprise = Entreprise.objects.get(siren=siren)
            questionnaire_exists = hasattr(entreprise, 'questionnaire_client')

            if questionnaire_exists:
                return render(request, 'questionnaires/client/identification.html', {
                    'siren': siren,
                    'nom_entreprise': entreprise.nom_entreprise,
                    'questionnaire_exists': True
                })
        except Entreprise.DoesNotExist:
            pass

        # Stocker les infos en session et rediriger vers le questionnaire
        request.session['client_siren'] = siren
        request.session['client_nom_entreprise'] = result['nom']
        return redirect('client_questionnaire')

    return render(request, 'questionnaires/client/identification.html')


@require_http_methods(["GET"])
def validate_siren(request):
    """
    Endpoint HTMX pour valider un SIREN et récupérer le nom.
    """
    siren = request.GET.get('siren', '').strip()

    if not siren:
        return HttpResponse(
            '<span class="error">Veuillez saisir un numéro SIREN</span>'
        )

    result = get_company_info(siren)

    if result['success']:
        return HttpResponse(f'''
            <div class="company-found">
                <strong>✓ Entreprise trouvée :</strong> {result['nom']}
            </div>
        ''')
    else:
        return HttpResponse(f'''
            <span class="error">✗ {result['error']}</span>
        ''')


def client_questionnaire(request):
    """Page du questionnaire client"""
    # Vérifier que le SIREN est en session
    siren = request.session.get('client_siren')
    nom_entreprise = request.session.get('client_nom_entreprise')

    if not siren or not nom_entreprise:
        messages.error(request, 'Session expirée. Veuillez recommencer.')
        return redirect('client_identification')

    if request.method == 'POST':
        # Créer ou récupérer l'entreprise
        entreprise, created = Entreprise.objects.get_or_create(
            siren=siren,
            defaults={'nom_entreprise': nom_entreprise}
        )

        # Traiter les checkboxes pour accompagnement_souhaite
        accompagnement = request.POST.getlist('accompagnement_souhaite')

        # Créer ou mettre à jour le questionnaire
        questionnaire, created = QuestionnaireClient.objects.update_or_create(
            entreprise=entreprise,
            defaults={
                'logiciel_facturation': 'logiciel_facturation' in request.POST,
                'logiciel_facturation_nom': request.POST.get('logiciel_facturation_nom', ''),
                'factures_format_electronique': request.POST.get('factures_format_electronique', ''),
                'logiciel_devis': 'logiciel_devis' in request.POST,
                'logiciel_devis_nom': request.POST.get('logiciel_devis_nom', ''),
                'caisse_enregistreuse': request.POST.get('caisse_enregistreuse', ''),
                'caisse_enregistreuse_nom': request.POST.get('caisse_enregistreuse_nom', ''),
                'caisse_certifiee': request.POST.get('caisse_certifiee', ''),
                'plateforme_agreee': request.POST.get('plateforme_agreee', ''),
                'plateforme_agreee_nom': request.POST.get('plateforme_agreee_nom', ''),
                'gestion_future': request.POST.get('gestion_future', ''),
                'aisance_outils': request.POST.get('aisance_outils', ''),
                'reception_factures_achats': request.POST.get('reception_factures_achats', ''),
                'reception_achats_autre': request.POST.get('reception_achats_autre', ''),
                'envoi_factures_ventes': request.POST.get('envoi_factures_ventes', ''),
                'envoi_ventes_autre': request.POST.get('envoi_ventes_autre', ''),
                'conservation_factures': request.POST.get('conservation_factures', ''),
                'accompagnement_souhaite': accompagnement,
                'accompagnement_autre': request.POST.get('accompagnement_autre', ''),
                'commentaires': request.POST.get('commentaires', ''),
            }
        )

        # Stocker l'ID du questionnaire en session
        request.session['questionnaire_id'] = str(entreprise.siren)
        messages.success(request, 'Questionnaire enregistré avec succès !')
        return redirect('client_recapitulatif')

    return render(request, 'questionnaires/client/questionnaire.html', {
        'siren': siren,
        'nom_entreprise': nom_entreprise
    })


def client_recapitulatif(request):
    """Page de récapitulatif client"""
    # TODO: Récupérer les données du questionnaire
    return render(request, 'questionnaires/client/recapitulatif.html')


# ============================================================================
# PARCOURS COLLABORATEUR
# ============================================================================

@login_required
def dashboard(request):
    """Dashboard collaborateur avec filtres et recherche"""
    # Récupérer les paramètres de filtrage
    search_query = request.GET.get('search', '').strip()
    filter_questionnaire = request.GET.get('filter', 'all')
    sort_by = request.GET.get('sort', '-date_modification')

    # Statistiques
    total_entreprises = Entreprise.objects.filter(is_archived=False).count()
    questionnaires_client = QuestionnaireClient.objects.count()
    questionnaires_collaborateur = QuestionnaireCollaborateur.objects.count()

    # Liste des entreprises avec filtres
    entreprises = Entreprise.objects.filter(is_archived=False).select_related(
        'questionnaire_client',
        'questionnaire_collaborateur'
    )

    # Recherche par SIREN ou nom
    if search_query:
        entreprises = entreprises.filter(
            Q(siren__icontains=search_query) |
            Q(nom_entreprise__icontains=search_query)
        )

    # Filtrer par type de questionnaire
    if filter_questionnaire == 'client_only':
        entreprises = entreprises.filter(
            questionnaire_client__isnull=False,
            questionnaire_collaborateur__isnull=True
        )
    elif filter_questionnaire == 'collaborateur_only':
        entreprises = entreprises.filter(
            questionnaire_client__isnull=True,
            questionnaire_collaborateur__isnull=False
        )
    elif filter_questionnaire == 'both':
        entreprises = entreprises.filter(
            questionnaire_client__isnull=False,
            questionnaire_collaborateur__isnull=False
        )
    elif filter_questionnaire == 'none':
        entreprises = entreprises.filter(
            questionnaire_client__isnull=True,
            questionnaire_collaborateur__isnull=True
        )

    # Tri
    valid_sorts = ['siren', '-siren', 'nom_entreprise', '-nom_entreprise',
                   'date_creation', '-date_creation', 'date_modification', '-date_modification']
    if sort_by in valid_sorts:
        entreprises = entreprises.order_by(sort_by)

    context = {
        'total_entreprises': total_entreprises,
        'questionnaires_client': questionnaires_client,
        'questionnaires_collaborateur': questionnaires_collaborateur,
        'entreprises': entreprises,
        'search_query': search_query,
        'filter_questionnaire': filter_questionnaire,
        'sort_by': sort_by,
    }

    return render(request, 'questionnaires/collaborateur/dashboard.html', context)


@login_required
def collaborateur_identification(request):
    """Identification entreprise pour nouveau questionnaire collaborateur"""
    if request.method == 'POST':
        siren = request.POST.get('siren', '').strip()

        if not siren:
            messages.error(request, 'Veuillez saisir un numéro SIREN')
            return render(request, 'questionnaires/collaborateur/identification.html')

        # Appel API INSEE
        result = get_company_info(siren)

        if not result['success']:
            messages.error(request, result['error'])
            return render(request, 'questionnaires/collaborateur/identification.html', {
                'siren': siren
            })

        # Vérifier si un questionnaire collaborateur existe déjà
        try:
            entreprise = Entreprise.objects.get(siren=siren)
            questionnaire_exists = hasattr(entreprise, 'questionnaire_collaborateur')

            if questionnaire_exists:
                messages.warning(request, 'Un questionnaire collaborateur existe déjà pour cette entreprise.')
                return redirect('voir_questionnaire', siren=siren)
        except Entreprise.DoesNotExist:
            pass

        # Stocker en session
        request.session['collab_siren'] = siren
        request.session['collab_nom_entreprise'] = result['nom']
        return redirect('collaborateur_questionnaire')

    return render(request, 'questionnaires/collaborateur/identification.html')


@login_required
def collaborateur_questionnaire(request):
    """Questionnaire collaborateur"""
    siren = request.session.get('collab_siren')
    nom_entreprise = request.session.get('collab_nom_entreprise')

    if not siren or not nom_entreprise:
        messages.error(request, 'Session expirée. Veuillez recommencer.')
        return redirect('collaborateur_identification')

    if request.method == 'POST':
        # Créer ou récupérer l'entreprise
        entreprise, created = Entreprise.objects.get_or_create(
            siren=siren,
            defaults={'nom_entreprise': nom_entreprise}
        )

        # Créer ou mettre à jour le questionnaire
        questionnaire, created = QuestionnaireCollaborateur.objects.update_or_create(
            entreprise=entreprise,
            defaults={
                'collaborateur': request.user,
                'assujettie_tva': request.POST.get('assujettie_tva', ''),
                'code_ape': request.POST.get('code_ape', ''),
                'activite_precise': request.POST.get('activite_precise', ''),
                'taille_entreprise': request.POST.get('taille_entreprise', ''),
                'regime_tva': request.POST.get('regime_tva', ''),
                'activite_exoneree_tva': request.POST.get('activite_exoneree_tva', ''),
                'plateforme_agreee': 'plateforme_agreee' in request.POST,
                'plateforme_agreee_nom': request.POST.get('plateforme_agreee_nom', ''),
                'nb_factures_ventes': request.POST.get('nb_factures_ventes', ''),
                'nb_clients_actifs': request.POST.get('nb_clients_actifs', ''),
                'vente_btob_domestique': 'vente_btob_domestique' in request.POST,
                'vente_btob_export': 'vente_btob_export' in request.POST,
                'vente_btoc_facture': 'vente_btoc_facture' in request.POST,
                'vente_btoc_caisse': 'vente_btoc_caisse' in request.POST,
                'nb_factures_achats': request.POST.get('nb_factures_achats', ''),
                'nb_fournisseurs_actifs': request.POST.get('nb_fournisseurs_actifs', ''),
                'achat_btob_domestique': 'achat_btob_domestique' in request.POST,
                'achat_btob_intracommunautaire': 'achat_btob_intracommunautaire' in request.POST,
                'achat_btob_hors_ue': 'achat_btob_hors_ue' in request.POST,
                'commentaires': request.POST.get('commentaires', ''),
            }
        )

        # Stocker en session
        request.session['questionnaire_id'] = str(entreprise.siren)
        messages.success(request, 'Questionnaire enregistré avec succès !')
        return redirect('collaborateur_recapitulatif')

    return render(request, 'questionnaires/collaborateur/questionnaire.html', {
        'siren': siren,
        'nom_entreprise': nom_entreprise
    })


@login_required
def collaborateur_recapitulatif(request):
    """Récapitulatif questionnaire collaborateur"""
    # TODO: Récupérer les données
    return render(request, 'questionnaires/collaborateur/recapitulatif.html')


@login_required
def voir_questionnaire(request, siren):
    """Voir le détail d'un questionnaire"""
    entreprise = get_object_or_404(Entreprise, siren=siren)

    has_client = hasattr(entreprise, 'questionnaire_client')
    has_collaborateur = hasattr(entreprise, 'questionnaire_collaborateur')

    context = {
        'entreprise': entreprise,
        'has_client': has_client,
        'has_collaborateur': has_collaborateur,
    }

    if has_client:
        context['questionnaire_client'] = entreprise.questionnaire_client

    if has_collaborateur:
        context['questionnaire_collaborateur'] = entreprise.questionnaire_collaborateur

    return render(request, 'questionnaires/collaborateur/voir_questionnaire.html', context)


# ============================================================================
# ACTIONS - ÉDITION, SUPPRESSION, EXPORT
# ============================================================================

@login_required
@require_http_methods(["POST"])
def archiver_entreprise(request, siren):
    """Archiver (soft delete) une entreprise"""
    entreprise = get_object_or_404(Entreprise, siren=siren)
    entreprise.is_archived = True
    entreprise.save()
    messages.success(request, f'L\'entreprise {entreprise.nom_entreprise} a été archivée.')
    return redirect('dashboard')


@login_required
def editer_entreprise(request, siren):
    """Éditer les questionnaires d'une entreprise"""
    entreprise = get_object_or_404(Entreprise, siren=siren)

    has_client = hasattr(entreprise, 'questionnaire_client')
    has_collaborateur = hasattr(entreprise, 'questionnaire_collaborateur')

    # Pour l'instant, rediriger vers la vue de visualisation
    # TODO: Créer des formulaires d'édition dédiés
    messages.info(request, 'La fonctionnalité d\'édition sera bientôt disponible.')
    return redirect('voir_questionnaire', siren=siren)


@login_required
def export_csv(request):
    """Exporter toutes les entreprises et questionnaires en CSV"""
    # Créer la réponse CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="export_questionnaires.csv"'
    response.write('\ufeff')  # BOM UTF-8 pour Excel

    writer = csv.writer(response, delimiter=';')

    # En-têtes
    writer.writerow([
        'SIREN',
        'Nom Entreprise',
        'Date Création',
        'Date Modification',
        'Q. Client Complété',
        'Q. Collaborateur Complété',
        # Client
        'Client - Logiciel Facturation',
        'Client - Logiciel Facturation Nom',
        'Client - Factures Format Électronique',
        'Client - Logiciel Devis',
        'Client - Logiciel Devis Nom',
        'Client - Caisse Enregistreuse',
        'Client - Caisse Enregistreuse Nom',
        'Client - Caisse Certifiée',
        'Client - Plateforme Agréée',
        'Client - Plateforme Agréée Nom',
        'Client - Gestion Future',
        'Client - Aisance Outils',
        'Client - Réception Factures Achats',
        'Client - Reception Achats Autre',
        'Client - Envoi Factures Ventes',
        'Client - Envoi Ventes Autre',
        'Client - Conservation Factures',
        'Client - Accompagnement Souhaité',
        'Client - Accompagnement Autre',
        'Client - Commentaires',
        # Collaborateur
        'Collab - Assujettie TVA',
        'Collab - Code APE',
        'Collab - Activité Précise',
        'Collab - Taille Entreprise',
        'Collab - Régime TVA',
        'Collab - Activité Exonérée TVA',
        'Collab - Plateforme Agréée',
        'Collab - Plateforme Agréée Nom',
        'Collab - Nb Factures Ventes',
        'Collab - Nb Clients Actifs',
        'Collab - Vente B2B France',
        'Collab - Vente B2B Export',
        'Collab - Vente B2C Facture',
        'Collab - Vente B2C Caisse',
        'Collab - Nb Factures Achats',
        'Collab - Nb Fournisseurs Actifs',
        'Collab - Achat B2B France',
        'Collab - Achat B2B UE',
        'Collab - Achat B2B Hors UE',
        'Collab - Commentaires',
    ])

    # Données
    entreprises = Entreprise.objects.filter(is_archived=False).select_related(
        'questionnaire_client',
        'questionnaire_collaborateur'
    )

    for e in entreprises:
        qc = e.questionnaire_client if hasattr(e, 'questionnaire_client') else None
        qco = e.questionnaire_collaborateur if hasattr(e, 'questionnaire_collaborateur') else None

        writer.writerow([
            e.siren,
            e.nom_entreprise,
            e.date_creation.strftime('%d/%m/%Y %H:%M') if e.date_creation else '',
            e.date_modification.strftime('%d/%m/%Y %H:%M') if e.date_modification else '',
            'Oui' if qc else 'Non',
            'Oui' if qco else 'Non',
            # Client
            'Oui' if qc and qc.logiciel_facturation else 'Non' if qc else '',
            qc.logiciel_facturation_nom if qc else '',
            qc.get_factures_format_electronique_display() if qc else '',
            'Oui' if qc and qc.logiciel_devis else 'Non' if qc else '',
            qc.logiciel_devis_nom if qc else '',
            qc.get_caisse_enregistreuse_display() if qc else '',
            qc.caisse_enregistreuse_nom if qc else '',
            qc.get_caisse_certifiee_display() if qc else '',
            qc.get_plateforme_agreee_display() if qc else '',
            qc.plateforme_agreee_nom if qc else '',
            qc.get_gestion_future_display() if qc else '',
            qc.get_aisance_outils_display() if qc else '',
            qc.get_reception_factures_achats_display() if qc else '',
            qc.reception_achats_autre if qc else '',
            qc.get_envoi_factures_ventes_display() if qc else '',
            qc.envoi_ventes_autre if qc else '',
            qc.get_conservation_factures_display() if qc else '',
            ', '.join(qc.accompagnement_souhaite) if qc and qc.accompagnement_souhaite else '',
            qc.accompagnement_autre if qc else '',
            qc.commentaires if qc else '',
            # Collaborateur
            qco.get_assujettie_tva_display() if qco else '',
            qco.code_ape if qco else '',
            qco.activite_precise if qco else '',
            qco.get_taille_entreprise_display() if qco else '',
            qco.get_regime_tva_display() if qco else '',
            qco.get_activite_exoneree_tva_display() if qco else '',
            'Oui' if qco and qco.plateforme_agreee else 'Non' if qco else '',
            qco.plateforme_agreee_nom if qco else '',
            qco.get_nb_factures_ventes_display() if qco else '',
            qco.get_nb_clients_actifs_display() if qco else '',
            'Oui' if qco and qco.vente_btob_domestique else 'Non' if qco else '',
            'Oui' if qco and qco.vente_btob_export else 'Non' if qco else '',
            'Oui' if qco and qco.vente_btoc_facture else 'Non' if qco else '',
            'Oui' if qco and qco.vente_btoc_caisse else 'Non' if qco else '',
            qco.get_nb_factures_achats_display() if qco else '',
            qco.get_nb_fournisseurs_actifs_display() if qco else '',
            'Oui' if qco and qco.achat_btob_domestique else 'Non' if qco else '',
            'Oui' if qco and qco.achat_btob_intracommunautaire else 'Non' if qco else '',
            'Oui' if qco and qco.achat_btob_hors_ue else 'Non' if qco else '',
            qco.commentaires if qco else '',
        ])

    return response
