from django.contrib.auth.models import AbstractUser
from django.db import models


class Cabinet(models.Model):
    nom = models.CharField(max_length=255, verbose_name="Nom du cabinet")

    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Cabinet"
        verbose_name_plural = "Cabinets"


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

    cabinets = models.ManyToManyField(
        Cabinet,
        blank=True,
        related_name="Comptables",
        verbose_name="Cabinets"
    )

    # Email comme identifiant
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.get_full_name()} ({self.email})"
        return self.email
