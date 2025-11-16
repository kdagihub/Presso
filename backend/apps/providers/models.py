import uuid
from django.db import models
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance


class Provider(models.Model):
    """
    Modèle représentant un prestataire (Pressing ou Fanico)
    """
    TYPE_CHOICES = [
        ('pressing', 'Pressing'),
        ('laverie', 'Laverie'),
        ('blanchisserie', 'Blanchisserie'),
        ('fanico', 'Fanico'),
        ('pressing_chaussures', 'Pressing de chaussures'),
        ('nettoyage', 'Nettoyage'),
        ('autre', 'Autre'),
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
        verbose_name="Latitude",
        help_text="Position GPS du prestataire"
    )
    
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Longitude",
        help_text="Position GPS du prestataire"
    )
    
    location = gis_models.PointField(
        blank=True,
        null=True,
        verbose_name="Localisation",
        help_text="Point géographique (généré automatiquement depuis lat/lng)",
        geography=True,
        srid=4326  # WGS84 - Standard mondial GPS
    )
    
    adresse = models.TextField(
        verbose_name="Adresse complète"
    )
    
    quartier = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Quartier/Commune"
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
    
    def save(self, *args, **kwargs):
        """Créer automatiquement le Point GeoDjango depuis latitude/longitude"""
        if self.latitude is not None and self.longitude is not None:
            self.location = Point(float(self.longitude), float(self.latitude))
        super().save(*args, **kwargs)
    
    @staticmethod
    def find_nearby(latitude, longitude, max_distance_km=10, provider_type=None):
        """
        Trouve les prestataires proches d'une position donnée
        
        Args:
            latitude: Latitude de recherche
            longitude: Longitude de recherche
            max_distance_km: Distance maximale en km
            provider_type: 'pressing' ou 'fanico' (optionnel)
        
        Returns:
            QuerySet de prestataires triés par distance
        """
        point = Point(float(longitude), float(latitude))
        
        queryset = Provider.objects.filter(
            location__isnull=False,
            is_active=True,
            statut_kyc='verified'
        ).filter(
            location__distance_lte=(point, Distance(km=max_distance_km))
        )
        
        if provider_type:
            queryset = queryset.filter(type=provider_type)
        
        # Annoter avec la distance et trier
        return queryset.annotate(
            distance=gis_models.functions.Distance('location', point)
        ).order_by('distance')
    
    def get_clients_in_coverage(self):
        """
        Retourne les clients dans la zone de couverture du prestataire
        
        Returns:
            QuerySet d'utilisateurs clients dans le rayon
        """
        from apps.users.models import User
        
        if not self.location:
            return User.objects.none()
        
        return User.objects.filter(
            location__isnull=False,
            group__name='client'
        ).filter(
            location__distance_lte=(self.location, Distance(km=float(self.rayon_km)))
        ).annotate(
            distance=gis_models.functions.Distance('location', self.location)
        ).order_by('distance')
    
    def is_within_range(self, user_or_point, tolerance_km=0):
        """
        Vérifie si un utilisateur ou point est dans le rayon de couverture
        
        Args:
            user_or_point: Instance User ou Point GeoDjango
            tolerance_km: Tolérance supplémentaire en km (défaut: 0)
        
        Returns:
            Boolean
        """
        if not self.location:
            return False
        
        if hasattr(user_or_point, 'location'):
            # C'est un User
            if not user_or_point.location:
                return False
            target_location = user_or_point.location
        else:
            # C'est un Point
            target_location = user_or_point
        
        max_distance = float(self.rayon_km) + tolerance_km
        distance_m = self.location.distance(target_location) * 1000  # Convertir en mètres
        distance_km = distance_m / 1000
        
        return distance_km <= max_distance
