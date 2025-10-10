import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.providers.models import Provider
from apps.orders.models import Order


class Review(models.Model):
    """
    Modèle d'avis client sur un prestataire
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given',
        verbose_name="Client"
    )
    
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name="Prestataire"
    )
    
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name="Commande",
        help_text="Un avis par commande"
    )
    
    note = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note",
        help_text="Note de 1 à 5 étoiles"
    )
    
    commentaire = models.TextField(
        blank=True,
        verbose_name="Commentaire"
    )
    
    # Critères détaillés (optionnel)
    note_qualite = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note qualité"
    )
    
    note_delai = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note respect des délais"
    )
    
    note_service = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Note service client"
    )
    
    # Modération
    is_approved = models.BooleanField(
        default=True,
        verbose_name="Approuvé",
        help_text="L'avis est visible publiquement"
    )
    
    is_flagged = models.BooleanField(
        default=False,
        verbose_name="Signalé",
        help_text="L'avis a été signalé pour modération"
    )
    
    # Réponse du prestataire
    reponse_provider = models.TextField(
        blank=True,
        verbose_name="Réponse du prestataire"
    )
    
    date_reponse = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de réponse"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['provider', 'is_approved']),
            models.Index(fields=['client']),
        ]
    
    def __str__(self):
        return f"{self.client.get_full_name()} → {self.provider.nom_commercial} ({self.note}/5)"
