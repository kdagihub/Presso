import uuid
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour Presso
    Hérite de AbstractUser et ajoute des champs spécifiques à la plateforme
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Validation du numéro de téléphone ivoirien
    phone_regex = RegexValidator(
        regex=r'^\+225\d{10}$|^\d{10}$',
        message="Le numéro doit être au format: '+225XXXXXXXXXX' ou 'XXXXXXXXXX'"
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=15,
        unique=True,
        verbose_name="Téléphone",
        help_text="Numéro de téléphone (format ivoirien)"
    )
    
    photo_profil = models.ImageField(
        upload_to='users/profils/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Photo de profil"
    )
    
    role = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Rôle personnalisé",
        help_text="Rôle spécifique (ex: fanico_express, pressing_premium)"
    )
    
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presso_users',
        verbose_name="Groupe"
    )
    
    date_inscription = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'inscription"
    )
    
    # Surcharger pour permettre login par phone/email/username
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'phone']
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['-date_inscription']
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.phone})"
    
    def get_role_display(self):
        """Retourne le rôle avec le groupe"""
        if self.group:
            return f"{self.group.name} - {self.role}" if self.role else self.group.name
        return self.role or "Aucun rôle"
