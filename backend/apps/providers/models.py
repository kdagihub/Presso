import uuid
from django.conf import settings  # type: ignore
from django.contrib.gis.db import models as gis_models  # type: ignore
from django.contrib.gis.geos import Point  # type: ignore
from django.contrib.gis.measure import Distance  # type: ignore
from django.db import models  # type: ignore
from django.db.models import Q  # type: ignore


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
    
    ville = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Ville",
        help_text="Ville du prestataire"
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


class ProviderAgency(models.Model):
    """
    Agence (local) appartenant à un prestataire.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='agencies',
        verbose_name="Prestataire"
    )

    name = models.CharField(max_length=200, verbose_name="Nom de l'agence")
    code = models.CharField(
        max_length=32,
        blank=True,
        verbose_name="Code agence",
        help_text="Identifiant court (optionnel)"
    )
    description = models.TextField(blank=True, verbose_name="Description")

    adresse = models.TextField(verbose_name="Adresse complète")
    ville = models.CharField(max_length=120, verbose_name="Ville")
    quartier = models.CharField(max_length=120, blank=True, verbose_name="Quartier / Commune")

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
    location = gis_models.PointField(
        blank=True,
        null=True,
        geography=True,
        srid=4326,
        verbose_name="Localisation"
    )

    contact_name = models.CharField(max_length=120, blank=True, verbose_name="Personne de contact")
    contact_phone = models.CharField(max_length=32, blank=True, verbose_name="Téléphone de contact")
    contact_email = models.EmailField(blank=True, verbose_name="Email de contact")

    opening_hours = models.JSONField(default=dict, blank=True, verbose_name="Horaires d'ouverture")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Métadonnées")

    is_default = models.BooleanField(
        default=False,
        verbose_name="Agence principale",
        help_text="Agence affichée par défaut pour la gestion"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")

    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name = "Agence"
        verbose_name_plural = "Agences"
        ordering = ['provider', 'name']
        indexes = [
            models.Index(fields=['provider', 'is_active']),
            models.Index(fields=['ville', 'quartier']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'code'],
                name='unique_agency_code_per_provider',
                condition=~Q(code__exact='')
            ),
            models.UniqueConstraint(
                fields=['provider'],
                condition=Q(is_default=True),
                name='unique_default_agency_per_provider'
            ),
        ]

    def __str__(self):
        return f"{self.provider.nom_commercial} - {self.name}"

    def save(self, *args, **kwargs):
        if self.latitude is not None and self.longitude is not None:
            self.location = Point(float(self.longitude), float(self.latitude))
        super().save(*args, **kwargs)


class ProviderStaff(models.Model):
    """
    Employés / gestionnaires rattachés à un prestataire (et éventuellement à une agence).
    """
    ROLE_CHOICES = [
        ('owner', 'Propriétaire'),
        ('manager', 'Manager'),
        ('operator', 'Opérateur'),
        ('delivery', 'Livreur'),
        ('custom', 'Rôle personnalisé'),
    ]

    STATUS_CHOICES = [
        ('invited', 'Invité'),
        ('active', 'Actif'),
        ('suspended', 'Suspendu'),
        ('revoked', 'Révoqué'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='staff_members',
        verbose_name="Prestataire"
    )
    agency = models.ForeignKey(
        ProviderAgency,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_members',
        verbose_name="Agence"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_assignments',
        verbose_name="Utilisateur",
        null=True,
        blank=True
    )

    system_role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='operator',
        verbose_name="Rôle système"
    )
    role = models.ForeignKey(
        'core.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_members',
        verbose_name="Rôle personnalisé"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='invited',
        verbose_name="Statut"
    )
    invited_email = models.EmailField(blank=True, verbose_name="Email d'invitation")
    invited_phone = models.CharField(max_length=32, blank=True, verbose_name="Téléphone d'invitation")
    invite_token = models.CharField(max_length=128, blank=True, verbose_name="Jeton d'invitation")
    invited_at = models.DateTimeField(blank=True, null=True, verbose_name="Invité le")
    activated_at = models.DateTimeField(blank=True, null=True, verbose_name="Activé le")
    last_seen_at = models.DateTimeField(blank=True, null=True, verbose_name="Dernière activité")

    notes = models.TextField(blank=True, verbose_name="Notes internes")

    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")

    class Meta:
        verbose_name = "Membre du staff"
        verbose_name_plural = "Staff du prestataire"
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'user'],
                condition=Q(user__isnull=False),
                name='unique_staff_user_per_provider',
            ),
        ]
        indexes = [
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['agency']),
            models.Index(fields=['system_role']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.provider.nom_commercial}"

    @property
    def is_owner(self) -> bool:
        return self.system_role == 'owner'

    def can_manage_orders(self) -> bool:
        if self.role:
            return self.role.has_permission('orders.manage')
        return self.system_role in {'owner', 'manager'}
