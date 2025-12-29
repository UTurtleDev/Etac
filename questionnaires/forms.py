from django import forms
from .models import QuestionnaireClient, QuestionnaireCollaborateur


class QuestionnaireClientForm(forms.ModelForm):
    """Formulaire pour le questionnaire client"""

    class Meta:
        model = QuestionnaireClient
        exclude = ['entreprise', 'date_completion', 'date_modification',
                   'modifie_par_collaborateur', 'cookies_consent_date']

        widgets = {
            # Text inputs
            'logiciel_facturation_nom': forms.TextInput(attrs={
                'placeholder': 'Nom du logiciel',
                'class': 'form-control'
            }),
            'logiciel_devis_nom': forms.TextInput(attrs={
                'placeholder': 'Nom du logiciel',
                'class': 'form-control'
            }),
            'caisse_enregistreuse_nom': forms.TextInput(attrs={
                'placeholder': 'Nom/Marque de la caisse',
                'class': 'form-control'
            }),
            'plateforme_agreee_nom': forms.TextInput(attrs={
                'placeholder': 'Nom de la plateforme',
                'class': 'form-control'
            }),
            'reception_achats_autre': forms.TextInput(attrs={
                'placeholder': 'Précisez',
                'class': 'form-control'
            }),
            'envoi_ventes_autre': forms.TextInput(attrs={
                'placeholder': 'Précisez',
                'class': 'form-control'
            }),
            'accompagnement_autre': forms.TextInput(attrs={
                'placeholder': 'Précisez',
                'class': 'form-control'
            }),

            # Textarea
            'commentaires': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Vos commentaires ou questions...',
                'class': 'form-control'
            }),

            # Radio buttons et select - Ajout de classes CSS
            'factures_format_electronique': forms.RadioSelect(),
            'caisse_enregistreuse': forms.RadioSelect(),
            'caisse_certifiee': forms.RadioSelect(),
            'plateforme_agreee': forms.RadioSelect(),
            'gestion_future': forms.RadioSelect(),
            'aisance_outils': forms.RadioSelect(),
            'reception_factures_achats': forms.RadioSelect(),
            'envoi_factures_ventes': forms.RadioSelect(),
            'conservation_factures': forms.RadioSelect(),
        }

        labels = {
            'logiciel_facturation': 'Utilisez-vous un logiciel de facturation ?',
            'logiciel_facturation_nom': 'Si oui, lequel ?',
            'factures_format_electronique': 'Vos factures sont-elles déjà au format électronique ?',
            'logiciel_devis': 'Utilisez-vous un logiciel de devis ?',
            'logiciel_devis_nom': 'Si oui, lequel ?',
            'caisse_enregistreuse': 'Utilisez-vous une caisse enregistreuse ?',
            'caisse_enregistreuse_nom': 'Si oui, quelle marque/modèle ?',
            'caisse_certifiee': 'Votre caisse est-elle certifiée conforme ?',
            'plateforme_agreee': 'Utilisez-vous une plateforme agréée pour la facturation ?',
            'plateforme_agreee_nom': 'Si oui, laquelle ?',
            'gestion_future': 'Comment souhaitez-vous gérer la facturation électronique ?',
            'aisance_outils': 'Quel est votre niveau d\'aisance avec les outils numériques ?',
            'reception_factures_achats': 'Comment recevez-vous actuellement vos factures d\'achats ?',
            'reception_achats_autre': 'Autre (précisez)',
            'envoi_factures_ventes': 'Comment envoyez-vous actuellement vos factures de ventes ?',
            'envoi_ventes_autre': 'Autre (précisez)',
            'conservation_factures': 'Comment conservez-vous vos factures ?',
            'accompagnement_souhaite': 'Quel type d\'accompagnement souhaitez-vous ?',
            'accompagnement_autre': 'Autre (précisez)',
            'commentaires': 'Commentaires ou questions supplémentaires',
        }


class QuestionnaireCollaborateurForm(forms.ModelForm):
    """Formulaire pour le questionnaire collaborateur"""

    class Meta:
        model = QuestionnaireCollaborateur
        exclude = ['entreprise', 'collaborateur', 'date_completion',
                   'date_modification', 'cookies_consent_date']

        widgets = {
            # Text inputs
            'code_ape': forms.TextInput(attrs={
                'placeholder': 'Ex: 62.01Z',
                'class': 'form-control'
            }),
            'plateforme_agreee_nom': forms.TextInput(attrs={
                'placeholder': 'Nom de la plateforme',
                'class': 'form-control'
            }),

            # Textarea
            'activite_precise': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Décrivez précisément l\'activité de l\'entreprise...',
                'class': 'form-control'
            }),
            'commentaires': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Observations complémentaires...',
                'class': 'form-control'
            }),

            # Radio buttons
            'assujettie_tva': forms.RadioSelect(),
            'taille_entreprise': forms.RadioSelect(),
            'regime_tva': forms.RadioSelect(),
            'activite_exoneree_tva': forms.RadioSelect(),
            'nb_factures_ventes': forms.RadioSelect(),
            'nb_clients_actifs': forms.RadioSelect(),
            'nb_factures_achats': forms.RadioSelect(),
            'nb_fournisseurs_actifs': forms.RadioSelect(),
        }

        labels = {
            'assujettie_tva': 'L\'entreprise est-elle assujettie à la TVA ?',
            'code_ape': 'Code APE (NAF)',
            'activite_precise': 'Description précise de l\'activité',
            'taille_entreprise': 'Taille de l\'entreprise',
            'regime_tva': 'Régime de TVA',
            'activite_exoneree_tva': 'Secteur d\'activité (exonération TVA)',
            'plateforme_agreee': 'Utilise une plateforme de dématérialisation agréée',
            'plateforme_agreee_nom': 'Si oui, laquelle ?',
            'nb_factures_ventes': 'Nombre de factures de ventes par an',
            'nb_clients_actifs': 'Nombre de clients actifs',
            'vente_btob_domestique': 'Ventes B2B France',
            'vente_btob_export': 'Ventes B2B Export (hors UE)',
            'vente_btoc_facture': 'Ventes B2C avec facture',
            'vente_btoc_caisse': 'Ventes B2C avec ticket de caisse',
            'nb_factures_achats': 'Nombre de factures d\'achats par an',
            'nb_fournisseurs_actifs': 'Nombre de fournisseurs actifs',
            'achat_btob_domestique': 'Achats B2B France',
            'achat_btob_intracommunautaire': 'Achats B2B intracommunautaires (UE)',
            'achat_btob_hors_ue': 'Achats B2B hors UE',
            'commentaires': 'Observations et informations complémentaires',
        }
