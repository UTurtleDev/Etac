from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user pour les collaborateurs du cabinet ETAC"""

    email = models.EmailField(
        unique=True,
        verbose_name="Email"
    )

    is_collaborateur = models.BooleanField(
        default=False,
        help_text="Collaborateur du cabinet ETAC"
    )

    # Email comme identifiant
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.get_full_name()} ({self.email})"
        return self.email
