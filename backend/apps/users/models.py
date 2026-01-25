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


# =============================================================================
# TOKENS FCM (Push Notifications)
# =============================================================================

class UserFCMToken(models.Model):
    """
    Stocke les tokens FCM (Firebase Cloud Messaging) des utilisateurs.
    Un utilisateur peut avoir plusieurs tokens (un par device/navigateur).
    
    Utilisé pour envoyer des notifications push sur :
    - Web (Vue.js via Service Worker)
    - Mobile (Flutter Android/iOS)
    """
    DEVICE_TYPE_CHOICES = [
        ('web', 'Navigateur Web'),
        ('android', 'Android'),
        ('ios', 'iOS'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fcm_tokens',
        verbose_name="Utilisateur"
    )
    
    token = models.CharField(
        max_length=500,
        unique=True,
        verbose_name="Token FCM",
        help_text="Token unique généré par Firebase pour ce device"
    )
    
    device_type = models.CharField(
        max_length=20,
        choices=DEVICE_TYPE_CHOICES,
        default='web',
        verbose_name="Type de device"
    )
    
    device_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nom du device",
        help_text="Ex: Chrome sur Windows, iPhone 15, Samsung Galaxy S24"
    )
    
    device_info = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Informations device",
        help_text="User-Agent, OS, version navigateur, etc."
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="False si le token est invalide ou révoqué"
    )
    
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière utilisation",
        help_text="Dernière notification envoyée avec succès"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date d'enregistrement")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Token FCM"
        verbose_name_plural = "Tokens FCM"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token']),
            models.Index(fields=['device_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_device_type_display()} ({self.device_name or 'Sans nom'})"
    
    def mark_used(self):
        """Met à jour la date de dernière utilisation"""
        from django.utils import timezone
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at', 'updated'])
    
    def deactivate(self):
        """Désactive le token (ex: si Firebase le rejette)"""
        self.is_active = False
        self.save(update_fields=['is_active', 'updated'])
    
    @classmethod
    def get_active_tokens_for_user(cls, user_id: str) -> list:
        """Retourne tous les tokens actifs d'un utilisateur"""
        return list(
            cls.objects.filter(user_id=user_id, is_active=True)
            .values_list('token', flat=True)
        )
    
    @classmethod
    def register_token(
        cls,
        user,
        token: str,
        device_type: str = 'web',
        device_name: str = '',
        device_info: dict = None
    ) -> 'UserFCMToken':
        """
        Enregistre ou met à jour un token FCM.
        Si le token existe déjà pour un autre user, il est transféré.
        """
        # Vérifier si le token existe déjà
        existing = cls.objects.filter(token=token).first()
        
        if existing:
            # Token existe - le mettre à jour et l'activer
            existing.user = user
            existing.device_type = device_type
            existing.device_name = device_name
            existing.device_info = device_info or {}
            existing.is_active = True
            existing.save()
            return existing
        
        # Nouveau token
        return cls.objects.create(
            user=user,
            token=token,
            device_type=device_type,
            device_name=device_name,
            device_info=device_info or {}
        )


# =============================================================================
# PRÉFÉRENCES DE NOTIFICATION (CLIENTS)
# =============================================================================

class UserNotificationPreferences(models.Model):
    """
    Préférences de notification pour les utilisateurs (clients).
    Les prestataires utilisent ProviderSettings.
    
    Créé automatiquement à l'inscription du client.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name="Utilisateur"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # CANAUX DE NOTIFICATION
    # ═══════════════════════════════════════════════════════════════════
    
    push_enabled = models.BooleanField(
        default=True,
        verbose_name="Notifications push",
        help_text="Notifications sur l'appareil"
    )
    
    email_enabled = models.BooleanField(
        default=True,
        verbose_name="Notifications email"
    )
    
    sms_enabled = models.BooleanField(
        default=False,
        verbose_name="Notifications SMS",
        help_text="SMS pour événements critiques uniquement"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # TYPES DE NOTIFICATIONS
    # ═══════════════════════════════════════════════════════════════════
    
    notify_order_confirmations = models.BooleanField(
        default=True,
        verbose_name="Confirmations de commande",
        help_text="Quand une commande est passée"
    )
    
    notify_order_updates = models.BooleanField(
        default=True,
        verbose_name="Mises à jour commandes",
        help_text="Changements de statut"
    )
    
    notify_delivery = models.BooleanField(
        default=True,
        verbose_name="Livraisons",
        help_text="Notifications de livraison et OTP"
    )
    
    notify_payments = models.BooleanField(
        default=True,
        verbose_name="Paiements",
        help_text="Confirmations de paiement"
    )
    
    notify_promotions = models.BooleanField(
        default=False,
        verbose_name="Promotions",
        help_text="Offres et promotions (optionnel)"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTADONNÉES
    # ═══════════════════════════════════════════════════════════════════
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Préférences de notification"
        verbose_name_plural = "Préférences de notification"
    
    def __str__(self):
        return f"Préférences notification - {self.user.username}"
    
    @classmethod
    def get_or_create_for_user(cls, user) -> 'UserNotificationPreferences':
        """Récupère ou crée les préférences pour un utilisateur"""
        prefs, created = cls.objects.get_or_create(user=user)
        return prefs
    
    def should_notify(self, notification_type: str, channel: str) -> bool:
        """
        Vérifie si l'utilisateur doit recevoir une notification.
        
        Args:
            notification_type: 'order_confirmation', 'order_update', 'delivery', 'payment', 'promotion'
            channel: 'push', 'email', 'sms'
        
        Returns:
            bool: True si la notification doit être envoyée
        """
        # Vérifier le canal
        channel_enabled = {
            'push': self.push_enabled,
            'email': self.email_enabled,
            'sms': self.sms_enabled,
        }.get(channel, False)
        
        if not channel_enabled:
            return False
        
        # Vérifier le type
        type_enabled = {
            'order_confirmation': self.notify_order_confirmations,
            'order_update': self.notify_order_updates,
            'delivery': self.notify_delivery,
            'payment': self.notify_payments,
            'promotion': self.notify_promotions,
        }.get(notification_type, True)
        
        return type_enabled
