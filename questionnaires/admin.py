from django.contrib import admin
from .models import Entreprise, QuestionnaireClient, QuestionnaireCollaborateur


class QuestionnaireClientCabinetInline(admin.StackedInline):
    model = QuestionnaireClient
    fields = ('cabinet', 'collaborateur')
    extra = 0
    verbose_name = "Affectation"
    verbose_name_plural = "Affectation cabinet / collaborateur"
    can_delete = False


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    inlines = [QuestionnaireClientCabinetInline]
    list_display = ('siren', 'nom_entreprise', 'get_cabinet', 'get_collaborateur', 'date_creation', 'date_modification', 'is_archived')
    list_filter = ('is_archived', 'questionnaire_client__cabinet', 'questionnaire_client__collaborateur', 'date_creation', 'date_modification')
    search_fields = ('siren', 'nom_entreprise')
    ordering = ('-date_modification',)
    readonly_fields = ('date_creation', 'date_modification')

    fieldsets = (
        ('Informations entreprise', {
            'fields': ('siren', 'nom_entreprise')
        }),
        ('Statut', {
            'fields': ('is_archived',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Cabinet', ordering='questionnaire_client__cabinet__nom')
    def get_cabinet(self, obj):
        try:
            return obj.questionnaire_client.cabinet
        except Entreprise.questionnaire_client.RelatedObjectDoesNotExist:
            return '-'

    @admin.display(description='Collaborateur', ordering='questionnaire_client__collaborateur__last_name')
    def get_collaborateur(self, obj):
        try:
            return obj.questionnaire_client.collaborateur
        except Entreprise.questionnaire_client.RelatedObjectDoesNotExist:
            return '-'


@admin.register(QuestionnaireClient)
class QuestionnaireClientAdmin(admin.ModelAdmin):
    list_display = ('entreprise', 'date_completion', 'date_modification', 'modifie_par_collaborateur')
    list_filter = ('date_completion', 'date_modification', 'gestion_future', 'aisance_outils')
    search_fields = ('entreprise__siren', 'entreprise__nom_entreprise')
    readonly_fields = ('date_completion', 'date_modification')
    autocomplete_fields = ['entreprise']

    fieldsets = (
        ('Entreprise', {
            'fields': ('entreprise',)
        }),
        ('Partie 1 : Équipement actuel', {
            'fields': (
                'logiciel_facturation', 'logiciel_facturation_nom',
                'factures_format_electronique',
                'logiciel_devis', 'logiciel_devis_nom',
                'caisse_enregistreuse', 'caisse_enregistreuse_nom',
                'caisse_certifiee',
                'plateforme_agreee', 'plateforme_agreee_nom',
            )
        }),
        ('Partie 2 : Gestion facturation', {
            'fields': ('gestion_future', 'aisance_outils')
        }),
        ('Partie 3 : Informations complémentaires', {
            'fields': (
                'reception_factures_achats', 'reception_achats_autre',
                'envoi_factures_ventes', 'envoi_ventes_autre',
                'conservation_factures',
                'accompagnement_souhaite', 'accompagnement_autre',
                'commentaires',
            )
        }),
        ('Métadonnées', {
            'fields': ('date_completion', 'date_modification', 'modifie_par_collaborateur', 'cookies_consent_date'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuestionnaireCollaborateur)
class QuestionnaireCollaborateurAdmin(admin.ModelAdmin):
    list_display = ('entreprise', 'collaborateur', 'date_completion', 'date_modification', 'assujettie_tva')
    list_filter = ('date_completion', 'date_modification', 'assujettie_tva', 'taille_entreprise', 'regime_tva')
    search_fields = ('entreprise__siren', 'entreprise__nom_entreprise', 'code_ape')
    readonly_fields = ('date_completion', 'date_modification')
    autocomplete_fields = ['entreprise']

    fieldsets = (
        ('Entreprise', {
            'fields': ('entreprise', 'collaborateur')
        }),
        ('Assujettissement et activité', {
            'fields': (
                'assujettie_tva', 'code_ape', 'activite_precise',
                'taille_entreprise', 'regime_tva', 'activite_exoneree_tva',
                'plateforme_agreee', 'plateforme_agreee_nom',
            )
        }),
        ('Flux facturation - Ventes', {
            'fields': (
                'nb_factures_ventes', 'nb_clients_actifs',
                'vente_btob_domestique', 'vente_btob_export',
                'vente_btoc_facture', 'vente_btoc_caisse',
            )
        }),
        ('Flux facturation - Achats', {
            'fields': (
                'nb_factures_achats', 'nb_fournisseurs_actifs',
                'achat_btob_domestique', 'achat_btob_intracommunautaire',
                'achat_btob_hors_ue',
            )
        }),
        ('Informations complémentaires', {
            'fields': ('commentaires',)
        }),
        ('Métadonnées', {
            'fields': ('date_completion', 'date_modification', 'cookies_consent_date'),
            'classes': ('collapse',)
        }),
    )
