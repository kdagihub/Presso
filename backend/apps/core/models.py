import uuid
from django.db import models  # type: ignore
from django.conf import settings  # type: ignore


class Permission(models.Model):
    """
    Permissions granulaires pour le système multitenant
    Utilisé pour contrôler l'accès aux fonctionnalités
    """
    MODULE_CHOICES = [
        ('orders', 'Gestion des commandes'),
        ('services', 'Gestion des services'),
        ('tariffs', 'Gestion des tarifs'),
        ('stats', 'Statistiques'),
        ('staff', 'Gestion du personnel'),
        ('settings', 'Paramètres'),
        ('customers', 'Gestion clients'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Code",
        help_text="Ex: view_orders, manage_services, view_stats"
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name="Nom",
        help_text="Nom lisible de la permission"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    module = models.CharField(
        max_length=50,
        choices=MODULE_CHOICES,
        verbose_name="Module"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"
        ordering = ['module', 'code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['module', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Role(models.Model):
    """
    Rôles personnalisés créés par chaque prestataire
    Permet aux prestataires de définir leurs propres rôles avec permissions
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.CASCADE,
        related_name='custom_roles',
        verbose_name="Prestataire",
        help_text="Le prestataire qui a créé ce rôle"
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name="Nom du rôle",
        help_text="Ex: Manager, Opérateur, Comptable"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    permissions = models.ManyToManyField(
        Permission,
        related_name='roles',
        verbose_name="Permissions",
        blank=True
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Rôle personnalisé"
        verbose_name_plural = "Rôles personnalisés"
        unique_together = ['provider', 'name']
        ordering = ['provider', 'name']
    
    def __str__(self):
        return f"{self.provider.nom_commercial} - {self.name}"
    
    def has_permission(self, permission_code):
        """Vérifie si ce rôle a une permission spécifique"""
        return self.permissions.filter(code=permission_code, is_active=True).exists()


class ProviderSettings(models.Model):
    """
    Paramètres personnalisables par prestataire
    Configuration générale du tenant
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    provider = models.OneToOneField(
        'providers.Provider',
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name="Prestataire"
    )
    
    # Branding
    business_name = models.CharField(
        max_length=200,
        verbose_name="Nom commercial affiché",
        help_text="Nom affiché dans le dashboard"
    )
    
    logo = models.ImageField(
        upload_to='providers/logos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Logo"
    )
    
    primary_color = models.CharField(
        max_length=7,
        default='#3b82f6',
        verbose_name="Couleur principale",
        help_text="Format hex: #RRGGBB"
    )
    
    # Configuration opérationnelle
    auto_accept_orders = models.BooleanField(
        default=False,
        verbose_name="Acceptation automatique des commandes"
    )
    
    require_payment_before = models.BooleanField(
        default=False,
        verbose_name="Exiger le paiement avant traitement"
    )
    
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Montant minimum de commande (FCFA)"
    )
    
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Frais de livraison par défaut (FCFA)"
    )
    
    # Notifications
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifications par email"
    )
    
    sms_notifications = models.BooleanField(
        default=False,
        verbose_name="Notifications par SMS"
    )
    
    notification_email = models.EmailField(
        blank=True,
        verbose_name="Email de notification"
    )
    
    notification_phone = models.CharField(
        max_length=15,
        blank=True,
        verbose_name="Téléphone de notification"
    )
    
    # Horaires d'ouverture (JSON)
    opening_hours = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Horaires d'ouverture",
        help_text="Format JSON avec les horaires par jour"
    )
    
    # Métadonnées
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Paramètres supplémentaires en JSON"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Paramètres du prestataire"
        verbose_name_plural = "Paramètres des prestataires"
    
    def __str__(self):
        return f"Paramètres - {self.provider.nom_commercial}"


class TenantMixin(models.Model):
    """
    Mixin pour les modèles qui doivent être isolés par tenant (prestataire)
    À hériter pour tous les modèles tenant-specific
    """
    provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.CASCADE,
        verbose_name="Prestataire"
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['provider']),
        ]


class AuthEventLog(models.Model):
    """
    Journalisation des évènements d'authentification (login, OTP, reset, etc.).
    """
    event = models.CharField(max_length=64)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='auth_events',
    )
    phone_hash = models.CharField(max_length=128, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    success = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['event']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['phone_hash']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"AuthEvent<{self.event}:{'OK' if self.success else 'KO'}>"

