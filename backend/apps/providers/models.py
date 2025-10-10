import uuid
from django.db import models
from django.conf import settings


class Provider(models.Model):
    """
    Modèle représentant un prestataire (Pressing ou Fanico)
    """
    TYPE_CHOICES = [
        ('pressing', 'Pressing'),
        ('fanico', 'Fanico'),
    ]
    
    STATUT_KYC_CHOICES = [
        ('pending', 'En attente'),
        ('verified', 'Vérifié'),
        ('rejected', 'Rejeté'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provider_profile',
        verbose_name="Utilisateur"
    )
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="Type de prestataire"
    )
    
    nom_commercial = models.CharField(
        max_length=200,
        verbose_name="Nom commercial",
        help_text="Nom de l'établissement ou du prestataire"
    )
    
    photo_local = models.ImageField(
        upload_to='providers/locaux/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Photo du local",
        help_text="Photo de l'établissement (facultatif pour fanico)"
    )
    
    zone_couverture = models.TextField(
        verbose_name="Zone de couverture",
        help_text="Quartiers ou communes desservis"
    )
    
    rayon_km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        verbose_name="Rayon de couverture (km)",
        help_text="Distance maximale de déplacement"
    )
    
    # Géolocalisation
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Latitude"
    )
    
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Longitude"
    )
    
    adresse = models.TextField(
        verbose_name="Adresse complète"
    )
    
    statut_kyc = models.CharField(
        max_length=20,
        choices=STATUT_KYC_CHOICES,
        default='pending',
        verbose_name="Statut KYC"
    )
    
    document_identite = models.FileField(
        upload_to='providers/kyc/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Document d'identité",
        help_text="CNI, Passeport, etc."
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Le prestataire peut recevoir des commandes"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Prestataire"
        verbose_name_plural = "Prestataires"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.nom_commercial} ({self.get_type_display()})"
