import uuid
from django.db import models
from apps.orders.models import Order


class Payment(models.Model):
    """
    Modèle de paiement pour suivre les transactions Mobile Money
    """
    OPERATEUR_CHOICES = [
        ('orange', 'Orange Money'),
        ('mtn', 'MTN Mobile Money'),
        ('moov', 'Moov Money'),
        ('wave', 'Wave'),
    ]
    
    STATUT_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
        ('cancelled', 'Annulé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name="Commande"
    )
    
    reference = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Référence de paiement",
        help_text="Référence unique du paiement"
    )
    
    operateur = models.CharField(
        max_length=20,
        choices=OPERATEUR_CHOICES,
        verbose_name="Opérateur Mobile Money"
    )
    
    numero_payeur = models.CharField(
        max_length=15,
        verbose_name="Numéro du payeur"
    )
    
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant (FCFA)"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    
    # Référence externe de l'opérateur
    transaction_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="ID de transaction externe",
        help_text="ID fourni par l'opérateur Mobile Money"
    )
    
    # Métadonnées
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Données supplémentaires de la transaction"
    )
    
    # Messages d'erreur
    error_message = models.TextField(
        blank=True,
        verbose_name="Message d'erreur"
    )
    
    # Dates
    date_initiation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'initiation"
    )
    
    date_completion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de finalisation"
    )
    
    # Remboursement
    is_refund = models.BooleanField(
        default=False,
        verbose_name="Est un remboursement"
    )
    
    refund_of = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='refunds',
        verbose_name="Remboursement de"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['order', 'statut']),
            models.Index(fields=['reference']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.reference} - {self.montant} FCFA ({self.get_statut_display()})"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            # Générer une référence unique
            import time
            timestamp = int(time.time() * 1000)
            self.reference = f'PAY-{timestamp}-{str(self.id)[:8].upper()}'
        
        super().save(*args, **kwargs)
