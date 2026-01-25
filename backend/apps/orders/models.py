import uuid
import secrets
from decimal import Decimal
from django.conf import settings  # type: ignore
from django.db import models  # type: ignore
from django.utils import timezone  # type: ignore

from apps.providers.models import Provider, ProviderAgency, ProviderStaff


class Order(models.Model):
    """
    Modèle représentant une commande de lessive.
    
    Workflow MVP simplifié :
    1. pending → Client passe commande
    2. confirmed → Prestataire accepte
    3. collected → Linge récupéré chez le client
    4. in_progress → En cours de traitement
    5. ready → Prêt pour livraison
    6. delivered → Livré (OTP validé) → Payout programmé
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
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('escrow', 'En séquestre'),
        ('released', 'Libéré'),
        ('refunded', 'Remboursé'),
        ('failed', 'Échoué'),
    ]
    
    PAYOUT_STATUS_CHOICES = [
        ('not_applicable', 'Non applicable'),
        ('pending', 'En attente'),
        ('scheduled', 'Programmé'),
        ('processing', 'En cours'),
        ('completed', 'Envoyé'),
        ('failed', 'Échoué'),
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
    
    # ═══════════════════════════════════════════════════════════════════
    # PAIEMENT CLIENT
    # ═══════════════════════════════════════════════════════════════════
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name="Statut paiement client"
    )
    
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Méthode de paiement",
        help_text="orange_money, mtn_momo, wave, etc."
    )
    
    moneroo_payment_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="ID Paiement Moneroo"
    )
    
    paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Payé le"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # COMMISSION & MONTANTS CALCULÉS
    # ═══════════════════════════════════════════════════════════════════
    
    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.00'),
        verbose_name="Commission appliquée (%)"
    )
    
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant commission (FCFA)"
    )
    
    payout_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Frais payout Moneroo (FCFA)"
    )
    
    provider_net_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant net prestataire (FCFA)",
        help_text="Total - Commission - Frais Moneroo"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # OTP LIVRAISON (Validation par le client)
    # ═══════════════════════════════════════════════════════════════════
    
    delivery_otp = models.CharField(
        max_length=6,
        blank=True,
        verbose_name="Code OTP livraison",
        help_text="Code à 6 chiffres pour valider la livraison"
    )
    
    delivery_otp_generated_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="OTP généré le"
    )
    
    delivery_otp_validated_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="OTP validé le"
    )
    
    delivery_otp_validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='validated_deliveries',
        verbose_name="OTP validé par"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # PAYOUT PRESTATAIRE (Virement automatique)
    # ═══════════════════════════════════════════════════════════════════
    
    payout_status = models.CharField(
        max_length=20,
        choices=PAYOUT_STATUS_CHOICES,
        default='not_applicable',
        verbose_name="Statut payout prestataire"
    )
    
    payout_scheduled_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Payout programmé pour",
        help_text="Date/heure du virement automatique (après délai)"
    )
    
    payout_completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Payout envoyé le"
    )
    
    moneroo_payout_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="ID Payout Moneroo"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # RAISON D'ANNULATION / REFUS
    # ═══════════════════════════════════════════════════════════════════
    
    cancellation_reason = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Raison d'annulation",
        help_text="Code raison: too_busy, machine_down, client_request, etc."
    )
    
    cancellation_notes = models.TextField(
        blank=True,
        verbose_name="Notes d'annulation"
    )
    
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='cancelled_orders',
        verbose_name="Annulé par"
    )
    
    cancelled_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Annulé le"
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
            models.Index(fields=['payment_status']),
            models.Index(fields=['payout_status']),
            models.Index(fields=['payout_scheduled_at', 'payout_status']),
            models.Index(fields=['delivery_otp_validated_at']),
        ]
    
    def __str__(self):
        return f"{self.numero} - {self.client.get_full_name()} ({self.get_statut_display()})"
    
    @staticmethod
    def generate_order_number() -> str:
        """
        Génère un numéro de commande court, unique et facile à communiquer.
        
        Format: #LLNNNNN (8 caractères)
        - # : Préfixe visuel
        - LL : 2 lettres aléatoires (évite les voyelles pour éviter les mots)
        - NNNNN : 5 chiffres aléatoires
        
        Exemple: #BK47291
        
        Probabilité de collision: 1 sur 21^2 * 10^5 = ~4.4 millions
        Suffisant pour des milliers de commandes/jour.
        
        Note: L'UUID technique est déjà dans le champ `id` pour les opérations internes.
        """
        # Consonnes uniquement (évite les voyelles pour ne pas former de mots gênants)
        consonants = 'BCDFGHJKLMNPQRSTVWXZ'
        letters = ''.join(secrets.choice(consonants) for _ in range(2))
        numbers = ''.join(str(secrets.randbelow(10)) for _ in range(5))
        
        return f'#{letters}{numbers}'
    
    def save(self, *args, **kwargs):
        if not self.numero:
            # Générer un numéro de commande unique
            for _ in range(100):  # Max 100 tentatives (collision très rare)
                numero = self.generate_order_number()
                if not Order.objects.filter(numero=numero).exists():
                    self.numero = numero
                    break
            else:
                # Fallback avec UUID court si trop de collisions
                self.numero = f'#{uuid.uuid4().hex[:7].upper()}'

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
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTHODES OTP LIVRAISON
    # ═══════════════════════════════════════════════════════════════════
    
    def generate_delivery_otp(self) -> str:
        """
        Génère un nouveau code OTP à 6 chiffres pour la livraison.
        Le client reçoit ce code et doit le donner au livreur.
        """
        self.delivery_otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        self.delivery_otp_generated_at = timezone.now()
        self.delivery_otp_validated_at = None
        self.delivery_otp_validated_by = None
        self.save(update_fields=[
            'delivery_otp', 
            'delivery_otp_generated_at',
            'delivery_otp_validated_at',
            'delivery_otp_validated_by',
            'updated'
        ])
        return self.delivery_otp
    
    def validate_delivery_otp(self, code: str, validated_by=None) -> bool:
        """
        Valide le code OTP de livraison.
        Retourne True si valide, False sinon.
        """
        from apps.core.models import PlatformSettings
        
        if not self.delivery_otp or not code:
            return False
        
        if self.delivery_otp != code:
            return False
        
        # Vérifier si l'OTP n'a pas expiré
        if self.delivery_otp_generated_at:
            try:
                platform = PlatformSettings.objects.first()
                validity_minutes = platform.delivery_otp_validity_minutes if platform else 60
            except Exception:
                validity_minutes = 60
            
            expiry_time = self.delivery_otp_generated_at + timezone.timedelta(minutes=validity_minutes)
            if timezone.now() > expiry_time:
                return False
        
        # Marquer comme validé
        self.delivery_otp_validated_at = timezone.now()
        self.delivery_otp_validated_by = validated_by
        self.save(update_fields=[
            'delivery_otp_validated_at',
            'delivery_otp_validated_by',
            'updated'
        ])
        return True
    
    def is_delivery_otp_valid(self) -> bool:
        """Vérifie si l'OTP de livraison a été validé"""
        return self.delivery_otp_validated_at is not None
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTHODES CALCUL MONTANTS
    # ═══════════════════════════════════════════════════════════════════
    
    def calculate_amounts(self, save: bool = True) -> dict:
        """
        Calcule la commission, les frais et le montant net du prestataire.
        Utilise les paramètres de la plateforme.
        """
        from apps.core.models import PlatformSettings
        
        try:
            platform = PlatformSettings.objects.first()
            if platform:
                self.commission_percent = platform.commission_percent
                collect_fee_percent = platform.collect_fee_percent
                payout_fee_percent = platform.payout_fee_percent
            else:
                self.commission_percent = Decimal('3.00')
                collect_fee_percent = Decimal('3.00')
                payout_fee_percent = Decimal('1.50')
        except Exception:
            self.commission_percent = Decimal('3.00')
            collect_fee_percent = Decimal('3.00')
            payout_fee_percent = Decimal('1.50')
        
        total = self.total_final if self.total_final else self.total_estime
        
        # Calcul commission Pressow
        self.commission_amount = (total * self.commission_percent / Decimal('100')).quantize(Decimal('0.01'))
        
        # Frais CinetPay Collect (absorvés par Pressow mais calculés pour info)
        collect_fee = (total * collect_fee_percent / Decimal('100')).quantize(Decimal('0.01'))
        
        # Montant après commission (ce qui va au prestataire avant frais payout)
        amount_after_commission = total - self.commission_amount
        
        # Frais CinetPay Payout (déduits du prestataire)
        self.payout_fee = (amount_after_commission * payout_fee_percent / Decimal('100')).quantize(Decimal('0.01'))
        
        # Net prestataire (après commission + frais payout)
        self.provider_net_amount = amount_after_commission - self.payout_fee
        
        if save:
            self.save(update_fields=[
                'commission_percent',
                'commission_amount',
                'payout_fee',
                'provider_net_amount',
                'updated'
            ])
        
        return {
            'total': total,
            'commission_percent': self.commission_percent,
            'commission_amount': self.commission_amount,
            'payout_fee': self.payout_fee,
            'provider_net_amount': self.provider_net_amount,
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTHODES PAYOUT
    # ═══════════════════════════════════════════════════════════════════
    
    def schedule_payout(self, delay_hours: int = None) -> None:
        """
        Programme le payout automatique après le délai de sécurité.
        Appelé après validation de l'OTP de livraison.
        """
        from apps.core.models import PlatformSettings
        
        if delay_hours is None:
            try:
                platform = PlatformSettings.objects.first()
                delay_hours = platform.payout_delay_hours if platform else 2
            except Exception:
                delay_hours = 2
        
        self.payout_status = 'scheduled'
        self.payout_scheduled_at = timezone.now() + timezone.timedelta(hours=delay_hours)
        self.save(update_fields=['payout_status', 'payout_scheduled_at', 'updated'])
    
    def mark_payout_processing(self, moneroo_id: str = '') -> None:
        """Marque le payout comme en cours de traitement"""
        self.payout_status = 'processing'
        if moneroo_id:
            self.moneroo_payout_id = moneroo_id
        self.save(update_fields=['payout_status', 'moneroo_payout_id', 'updated'])
    
    def mark_payout_completed(self) -> None:
        """Marque le payout comme complété"""
        self.payout_status = 'completed'
        self.payout_completed_at = timezone.now()
        self.save(update_fields=['payout_status', 'payout_completed_at', 'updated'])
    
    def mark_payout_failed(self) -> None:
        """Marque le payout comme échoué"""
        self.payout_status = 'failed'
        self.save(update_fields=['payout_status', 'updated'])
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTHODES ANNULATION
    # ═══════════════════════════════════════════════════════════════════
    
    def cancel(
        self, 
        reason: str, 
        notes: str = '', 
        cancelled_by=None,
        refund: bool = False
    ) -> None:
        """
        Annule la commande avec une raison.
        
        Args:
            reason: Code raison (too_busy, machine_down, client_request, etc.)
            notes: Notes supplémentaires
            cancelled_by: Utilisateur qui annule
            refund: Si True, déclencher le remboursement
        """
        previous_status = self.statut
        self.statut = 'cancelled'
        self.statut_changed_at = timezone.now()
        self.cancellation_reason = reason
        self.cancellation_notes = notes
        self.cancelled_by = cancelled_by
        self.cancelled_at = timezone.now()
        
        if refund and self.payment_status in ['paid', 'escrow']:
            self.payment_status = 'refunded'
        
        self.save()
        
        # Logger l'annulation
        self.log_status(
            event='status_change',
            new_status='cancelled',
            previous_status=previous_status,
            comment=f"Annulé: {reason}. {notes}".strip(),
            performed_by=cancelled_by,
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
