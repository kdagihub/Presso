import uuid
from django.conf import settings  # type: ignore
from django.db import models  # type: ignore
from django.utils import timezone  # type: ignore

from apps.providers.models import Provider, ProviderAgency, ProviderStaff


class Order(models.Model):
    """
    Modèle représentant une commande de lessive
    """
    STATUT_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('collected', 'Collectée'),
        ('in_progress', 'En cours'),
        ('ready', 'Prête'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Numéro de commande lisible
    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Numéro de commande",
        help_text="Généré automatiquement (ex: ORD-2024-0001)"
    )
    
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders_as_client',
        verbose_name="Client"
    )
    
    provider = models.ForeignKey(
        Provider,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name="Prestataire"
    )

    agency = models.ForeignKey(
        ProviderAgency,
        on_delete=models.SET_NULL,
        related_name='orders',
        null=True,
        blank=True,
        verbose_name="Agence assignée"
    )

    assigned_staff = models.ForeignKey(
        ProviderStaff,
        on_delete=models.SET_NULL,
        related_name='orders',
        null=True,
        blank=True,
        verbose_name="Staff assigné"
    )
    
    # Adresses
    adresse_collecte = models.TextField(
        verbose_name="Adresse de collecte"
    )
    
    latitude_collecte = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Latitude collecte"
    )
    
    longitude_collecte = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Longitude collecte"
    )
    
    adresse_livraison = models.TextField(
        verbose_name="Adresse de livraison"
    )
    
    latitude_livraison = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Latitude livraison"
    )
    
    longitude_livraison = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name="Longitude livraison"
    )
    
    # Créneaux
    creneau_collecte = models.DateTimeField(
        verbose_name="Créneau de collecte",
        help_text="Date et heure souhaitées pour la collecte"
    )
    
    creneau_livraison = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Créneau de livraison estimé"
    )
    
    # Dates réelles
    date_collecte = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de collecte réelle"
    )
    
    date_livraison = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de livraison réelle"
    )
    
    # Statut
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='pending',
        verbose_name="Statut"
    )

    statut_changed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Dernier changement de statut"
    )
    
    # Montants
    total_estime = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Total estimé (FCFA)"
    )
    
    total_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Total final (FCFA)",
        help_text="Montant réel après traitement"
    )
    
    frais_livraison = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Frais de livraison (FCFA)"
    )
    
    # Notes
    notes_client = models.TextField(
        blank=True,
        verbose_name="Notes du client",
        help_text="Instructions particulières"
    )
    
    notes_provider = models.TextField(
        blank=True,
        verbose_name="Notes du prestataire",
        help_text="Observations lors du traitement"
    )
    
    # Preuve de livraison
    preuve_livraison_url = models.URLField(
        blank=True,
        verbose_name="URL preuve de livraison",
        help_text="Signature ou photo de livraison"
    )
    
    signature_client = models.ImageField(
        upload_to='orders/signatures/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Signature client"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['client', 'statut']),
            models.Index(fields=['provider', 'statut']),
            models.Index(fields=['numero']),
        ]
    
    def __str__(self):
        return f"{self.numero} - {self.client.get_full_name()} ({self.get_statut_display()})"
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Générer un numéro de commande automatique
            year = timezone.now().year
            last_order = Order.objects.filter(
                numero__startswith=f'ORD-{year}-'
            ).order_by('-numero').first()
            
            if last_order:
                last_num = int(last_order.numero.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.numero = f'ORD-{year}-{new_num:04d}'

        if not self.statut_changed_at:
            self.statut_changed_at = timezone.now()
        
        super().save(*args, **kwargs)

    def log_status(
        self,
        *,
        event: str = 'status_change',
        new_status: str,
        previous_status: str | None = None,
        comment: str = '',
        performed_by=None,
    ) -> 'OrderStatusLog':
        if previous_status is None:
            previous_status = self.statut
        return OrderStatusLog.objects.create(
            order=self,
            event=event,
            previous_status=previous_status,
            new_status=new_status,
            comment=comment or '',
            performed_by=performed_by,
        )


class OrderStatusLog(models.Model):
    EVENT_CHOICES = [
        ('creation', 'Création'),
        ('status_change', 'Changement de statut'),
        ('assignment', 'Affectation'),
        ('note', 'Note'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_logs',
        verbose_name="Commande"
    )
    event = models.CharField(max_length=20, choices=EVENT_CHOICES, default='status_change')
    previous_status = models.CharField(
        max_length=20,
        choices=Order.STATUT_CHOICES,
        null=True,
        blank=True,
        verbose_name="Statut précédent",
    )
    new_status = models.CharField(
        max_length=20,
        choices=Order.STATUT_CHOICES,
        verbose_name="Nouveau statut",
    )
    comment = models.TextField(blank=True, verbose_name="Commentaire")
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Effectué par",
    )
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Métadonnées")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de l'action")

    class Meta:
        verbose_name = "Journal de statut"
        verbose_name_plural = "Journaux de statut"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['order', 'event']),
            models.Index(fields=['new_status']),
        ]

    def __str__(self):
        return f"{self.order.numero} - {self.get_event_display()} ({self.new_status})"
