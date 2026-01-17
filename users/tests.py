from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTests(TestCase):
    """Tests pour le modèle User personnalisé"""

    def test_create_user(self):
        """Un utilisateur peut être créé"""
        user = User.objects.create_user(
            email='[email protected]',
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(user.email, '[email protected]')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_collaborateur)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_collaborateur(self):
        """Un collaborateur peut être créé"""
        user = User.objects.create_user(
            email='[email protected]',
            username='collab',
            password='testpass123',
            is_collaborateur=True
        )
        self.assertTrue(user.is_collaborateur)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        """Un superutilisateur peut être créé"""
        user = User.objects.create_superuser(
            email='[email protected]',
            username='admin',
            password='adminpass123'
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        # Note: is_collaborateur n'est pas forcément True pour un superuser

    def test_email_required(self):
        """L'email peut être vide (username est utilisé comme fallback)"""
        # Django permet de créer un user sans email si username est fourni
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')

    def test_user_str(self):
        """La représentation string de l'utilisateur est l'email"""
        user = User.objects.create_user(
            email='[email protected]',
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(str(user), '[email protected]')
