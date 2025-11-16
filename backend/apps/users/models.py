import uuid
from django.contrib.auth.models import AbstractUser, Group
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé pour Presso
    Hérite de AbstractUser et ajoute des champs spécifiques à la plateforme
    Inclut la géolocalisation pour les clients
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
    
    phone_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Téléphone vérifié le",
        help_text="Date et heure de vérification du numéro de téléphone"
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
    
    custom_role = models.ForeignKey(
        'core.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name="Rôle personnalisé",
        help_text="Rôle créé par le prestataire avec permissions granulaires"
    )
    
    # Géolocalisation (pour les clients)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Latitude",
        help_text="Position GPS du client"
    )
    
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Longitude",
        help_text="Position GPS du client"
    )
    
    location = gis_models.PointField(
        blank=True,
        null=True,
        verbose_name="Localisation",
        help_text="Point géographique (généré automatiquement depuis lat/lng)",
        geography=True,
        srid=4326  # WGS84
    )
    
    adresse = models.TextField(
        blank=True,
        verbose_name="Adresse",
        help_text="Adresse complète du client"
    )
    
    quartier = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Quartier/Commune"
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
        if self.custom_role:
            return f"{self.custom_role.provider.nom_commercial} - {self.custom_role.name}"
        if self.group:
            return f"{self.group.name} - {self.role}" if self.role else self.group.name
        return self.role or "Aucun rôle"
    
    def has_custom_permission(self, permission_code):
        """Vérifie si l'utilisateur a une permission spécifique via son rôle personnalisé"""
        if self.is_superuser:
            return True
        if self.custom_role and self.custom_role.is_active:
            return self.custom_role.has_permission(permission_code)
        return False
    
    def get_provider(self):
        """Retourne le prestataire associé à cet utilisateur"""
        if hasattr(self, 'provider_profile'):
            return self.provider_profile
        if self.custom_role:
            return self.custom_role.provider
        return None
    
    def is_phone_verified(self):
        """Vérifie si le numéro de téléphone a été vérifié"""
        return self.phone_verified_at is not None
    
    def mark_phone_verified(self):
        """Marque le téléphone comme vérifié"""
        from django.utils import timezone
        if not self.phone_verified_at:
            self.phone_verified_at = timezone.now()
            self.save(update_fields=['phone_verified_at'])
    
    def save(self, *args, **kwargs):
        """Créer automatiquement le Point GeoDjango depuis latitude/longitude"""
        if self.latitude is not None and self.longitude is not None:
            self.location = Point(float(self.longitude), float(self.latitude))
        super().save(*args, **kwargs)
    
    def get_nearby_providers(self, max_distance_km=10, provider_type=None):
        """
        Retourne les prestataires dans un rayon donné
        
        Args:
            max_distance_km: Distance maximale en km (défaut: 10km)
            provider_type: 'pressing' ou 'fanico' (optionnel)
        
        Returns:
            QuerySet de prestataires triés par distance
        """
        from apps.providers.models import Provider
        
        if not self.location:
            return Provider.objects.none()
        
        queryset = Provider.objects.filter(
            location__isnull=False,
            is_active=True,
            statut_kyc='verified'
        ).filter(
            location__distance_lte=(self.location, Distance(km=max_distance_km))
        )
        
        if provider_type:
            queryset = queryset.filter(type=provider_type)
        
        # Annoter avec la distance et trier
        return queryset.annotate(
            distance=gis_models.functions.Distance('location', self.location)
        ).order_by('distance')
    
    def calculate_distance_to(self, provider):
        """
        Calcule la distance en km entre le user et un prestataire
        
        Args:
            provider: Instance de Provider
        
        Returns:
            Distance en km (float) ou None
        """
        if not self.location or not provider.location:
            return None
        
        distance = self.location.distance(provider.location) * 100  # Convertir en km
        return round(distance, 2)
