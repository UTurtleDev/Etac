from django.db import models
from django.conf import settings


class Entreprise(models.Model):
    """
    Modèle central - Clé = SIREN
    Toutes les données sont regroupées par SIREN
    """
    siren = models.CharField(
        max_length=9,
        unique=True,
        primary_key=True,
        verbose_name="SIREN"
    )
    nom_entreprise = models.CharField(
        max_length=255,
        verbose_name="Nom entreprise"
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    is_archived = models.BooleanField(
        default=False,
        verbose_name="Archivé"
    )

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"
        ordering = ['-date_modification']
        indexes = [
            models.Index(fields=['siren']),
            models.Index(fields=['nom_entreprise']),
        ]

    def __str__(self):
        return f"{self.nom_entreprise} ({self.siren})"


class QuestionnaireClient(models.Model):
    """Questionnaire rempli par les clients"""

    # Relation
    entreprise = models.OneToOneField(
        'Entreprise',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='questionnaire_client'
    )

    # === PARTIE 1 : ÉQUIPEMENT ACTUEL ===

    # 1.1 Logiciel facturation
    logiciel_facturation = models.BooleanField(default=False)
    logiciel_facturation_nom = models.CharField(max_length=255, blank=True)

    # 1.2 Format électronique
    CHOIX_OUI_NON_NSP = [
        ('yes', 'Oui'),
        ('no', 'Non'),
        ('dont_know', 'Je ne sais pas'),
    ]
    factures_format_electronique = models.CharField(
        max_length=20,
        choices=CHOIX_OUI_NON_NSP,
        blank=True
    )

    # 1.3 Logiciel devis
    logiciel_devis = models.BooleanField(default=False)
    logiciel_devis_nom = models.CharField(max_length=255, blank=True)

    # 1.4 Caisse enregistreuse
    CHOIX_CAISSE = [
        ('yes', 'Oui'),
        ('no', 'Non'),
        ('not_applicable', 'Non applicable'),
    ]
    caisse_enregistreuse = models.CharField(
        max_length=20,
        choices=CHOIX_CAISSE,
        blank=True
    )
    caisse_enregistreuse_nom = models.CharField(max_length=255, blank=True)

    # 1.5 Certification caisse
    caisse_certifiee = models.CharField(
        max_length=20,
        choices=CHOIX_OUI_NON_NSP,
        blank=True
    )

    # 1.6 Plateforme agréée
    plateforme_agreee = models.CharField(
        max_length=20,
        choices=CHOIX_OUI_NON_NSP,
        blank=True
    )
    plateforme_agreee_nom = models.CharField(max_length=255, blank=True)

    # === PARTIE 2 : GESTION FACTURATION ===

    CHOIX_GESTION = [
        ('internal', 'Gérer en interne avec accompagnement'),
        ('delegate', 'Déléguer au cabinet'),
        ('dont_know', 'Je ne sais pas, besoin de conseils'),
    ]
    gestion_future = models.CharField(
        max_length=20,
        choices=CHOIX_GESTION,
        blank=True
    )

    CHOIX_AISANCE = [
        ('very_comfortable', 'Très à l\'aise'),
        ('medium', 'Moyen'),
        ('not_comfortable', 'Pas du tout à l\'aise'),
    ]
    aisance_outils = models.CharField(
        max_length=20,
        choices=CHOIX_AISANCE,
        blank=True
    )

    # === PARTIE 3 : INFOS COMPLÉMENTAIRES ===

    CHOIX_RECEPTION_ACHATS = [
        ('paper', 'Principalement par courrier papier'),
        ('email', 'Principalement par email (PDF)'),
        ('mixed', 'Mix papier/email'),
        ('platform', 'Via plateforme dématérialisée'),
        ('other', 'Autre'),
    ]
    reception_factures_achats = models.CharField(
        max_length=20,
        choices=CHOIX_RECEPTION_ACHATS,
        blank=True
    )
    reception_achats_autre = models.CharField(max_length=255, blank=True)

    envoi_factures_ventes = models.CharField(
        max_length=20,
        choices=CHOIX_RECEPTION_ACHATS,  # Mêmes choix
        blank=True
    )
    envoi_ventes_autre = models.CharField(max_length=255, blank=True)

    CHOIX_CONSERVATION = [
        ('paper', 'Classement papier uniquement'),
        ('electronic', 'Archivage électronique uniquement'),
        ('mixed', 'Mix papier + électronique'),
        ('accounting_firm', 'Confié au cabinet comptable'),
    ]
    conservation_factures = models.CharField(
        max_length=20,
        choices=CHOIX_CONSERVATION,
        blank=True
    )

    # Accompagnement (CHOIX MULTIPLES → JSONField)
    accompagnement_souhaite = models.JSONField(
        default=list,
        blank=True,
        help_text="Liste des types d'accompagnement"
    )
    # Choix possibles: information, conseil, formation, parametrage,
    # gestion_complete, support, aucun, autre

    accompagnement_autre = models.CharField(max_length=255, blank=True)

    # Commentaires
    commentaires = models.TextField(blank=True)

    # Métadonnées
    date_completion = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    modifie_par_collaborateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questionnaires_client_modifies'
    )
    cookies_consent_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date acceptation cookies"
    )

    class Meta:
        verbose_name = "Questionnaire Client"
        verbose_name_plural = "Questionnaires Clients"

    def __str__(self):
        return f"Q. Client - {self.entreprise.nom_entreprise}"


class QuestionnaireCollaborateur(models.Model):
    """Questionnaire rempli par les collaborateurs"""

    # Relation
    entreprise = models.OneToOneField(
        'Entreprise',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='questionnaire_collaborateur'
    )

    # === ASSUJETTISSEMENT ET ACTIVITÉ ===

    CHOIX_TVA = [
        ('yes', 'Oui'),
        ('no', 'Non'),
        ('unsure', 'J\'ai un doute'),
    ]
    assujettie_tva = models.CharField(
        max_length=20,
        choices=CHOIX_TVA,
        blank=True
    )

    code_ape = models.CharField(max_length=10, blank=True)
    activite_precise = models.TextField(blank=True)

    CHOIX_TAILLE = [
        ('small_medium', 'TPE/PME'),
        ('mid_sized', 'ETI'),
        ('large', 'Grande entreprise'),
    ]
    taille_entreprise = models.CharField(
        max_length=20,
        choices=CHOIX_TAILLE,
        blank=True
    )

    CHOIX_REGIME_TVA = [
        ('franchise', 'Franchise en base'),
        ('simplified_real', 'Réel simplifié'),
        ('quarterly_real', 'Réel trimestriel'),
        ('monthly_real', 'Réel mensuel'),
    ]
    regime_tva = models.CharField(
        max_length=20,
        choices=CHOIX_REGIME_TVA,
        blank=True
    )

    CHOIX_ACTIVITE_EXONEREE = [
        ('health', 'Prestations santé'),
        ('education', 'Enseignement et formation'),
        ('real_estate', 'Opérations immobilières'),
        ('nonprofit', 'Associations à but non lucratif'),
        ('banking', 'Opérations bancaires et financières'),
        ('insurance', 'Opérations d\'assurance'),
        ('mixed', 'Activité mixte ou n\'exerce pas dans ces secteurs'),
    ]
    activite_exoneree_tva = models.CharField(
        max_length=20,
        choices=CHOIX_ACTIVITE_EXONEREE,
        blank=True
    )

    plateforme_agreee = models.BooleanField(default=False)
    plateforme_agreee_nom = models.CharField(max_length=255, blank=True)

    # === FLUX FACTURATION - VENTES ===

    CHOIX_NOMBRE = [
        ('less_than_50', 'Moins de 50'),
        ('between_50_200', 'Entre 50 et 200'),
        ('between_200_1000', 'Entre 200 et 1000'),
        ('between_1000_5000', 'Entre 1000 et 5000'),
        ('more_than_5000', 'Plus de 5000'),
        ('not_applicable', 'N/A'),
    ]
    nb_factures_ventes = models.CharField(
        max_length=20,
        choices=CHOIX_NOMBRE,
        blank=True
    )

    CHOIX_CLIENTS = [
        ('less_than_10', 'Moins de 10'),
        ('between_10_50', 'Entre 10 et 50'),
        ('between_50_200', 'Entre 50 et 200'),
        ('more_than_200', 'Plus de 200'),
        ('not_applicable', 'N/A'),
    ]
    nb_clients_actifs = models.CharField(
        max_length=20,
        choices=CHOIX_CLIENTS,
        blank=True
    )

    # Types de ventes (tableau Oui/Non)
    vente_btob_domestique = models.BooleanField(default=False)
    vente_btob_export = models.BooleanField(default=False)
    vente_btoc_facture = models.BooleanField(default=False)
    vente_btoc_caisse = models.BooleanField(default=False)

    # === FLUX FACTURATION - ACHATS ===

    nb_factures_achats = models.CharField(
        max_length=20,
        choices=CHOIX_NOMBRE,
        blank=True
    )
    nb_fournisseurs_actifs = models.CharField(
        max_length=20,
        choices=CHOIX_CLIENTS,
        blank=True
    )

    # Types d'achats
    achat_btob_domestique = models.BooleanField(default=False)
    achat_btob_intracommunautaire = models.BooleanField(default=False)
    achat_btob_hors_ue = models.BooleanField(default=False)

    # === INFORMATIONS COMPLÉMENTAIRES ===

    commentaires = models.TextField(blank=True)

    # Métadonnées
    collaborateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='questionnaires_crees'
    )
    date_completion = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    cookies_consent_date = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = "Questionnaire Collaborateur"
        verbose_name_plural = "Questionnaires Collaborateurs"

    def __str__(self):
        return f"Q. Collab - {self.entreprise.nom_entreprise}"
