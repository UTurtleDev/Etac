from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.core.paginator import Paginator
import csv
from .models import Entreprise, QuestionnaireClient, QuestionnaireCollaborateur
from .forms import QuestionnaireClientForm, QuestionnaireCollaborateurForm
from .utils import get_company_info


def _process_siren_identification(request, siren, session_prefix, check_existing_questionnaire=False):
    """
    Logique commune de validation SIREN et stockage en session.

    Args:
        request: HttpRequest
        siren: str - Numéro SIREN
        session_prefix: str - 'client' ou 'collab'
        check_existing_questionnaire: bool - Vérifier si questionnaire existe

    Returns:
        dict: {
            'success': bool,
            'entreprise': Entreprise (si success=True),
            'exists': bool (si check_existing_questionnaire=True),
            'error': str (si success=False)
        }
    """
    # Validation SIREN
    if not siren:
        return {'success': False, 'error': 'Veuillez saisir un numéro SIREN'}

    # Appel API INSEE
    result = get_company_info(siren)

    if not result['success']:
        return {'success': False, 'error': result['error']}

    # Vérifier si un questionnaire existe déjà
    try:
        entreprise = Entreprise.objects.get(siren=siren)
        exists = False

        if check_existing_questionnaire:
            questionnaire_attr = f'questionnaire_{session_prefix}'
            exists = hasattr(entreprise, questionnaire_attr)

    except Entreprise.DoesNotExist:
        entreprise = None
        exists = False

    # Stocker en session
    request.session[f'{session_prefix}_siren'] = siren
    request.session[f'{session_prefix}_nom_entreprise'] = result['nom']

    return {
        'success': True,
        'entreprise': entreprise,
        'exists': exists,
        'nom': result['nom'],
        'error': None
    }


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
        action = request.POST.get('action', '')

        # Utiliser la fonction helper pour le traitement
        result = _process_siren_identification(
            request, siren, 'client', check_existing_questionnaire=True
        )

        if not result['success']:
            messages.error(request, result['error'])
            return render(request, 'questionnaires/client/identification.html', {
                'siren': siren
            })

        # Si un questionnaire existe déjà
        if result['exists']:
            # Si l'utilisateur a confirmé qu'il veut modifier, rediriger vers le questionnaire
            if action == 'modifier':
                return redirect('client_questionnaire')
            # Sinon, afficher un avertissement
            return render(request, 'questionnaires/client/identification.html', {
                'siren': siren,
                'nom_entreprise': result['nom'],
                'questionnaire_exists': True
            })

        # Rediriger vers le questionnaire
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

    # Créer ou récupérer l'entreprise
    entreprise, created = Entreprise.objects.get_or_create(
        siren=siren,
        defaults={'nom_entreprise': nom_entreprise}
    )

    # Récupérer l'instance existante si elle existe
    questionnaire = getattr(entreprise, 'questionnaire_client', None)

    if request.method == 'POST':
        form = QuestionnaireClientForm(request.POST, instance=questionnaire)
        if form.is_valid():
            questionnaire = form.save(commit=False)
            questionnaire.entreprise = entreprise
            questionnaire.save()
            form.save_m2m()  # Nécessaire pour sauvegarder les ManyToMany (accompagnement_souhaite)

            # Stocker l'ID du questionnaire en session
            request.session['questionnaire_id'] = str(entreprise.siren)
            messages.success(request, 'Questionnaire enregistré avec succès !')
            return redirect('client_recapitulatif')
        else:
            # Afficher les erreurs spécifiques
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'{error}')
                    else:
                        field_label = form.fields[field].label or field
                        messages.error(request, f'{field_label}: {error}')
    else:
        form = QuestionnaireClientForm(instance=questionnaire)

    return render(request, 'questionnaires/client/questionnaire.html', {
        'siren': siren,
        'nom_entreprise': nom_entreprise,
        'form': form
    })


def client_recapitulatif(request):
    """Page de récapitulatif client"""
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

    # Pagination
    paginator = Paginator(entreprises, 20)  # 20 entreprises par page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'total_entreprises': total_entreprises,
        'questionnaires_client': questionnaires_client,
        'questionnaires_collaborateur': questionnaires_collaborateur,
        'entreprises': page_obj,
        'page_obj': page_obj,
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

        # Utiliser la fonction helper pour le traitement
        result = _process_siren_identification(
            request, siren, 'collab', check_existing_questionnaire=True
        )

        if not result['success']:
            messages.error(request, result['error'])
            return render(request, 'questionnaires/collaborateur/identification.html', {
                'siren': siren
            })

        # Si un questionnaire collaborateur existe déjà, rediriger vers la visualisation
        if result['exists']:
            messages.warning(request, 'Un questionnaire collaborateur existe déjà pour cette entreprise.')
            return redirect('voir_questionnaire', siren=siren)

        # Rediriger vers le questionnaire
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

    # Créer ou récupérer l'entreprise
    entreprise, created = Entreprise.objects.get_or_create(
        siren=siren,
        defaults={'nom_entreprise': nom_entreprise}
    )

    # Récupérer l'instance existante si elle existe
    questionnaire = getattr(entreprise, 'questionnaire_collaborateur', None)

    if request.method == 'POST':
        form = QuestionnaireCollaborateurForm(request.POST, instance=questionnaire)
        if form.is_valid():
            questionnaire = form.save(commit=False)
            questionnaire.entreprise = entreprise
            questionnaire.collaborateur = request.user
            questionnaire.save()
            form.save_m2m()

            # Stocker en session
            request.session['questionnaire_id'] = str(entreprise.siren)
            messages.success(request, 'Questionnaire enregistré avec succès !')
            return redirect('collaborateur_recapitulatif')
        else:
            # Afficher les erreurs spécifiques
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'{error}')
                    else:
                        field_label = form.fields[field].label or field
                        messages.error(request, f'{field_label}: {error}')
    else:
        form = QuestionnaireCollaborateurForm(instance=questionnaire)

    return render(request, 'questionnaires/collaborateur/questionnaire.html', {
        'siren': siren,
        'nom_entreprise': nom_entreprise,
        'form': form
    })


@login_required
def collaborateur_recapitulatif(request):
    """Récapitulatif questionnaire collaborateur"""
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

    # Récupérer ou initialiser les questionnaires
    questionnaire_client = getattr(entreprise, 'questionnaire_client', None)
    questionnaire_collaborateur = getattr(entreprise, 'questionnaire_collaborateur', None)

    if request.method == 'POST':
        # Déterminer quel formulaire a été soumis
        form_type = request.POST.get('form_type')

        if form_type == 'client' and has_client:
            form_client = QuestionnaireClientForm(request.POST, instance=questionnaire_client)
            if form_client.is_valid():
                questionnaire = form_client.save(commit=False)
                questionnaire.modifie_par_collaborateur = request.user
                questionnaire.save()
                form_client.save_m2m()
                messages.success(request, 'Questionnaire client mis à jour avec succès.')
                return redirect('voir_questionnaire', siren=siren)
            else:
                messages.error(request, 'Erreur dans le formulaire client. Veuillez vérifier vos réponses.')
                form_collaborateur = QuestionnaireCollaborateurForm(instance=questionnaire_collaborateur) if has_collaborateur else None

        elif form_type == 'collaborateur' and has_collaborateur:
            form_collaborateur = QuestionnaireCollaborateurForm(request.POST, instance=questionnaire_collaborateur)
            if form_collaborateur.is_valid():
                questionnaire = form_collaborateur.save(commit=False)
                questionnaire.collaborateur = request.user
                questionnaire.save()
                form_collaborateur.save_m2m()
                messages.success(request, 'Questionnaire collaborateur mis à jour avec succès.')
                return redirect('voir_questionnaire', siren=siren)
            else:
                messages.error(request, 'Erreur dans le formulaire collaborateur. Veuillez vérifier vos réponses.')
                form_client = QuestionnaireClientForm(instance=questionnaire_client) if has_client else None
        else:
            messages.error(request, 'Type de formulaire invalide.')
            return redirect('voir_questionnaire', siren=siren)
    else:
        # GET - afficher les formulaires
        form_client = QuestionnaireClientForm(instance=questionnaire_client) if has_client else None
        form_collaborateur = QuestionnaireCollaborateurForm(instance=questionnaire_collaborateur) if has_collaborateur else None

    context = {
        'entreprise': entreprise,
        'has_client': has_client,
        'has_collaborateur': has_collaborateur,
        'form_client': form_client,
        'form_collaborateur': form_collaborateur,
    }

    return render(request, 'questionnaires/collaborateur/editer_questionnaire.html', context)


def _get_csv_headers():
    """Retourne les en-têtes du CSV d'export"""
    return [
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
    ]


def _build_csv_row(entreprise, qc, qco):
    """
    Construit une ligne du CSV d'export

    Args:
        entreprise: Instance de Entreprise
        qc: Instance de QuestionnaireClient ou None
        qco: Instance de QuestionnaireCollaborateur ou None

    Returns:
        list: Ligne de données pour le CSV
    """
    return [
        entreprise.siren,
        entreprise.nom_entreprise,
        entreprise.date_creation.strftime('%d/%m/%Y %H:%M') if entreprise.date_creation else '',
        entreprise.date_modification.strftime('%d/%m/%Y %H:%M') if entreprise.date_modification else '',
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
    ]


@login_required
def export_csv(request):
    """Exporter toutes les entreprises et questionnaires en CSV"""
    # Créer la réponse CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="export_questionnaires.csv"'
    response.write('\ufeff')  # BOM UTF-8 pour Excel

    writer = csv.writer(response, delimiter=';')

    # En-têtes
    writer.writerow(_get_csv_headers())

    # Données
    entreprises = Entreprise.objects.filter(is_archived=False).select_related(
        'questionnaire_client',
        'questionnaire_collaborateur'
    )

    for entreprise in entreprises:
        qc = getattr(entreprise, 'questionnaire_client', None)
        qco = getattr(entreprise, 'questionnaire_collaborateur', None)
        writer.writerow(_build_csv_row(entreprise, qc, qco))

    return response
