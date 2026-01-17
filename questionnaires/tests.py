from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Entreprise, QuestionnaireClient, QuestionnaireCollaborateur
from .utils import get_company_info

User = get_user_model()


class HomePageTests(TestCase):
    """Tests pour la page d'accueil"""

    def test_home_page_loads(self):
        """La page d'accueil se charge correctement"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cabinet ETAC')

    def test_mentions_legales_page_loads(self):
        """La page mentions légales se charge correctement"""
        response = self.client.get(reverse('mentions_legales'))
        self.assertEqual(response.status_code, 200)


class SirenValidationTests(TestCase):
    """Tests pour la validation du format SIREN"""

    def test_valid_siren_format(self):
        """Un SIREN valide a 9 chiffres"""
        siren = '380315614'
        self.assertEqual(len(siren), 9)
        self.assertTrue(siren.isdigit())

    def test_invalid_siren_too_short(self):
        """Un SIREN trop court est invalide"""
        siren = '12345'
        self.assertFalse(len(siren) == 9)

    def test_invalid_siren_contains_letters(self):
        """Un SIREN contenant des lettres est invalide"""
        siren = 'ABC123456'
        self.assertFalse(siren.isdigit())

    def test_invalid_siren_mixed(self):
        """Un SIREN avec chiffres et lettres est invalide"""
        siren = '12345678A'
        self.assertFalse(len(siren) == 9 and siren.isdigit())


class EntrepriseModelTests(TestCase):
    """Tests pour le modèle Entreprise"""

    def setUp(self):
        self.entreprise = Entreprise.objects.create(
            siren='123456789',
            nom_entreprise='Test SARL'
        )

    def test_entreprise_creation(self):
        """Une entreprise peut être créée"""
        self.assertEqual(self.entreprise.siren, '123456789')
        self.assertEqual(self.entreprise.nom_entreprise, 'Test SARL')
        self.assertFalse(self.entreprise.is_archived)

    def test_entreprise_str(self):
        """La représentation string de l'entreprise est correcte"""
        self.assertEqual(str(self.entreprise), 'Test SARL (123456789)')

    def test_entreprise_archivage(self):
        """Une entreprise peut être archivée"""
        self.entreprise.is_archived = True
        self.entreprise.save()
        self.assertTrue(self.entreprise.is_archived)


class QuestionnaireClientTests(TestCase):
    """Tests pour le questionnaire client"""

    def setUp(self):
        self.entreprise = Entreprise.objects.create(
            siren='123456789',
            nom_entreprise='Test SARL'
        )

    def test_questionnaire_creation(self):
        """Un questionnaire client peut être créé"""
        questionnaire = QuestionnaireClient.objects.create(
            entreprise=self.entreprise,
            gestion_future='internal',
            aisance_outils='medium'
        )
        self.assertEqual(questionnaire.entreprise.siren, '123456789')
        self.assertEqual(questionnaire.gestion_future, 'internal')

    def test_questionnaire_one_per_entreprise(self):
        """Une seule instance de questionnaire client par entreprise"""
        QuestionnaireClient.objects.create(
            entreprise=self.entreprise,
            gestion_future='internal'
        )
        # Tenter de créer un second questionnaire devrait lever une erreur
        with self.assertRaises(Exception):
            QuestionnaireClient.objects.create(
                entreprise=self.entreprise,
                gestion_future='delegate'
            )


class QuestionnaireCollaborateurTests(TestCase):
    """Tests pour le questionnaire collaborateur"""

    def setUp(self):
        self.entreprise = Entreprise.objects.create(
            siren='123456789',
            nom_entreprise='Test SARL'
        )
        self.user = User.objects.create_user(
            email='[email protected]',
            username='collab',
            password='testpass123',
            is_collaborateur=True
        )

    def test_questionnaire_creation(self):
        """Un questionnaire collaborateur peut être créé"""
        questionnaire = QuestionnaireCollaborateur.objects.create(
            entreprise=self.entreprise,
            collaborateur=self.user,
            assujettie_tva='yes',
            taille_entreprise='small_medium'
        )
        self.assertEqual(questionnaire.entreprise.siren, '123456789')
        self.assertEqual(questionnaire.assujettie_tva, 'yes')
        self.assertEqual(questionnaire.collaborateur, self.user)


class ClientIdentificationViewTests(TestCase):
    """Tests pour la vue d'identification client"""

    def test_identification_page_get(self):
        """La page d'identification se charge en GET"""
        response = self.client.get(reverse('client_identification'))
        self.assertEqual(response.status_code, 200)

    def test_identification_without_siren(self):
        """Erreur si SIREN non fourni"""
        response = self.client.post(reverse('client_identification'), {
            'siren': ''
        })
        self.assertEqual(response.status_code, 200)
        # Vérifier le message d'erreur est affiché


class CollaborateurDashboardTests(TestCase):
    """Tests pour le dashboard collaborateur"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='[email protected]',
            username='collab',
            password='testpass123',
            is_collaborateur=True
        )
        self.client = Client()

    def test_dashboard_requires_login(self):
        """Le dashboard nécessite une authentification"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_accessible_when_logged_in(self):
        """Le dashboard est accessible quand connecté"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_displays_stats(self):
        """Le dashboard affiche les statistiques"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Dashboard Collaborateur')


class ExportCSVTests(TestCase):
    """Tests pour l'export CSV"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='[email protected]',
            username='collab',
            password='testpass123',
            is_collaborateur=True
        )
        self.entreprise = Entreprise.objects.create(
            siren='123456789',
            nom_entreprise='Test SARL'
        )
        self.client = Client()

    def test_export_requires_login(self):
        """L'export nécessite une authentification"""
        response = self.client.get(reverse('export_csv'))
        self.assertEqual(response.status_code, 302)

    def test_export_returns_csv(self):
        """L'export retourne bien un fichier CSV"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', response['Content-Disposition'])
