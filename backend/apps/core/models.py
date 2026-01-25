import uuid
import secrets
from decimal import Decimal
from django.db import models  # type: ignore
from django.db import transaction  # type: ignore
from django.conf import settings  # type: ignore
from django.utils import timezone  # type: ignore


# =============================================================================
# CONFIGURATION GLOBALE DE LA PLATEFORME
# =============================================================================

class PlatformSettings(models.Model):
    """
    Configuration globale de la plateforme Presso.
    Singleton - une seule instance doit exister.
    Gère les paramètres de commission, payout, montants minimums, etc.
    
    MODÈLE ÉCONOMIQUE (avec CinetPay):
    ===================================
    - Client paie le montant de la commande (pas de frais pour lui)
    - CinetPay prélève ~3% à l'encaissement (Collect)
    - Pressow prélève sa commission (3%)
    - CinetPay prélève ~1.5% au virement (Payout)
    - Total prélevé sur le prestataire : ~7.5%
    - Le prestataire garde ~92.5% du montant
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # ═══════════════════════════════════════════════════════════════════
    # COMMISSION PLATEFORME
    # ═══════════════════════════════════════════════════════════════════
    
    commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('3.00'),
        verbose_name="Commission plateforme (%)",
        help_text="Pourcentage prélevé sur chaque commande livrée (recommandé: 3%)"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # FRAIS PASSERELLE DE PAIEMENT (CinetPay)
    # ═══════════════════════════════════════════════════════════════════
    
    # Frais à l'encaissement (Collect) - payé par la plateforme
    collect_fee_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('3.00'),
        verbose_name="Frais Collect (%)",
        help_text="Frais CinetPay à l'encaissement (~3% Orange, ~1.8% MTN)"
    )
    
    # Frais au virement (Payout) - déduit du montant prestataire
    payout_fee_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('1.50'),
        verbose_name="Frais Payout (%)",
        help_text="Frais CinetPay au virement (~1.5% Orange, ~1.3% MTN)"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # MONTANTS LIMITES
    # ═══════════════════════════════════════════════════════════════════
    
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('500.00'),
        verbose_name="Montant minimum commande (FCFA)",
        help_text="Commandes en dessous de ce montant sont bloquées"
    )
    
    min_payout_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('500.00'),
        verbose_name="Montant minimum retrait (FCFA)",
        help_text="Montant minimum pour déclencher un payout"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # DÉLAIS
    # ═══════════════════════════════════════════════════════════════════
    
    payout_delay_hours = models.PositiveIntegerField(
        default=2,
        verbose_name="Délai avant payout (heures)",
        help_text="Temps d'attente après validation OTP avant virement automatique"
    )
    
    delivery_otp_validity_minutes = models.PositiveIntegerField(
        default=120,
        verbose_name="Validité OTP livraison (minutes)",
        help_text="Durée de validité du code OTP de livraison"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # API PASSERELLE (CinetPay / Moneroo)
    # ═══════════════════════════════════════════════════════════════════
    
    payment_gateway = models.CharField(
        max_length=50,
        default='cinetpay',
        choices=[
            ('cinetpay', 'CinetPay'),
            ('moneroo', 'Moneroo'),
            ('simulation', 'Simulation locale'),
        ],
        verbose_name="Passerelle de paiement",
        help_text="Service utilisé pour les paiements"
    )
    
    gateway_api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Clé API",
        help_text="Clé secrète pour l'API de paiement"
    )
    
    gateway_site_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Site ID (CinetPay)",
        help_text="Identifiant du site pour CinetPay"
    )
    
    gateway_webhook_secret = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Secret Webhook",
        help_text="Secret pour valider les webhooks"
    )
    
    gateway_sandbox_mode = models.BooleanField(
        default=True,
        verbose_name="Mode Sandbox/Test",
        help_text="Utiliser l'environnement de test"
    )
    
    # Champs legacy pour compatibilité
    moneroo_api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="[Legacy] Clé API Moneroo"
    )
    
    moneroo_webhook_secret = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="[Legacy] Secret Webhook Moneroo"
    )
    
    moneroo_sandbox_mode = models.BooleanField(
        default=True,
        verbose_name="[Legacy] Mode Sandbox Moneroo"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTADONNÉES
    # ═══════════════════════════════════════════════════════════════════
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Configuration supplémentaire en JSON"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Configuration plateforme"
        verbose_name_plural = "Configuration plateforme"
    
    def __str__(self):
        return f"Configuration Presso (Commission: {self.commission_percent}%, Gateway: {self.payment_gateway})"
    
    def save(self, *args, **kwargs):
        # Singleton pattern - empêcher la création de plusieurs instances
        if not self.pk and PlatformSettings.objects.exists():
            raise ValueError("Il ne peut y avoir qu'une seule instance de PlatformSettings")
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls) -> 'PlatformSettings':
        """Récupère l'instance unique ou la crée avec les valeurs par défaut"""
        instance, _ = cls.objects.get_or_create(pk=cls.objects.first().pk if cls.objects.exists() else None)
        return instance
    
    def calculate_commission(self, amount: Decimal) -> Decimal:
        """Calcule la commission plateforme pour un montant donné"""
        return (amount * self.commission_percent / Decimal('100')).quantize(Decimal('0.01'))
    
    def calculate_collect_fee(self, amount: Decimal) -> Decimal:
        """Calcule les frais d'encaissement (Collect) prélevés par la passerelle"""
        return (amount * self.collect_fee_percent / Decimal('100')).quantize(Decimal('0.01'))
    
    def calculate_payout_fee(self, amount: Decimal) -> Decimal:
        """Calcule les frais de virement (Payout) prélevés par la passerelle"""
        return (amount * self.payout_fee_percent / Decimal('100')).quantize(Decimal('0.01'))
    
    def calculate_net_received(self, order_amount: Decimal) -> Decimal:
        """
        Calcule le montant net reçu par Pressow après frais Collect.
        
        Args:
            order_amount: Montant payé par le client
            
        Returns:
            Montant reçu sur le compte Pressow
        """
        collect_fee = self.calculate_collect_fee(order_amount)
        return order_amount - collect_fee
    
    def calculate_provider_payout(self, order_amount: Decimal) -> dict:
        """
        Calcule tous les montants pour une commande.
        
        Args:
            order_amount: Montant de la commande payé par le client
            
        Returns:
            Dict avec tous les montants détaillés
        """
        # Frais à l'encaissement
        collect_fee = self.calculate_collect_fee(order_amount)
        net_received = order_amount - collect_fee
        
        # Commission Pressow
        commission = self.calculate_commission(order_amount)
        
        # Montant brut pour le prestataire (avant frais payout)
        gross_payout = order_amount - commission
        
        # Frais de virement
        payout_fee = self.calculate_payout_fee(gross_payout)
        
        # Montant net que le prestataire recevra
        net_payout = gross_payout - payout_fee
        
        # Marge nette Pressow (ce qui reste après tout)
        pressow_margin = net_received - gross_payout
        
        return {
            'order_amount': order_amount,
            'collect_fee': collect_fee,
            'net_received': net_received,
            'commission': commission,
            'commission_percent': self.commission_percent,
            'gross_payout': gross_payout,
            'payout_fee': payout_fee,
            'net_payout': net_payout,
            'pressow_margin': pressow_margin,
            'total_fees_percent': self.collect_fee_percent + self.commission_percent + self.payout_fee_percent,
            'provider_keeps_percent': Decimal('100') - self.collect_fee_percent - self.commission_percent - self.payout_fee_percent,
        }
    
    def calculate_net_payout(self, amount: Decimal) -> Decimal:
        """
        Calcule le montant net à verser au prestataire après commission et frais payout.
        (Méthode simplifiée pour compatibilité)
        """
        result = self.calculate_provider_payout(amount)
        return result['net_payout']
    
    def is_simulation_mode(self) -> bool:
        """Vérifie si on est en mode simulation (pas de clé API configurée)"""
        return self.gateway_sandbox_mode and not self.gateway_api_key


# =============================================================================
# PORTEFEUILLE PRESTATAIRE
# =============================================================================

class ProviderWallet(models.Model):
    """
    Portefeuille virtuel du prestataire.
    Gère le solde disponible, en attente, et total des gains.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    provider = models.OneToOneField(
        'providers.Provider',
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name="Prestataire"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # SOLDES
    # ═══════════════════════════════════════════════════════════════════
    
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Solde disponible (FCFA)",
        help_text="Montant disponible pour retrait"
    )
    
    pending_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Solde en attente (FCFA)",
        help_text="Montant en attente de virement (< délai payout)"
    )
    
    total_earned = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total gagné (FCFA)",
        help_text="Total cumulé depuis le début"
    )
    
    total_withdrawn = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total retiré (FCFA)",
        help_text="Total des retraits effectués"
    )
    
    total_commission_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total commissions payées (FCFA)",
        help_text="Total des commissions prélevées par la plateforme"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # STATISTIQUES
    # ═══════════════════════════════════════════════════════════════════
    
    orders_completed = models.PositiveIntegerField(
        default=0,
        verbose_name="Commandes complétées",
        help_text="Nombre total de commandes livrées"
    )
    
    last_payout_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernier retrait le"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTADONNÉES
    # ═══════════════════════════════════════════════════════════════════
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Wallet actif",
        help_text="Si False, les retraits sont bloqués"
    )
    
    suspended_reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Raison de suspension"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Portefeuille prestataire"
        verbose_name_plural = "Portefeuilles prestataires"
        indexes = [
            models.Index(fields=['provider']),
            models.Index(fields=['balance']),
        ]
    
    def __str__(self):
        return f"Wallet - {self.provider.nom_commercial} ({self.balance} FCFA)"
    
    def credit(
        self,
        amount: Decimal,
        transaction_type: str,
        order=None,
        description: str = '',
        reference: str = '',
        metadata: dict = None
    ) -> 'WalletTransaction':
        """
        Crédite le wallet (ajoute des fonds).
        Utilisé après livraison d'une commande.
        """
        with transaction.atomic():
            self.balance += amount
            self.total_earned += amount
            self.save(update_fields=['balance', 'total_earned', 'updated'])
            
            return WalletTransaction.objects.create(
                wallet=self,
                transaction_type=transaction_type,
                direction='credit',
                amount=amount,
                balance_after=self.balance,
                order=order,
                description=description,
                reference=reference or f'CR-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                metadata=metadata or {}
            )
    
    def debit(
        self,
        amount: Decimal,
        transaction_type: str,
        order=None,
        description: str = '',
        reference: str = '',
        metadata: dict = None
    ) -> 'WalletTransaction':
        """
        Débite le wallet (retire des fonds).
        Utilisé pour les payouts et remboursements.
        """
        if amount > self.balance:
            raise ValueError(f"Solde insuffisant. Disponible: {self.balance}, Demandé: {amount}")
        
        with transaction.atomic():
            self.balance -= amount
            self.total_withdrawn += amount
            self.save(update_fields=['balance', 'total_withdrawn', 'updated'])
            
            return WalletTransaction.objects.create(
                wallet=self,
                transaction_type=transaction_type,
                direction='debit',
                amount=amount,
                balance_after=self.balance,
                order=order,
                description=description,
                reference=reference or f'DB-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                metadata=metadata or {}
            )
    
    def add_pending(self, amount: Decimal) -> None:
        """Ajoute au solde en attente (après validation OTP, avant payout)"""
        self.pending_balance += amount
        self.save(update_fields=['pending_balance', 'updated'])
    
    def release_pending(self, amount: Decimal) -> None:
        """Libère le solde en attente vers le solde disponible"""
        if amount > self.pending_balance:
            amount = self.pending_balance
        self.pending_balance -= amount
        self.save(update_fields=['pending_balance', 'updated'])


class WalletTransaction(models.Model):
    """
    Historique des transactions du portefeuille.
    Trace chaque mouvement d'argent (crédit/débit).
    """
    TRANSACTION_TYPES = [
        ('order_payment', 'Paiement commande'),
        ('commission', 'Commission plateforme'),
        ('payout', 'Retrait Mobile Money'),
        ('refund', 'Remboursement'),
        ('adjustment', 'Ajustement manuel'),
        ('bonus', 'Bonus/Prime'),
    ]
    
    DIRECTION_CHOICES = [
        ('credit', 'Crédit (+)'),
        ('debit', 'Débit (-)'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    wallet = models.ForeignKey(
        ProviderWallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Portefeuille"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # DÉTAILS DE LA TRANSACTION
    # ═══════════════════════════════════════════════════════════════════
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        verbose_name="Type de transaction"
    )
    
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        verbose_name="Direction"
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Montant (FCFA)"
    )
    
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Solde après transaction"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # RÉFÉRENCES
    # ═══════════════════════════════════════════════════════════════════
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions',
        verbose_name="Commande liée"
    )
    
    reference = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Référence",
        help_text="Référence unique de la transaction"
    )
    
    external_reference = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Référence externe",
        help_text="ID Moneroo ou autre référence externe"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # STATUT & DESCRIPTION
    # ═══════════════════════════════════════════════════════════════════
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        verbose_name="Statut"
    )
    
    description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Description"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTADONNÉES
    # ═══════════════════════════════════════════════════════════════════
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Détails supplémentaires (frais, commission, etc.)"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Transaction wallet"
        verbose_name_plural = "Transactions wallet"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['wallet', 'transaction_type']),
            models.Index(fields=['wallet', 'created']),
            models.Index(fields=['reference']),
            models.Index(fields=['order']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        sign = '+' if self.direction == 'credit' else '-'
        return f"{sign}{self.amount} FCFA - {self.get_transaction_type_display()} ({self.reference})"


# =============================================================================
# DEMANDES DE RETRAIT (PAYOUT REQUESTS)
# =============================================================================

class PayoutRequest(models.Model):
    """
    Demande de retrait vers Mobile Money.
    Créée automatiquement après le délai de sécurité ou manuellement.
    """
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    wallet = models.ForeignKey(
        ProviderWallet,
        on_delete=models.CASCADE,
        related_name='payout_requests',
        verbose_name="Portefeuille"
    )
    
    payout_account = models.ForeignKey(
        'core.ProviderPayoutAccount',
        on_delete=models.PROTECT,
        related_name='payout_requests',
        verbose_name="Compte de destination"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # MONTANTS
    # ═══════════════════════════════════════════════════════════════════
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Montant demandé (FCFA)"
    )
    
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Frais de transfert (FCFA)"
    )
    
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Montant net (FCFA)",
        help_text="Montant réellement reçu par le prestataire"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # RÉFÉRENCES
    # ═══════════════════════════════════════════════════════════════════
    
    reference = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Référence interne"
    )
    
    moneroo_payout_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="ID Payout Moneroo"
    )
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payout_requests',
        verbose_name="Commande liée",
        help_text="Si payout automatique après livraison"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # STATUT
    # ═══════════════════════════════════════════════════════════════════
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name="Message d'erreur"
    )
    
    retry_count = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="Nombre de tentatives"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # DATES
    # ═══════════════════════════════════════════════════════════════════
    
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Programmé pour",
        help_text="Date/heure d'exécution prévue"
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Traité le"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Complété le"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTADONNÉES
    # ═══════════════════════════════════════════════════════════════════
    
    is_automatic = models.BooleanField(
        default=True,
        verbose_name="Payout automatique",
        help_text="True si déclenché automatiquement après OTP"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Réponse Moneroo, détails de la commande, etc."
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Demande de retrait"
        verbose_name_plural = "Demandes de retrait"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['wallet', 'status']),
            models.Index(fields=['reference']),
            models.Index(fields=['moneroo_payout_id']),
            models.Index(fields=['scheduled_at', 'status']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"Payout {self.reference} - {self.amount} FCFA ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f'PO-{timezone.now().strftime("%Y%m%d%H%M%S")}-{secrets.token_hex(4).upper()}'
        if not self.net_amount:
            self.net_amount = self.amount - self.fee
        super().save(*args, **kwargs)
    
    def mark_processing(self, moneroo_id: str = '') -> None:
        """Marque le payout comme en cours de traitement"""
        self.status = 'processing'
        self.processed_at = timezone.now()
        if moneroo_id:
            self.moneroo_payout_id = moneroo_id
        self.save(update_fields=['status', 'processed_at', 'moneroo_payout_id', 'updated'])
    
    def mark_completed(self) -> None:
        """Marque le payout comme complété"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated'])
        
        # Mettre à jour le wallet
        self.wallet.last_payout_at = timezone.now()
        self.wallet.save(update_fields=['last_payout_at', 'updated'])
    
    def mark_failed(self, error: str, should_retry: bool = True) -> None:
        """Marque le payout comme échoué"""
        self.status = 'failed'
        self.error_message = error
        if should_retry:
            self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count', 'updated'])


# =============================================================================
# PORTEFEUILLE CLIENT (Crédits / Remboursements)
# =============================================================================

class ClientWallet(models.Model):
    """
    Portefeuille virtuel du client.
    Gère les crédits (remboursements, trop-perçus).
    Le client peut utiliser son crédit pour payer ses commandes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name="Client"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # SOLDES
    # ═══════════════════════════════════════════════════════════════════
    
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Solde disponible (FCFA)",
        help_text="Montant utilisable pour payer des commandes"
    )
    
    total_credited = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total crédité (FCFA)",
        help_text="Total des crédits reçus (remboursements, trop-perçus)"
    )
    
    total_used = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Total utilisé (FCFA)",
        help_text="Total des crédits utilisés pour payer des commandes"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTADONNÉES
    # ═══════════════════════════════════════════════════════════════════
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Wallet actif"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Portefeuille client"
        verbose_name_plural = "Portefeuilles clients"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['balance']),
        ]
    
    def __str__(self):
        return f"Wallet Client - {self.user.get_full_name() or self.user.phone} ({self.balance} FCFA)"
    
    def credit(
        self,
        amount: Decimal,
        transaction_type: str,
        order=None,
        description: str = '',
        reference: str = '',
        metadata: dict = None
    ) -> 'ClientWalletTransaction':
        """
        Crédite le wallet client (ajoute des fonds).
        Utilisé pour les remboursements et trop-perçus.
        """
        with transaction.atomic():
            self.balance += amount
            self.total_credited += amount
            self.save(update_fields=['balance', 'total_credited', 'updated'])
            
            return ClientWalletTransaction.objects.create(
                wallet=self,
                transaction_type=transaction_type,
                direction='credit',
                amount=amount,
                balance_after=self.balance,
                order=order,
                description=description,
                reference=reference or f'CL-CR-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                metadata=metadata or {}
            )
    
    def debit(
        self,
        amount: Decimal,
        transaction_type: str,
        order=None,
        description: str = '',
        reference: str = '',
        metadata: dict = None
    ) -> 'ClientWalletTransaction':
        """
        Débite le wallet client (utilise des fonds).
        Utilisé quand le client paie avec son crédit.
        """
        if amount > self.balance:
            raise ValueError(f"Solde insuffisant. Disponible: {self.balance}, Demandé: {amount}")
        
        with transaction.atomic():
            self.balance -= amount
            self.total_used += amount
            self.save(update_fields=['balance', 'total_used', 'updated'])
            
            return ClientWalletTransaction.objects.create(
                wallet=self,
                transaction_type=transaction_type,
                direction='debit',
                amount=amount,
                balance_after=self.balance,
                order=order,
                description=description,
                reference=reference or f'CL-DB-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                metadata=metadata or {}
            )
    
    @classmethod
    def get_or_create_for_user(cls, user) -> 'ClientWallet':
        """Récupère ou crée le wallet pour un utilisateur"""
        wallet, _ = cls.objects.get_or_create(user=user)
        return wallet


class ClientWalletTransaction(models.Model):
    """
    Historique des transactions du portefeuille client.
    Trace chaque mouvement d'argent (crédit/débit).
    """
    TRANSACTION_TYPES = [
        ('refund', 'Remboursement commande'),
        ('overpayment', 'Trop-perçu (livreur a constaté moins)'),
        ('payment', 'Paiement avec crédit'),
        ('adjustment', 'Ajustement manuel'),
        ('promo', 'Crédit promotionnel'),
    ]
    
    DIRECTION_CHOICES = [
        ('credit', 'Crédit (+)'),
        ('debit', 'Débit (-)'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Complété'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    wallet = models.ForeignKey(
        ClientWallet,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Portefeuille"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # DÉTAILS DE LA TRANSACTION
    # ═══════════════════════════════════════════════════════════════════
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        verbose_name="Type de transaction"
    )
    
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        verbose_name="Direction"
    )
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Montant (FCFA)"
    )
    
    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Solde après transaction"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # RÉFÉRENCES
    # ═══════════════════════════════════════════════════════════════════
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_wallet_transactions',
        verbose_name="Commande liée"
    )
    
    reference = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Référence",
        help_text="Référence unique de la transaction"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # STATUT & DESCRIPTION
    # ═══════════════════════════════════════════════════════════════════
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        verbose_name="Statut"
    )
    
    description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Description"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Transaction wallet client"
        verbose_name_plural = "Transactions wallet client"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['wallet', 'transaction_type']),
            models.Index(fields=['wallet', 'created']),
            models.Index(fields=['reference']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        sign = '+' if self.direction == 'credit' else '-'
        return f"{sign}{self.amount} FCFA - {self.get_transaction_type_display()} ({self.reference})"


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
    Configuration générale du tenant + état d'onboarding
    """
    ONBOARDING_STEPS = [
        (0, 'Non commencé'),
        (1, 'Identité du pressing'),
        (2, 'Services et tarifs'),
        (3, 'Informations de paiement'),
        (4, 'Terminé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    provider = models.OneToOneField(
        'providers.Provider',
        on_delete=models.CASCADE,
        related_name='settings',
        verbose_name="Prestataire"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # ONBOARDING (Configuration initiale obligatoire)
    # ═══════════════════════════════════════════════════════════════════
    
    onboarding_completed = models.BooleanField(
        default=False,
        verbose_name="Onboarding terminé",
        help_text="Indique si le prestataire a terminé la configuration initiale"
    )
    
    onboarding_step = models.PositiveSmallIntegerField(
        default=0,
        choices=ONBOARDING_STEPS,
        verbose_name="Étape d'onboarding",
        help_text="Étape actuelle du parcours de configuration"
    )
    
    onboarding_started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Onboarding commencé le"
    )
    
    onboarding_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Onboarding terminé le"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # ÉTAT OPÉRATIONNEL (Ouvert/Fermé)
    # ═══════════════════════════════════════════════════════════════════
    
    is_open = models.BooleanField(
        default=False,
        verbose_name="Pressing ouvert",
        help_text="Si False, le pressing n'apparaît pas dans l'app client"
    )
    
    closed_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Raison de fermeture",
        help_text="Ex: Vacances, Panne machine, Trop de travail"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # BRANDING
    # ═══════════════════════════════════════════════════════════════════
    
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
    
    storefront_photo = models.ImageField(
        upload_to='providers/storefronts/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Photo de la devanture",
        help_text="Photo de l'établissement visible par les clients"
    )
    
    primary_color = models.CharField(
        max_length=7,
        default='#3b82f6',
        verbose_name="Couleur principale",
        help_text="Format hex: #RRGGBB"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # CONFIGURATION OPÉRATIONNELLE
    # ═══════════════════════════════════════════════════════════════════
    
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
    
    # ═══════════════════════════════════════════════════════════════════
    # NOTIFICATIONS - Canaux
    # ═══════════════════════════════════════════════════════════════════
    
    push_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifications push",
        help_text="Notifications sur l'appareil (navigateur/mobile)"
    )
    
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Notifications par email"
    )
    
    sms_notifications = models.BooleanField(
        default=False,
        verbose_name="Notifications par SMS",
        help_text="SMS facturés, à activer avec précaution"
    )
    
    notification_email = models.EmailField(
        blank=True,
        verbose_name="Email de notification",
        help_text="Si vide, utilise l'email du compte"
    )
    
    notification_phone = models.CharField(
        max_length=15,
        blank=True,
        verbose_name="Téléphone de notification",
        help_text="Si vide, utilise le téléphone du compte"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # NOTIFICATIONS - Types (quels événements notifier)
    # ═══════════════════════════════════════════════════════════════════
    
    notify_new_orders = models.BooleanField(
        default=True,
        verbose_name="Nouvelles commandes",
        help_text="Notification à chaque nouvelle commande"
    )
    
    notify_order_updates = models.BooleanField(
        default=True,
        verbose_name="Mises à jour commandes",
        help_text="Annulations, modifications de commandes"
    )
    
    notify_payments = models.BooleanField(
        default=True,
        verbose_name="Paiements reçus",
        help_text="Notification quand un paiement est confirmé"
    )
    
    notify_reminders = models.BooleanField(
        default=True,
        verbose_name="Rappels",
        help_text="Rappels pour commandes en attente"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # DISPONIBILITÉ AVANCÉE
    # ═══════════════════════════════════════════════════════════════════
    
    pause_mode = models.BooleanField(
        default=False,
        verbose_name="Mode pause",
        help_text="Mettre temporairement le pressing en pause (n'accepte plus de commandes)"
    )
    
    pause_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Raison de la pause",
        help_text="Ex: Vacances, Maintenance, etc."
    )
    
    max_orders_per_day = models.PositiveIntegerField(
        default=0,
        verbose_name="Max commandes par jour",
        help_text="0 = illimité"
    )
    
    working_days = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Jours de travail",
        help_text="Liste des jours: ['monday', 'tuesday', ...]"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # SÉCURITÉ
    # ═══════════════════════════════════════════════════════════════════
    
    two_factor_auth = models.BooleanField(
        default=False,
        verbose_name="Authentification à deux facteurs",
        help_text="Double vérification lors de la connexion"
    )
    
    login_alerts = models.BooleanField(
        default=True,
        verbose_name="Alertes de connexion",
        help_text="Notification en cas de nouvelle connexion"
    )
    
    # ═══════════════════════════════════════════════════════════════════
    # HORAIRES & MÉTADONNÉES
    # ═══════════════════════════════════════════════════════════════════
    
    opening_hours = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Horaires d'ouverture",
        help_text="Format JSON avec les horaires par jour"
    )
    
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
    
    def get_onboarding_status(self) -> dict:
        """Retourne l'état détaillé de l'onboarding"""
        return {
            'completed': self.onboarding_completed,
            'current_step': self.onboarding_step,
            'steps': {
                'identity': self.onboarding_step >= 1,
                'services': self.onboarding_step >= 2,
                'payout': self.onboarding_step >= 3,
            },
            'started_at': self.onboarding_started_at,
            'completed_at': self.onboarding_completed_at,
        }
    
    def advance_onboarding(self, step: int) -> None:
        """Avance l'onboarding à une étape donnée"""
        from django.utils import timezone
        
        if step > self.onboarding_step:
            if self.onboarding_step == 0:
                self.onboarding_started_at = timezone.now()
            
            self.onboarding_step = step
            
            if step >= 3:
                self.onboarding_completed = True
                self.onboarding_completed_at = timezone.now()
            
            self.save(update_fields=[
                'onboarding_step',
                'onboarding_completed',
                'onboarding_started_at',
                'onboarding_completed_at',
                'updated'
            ])


class ProviderPayoutAccount(models.Model):
    """
    Comptes de paiement (Mobile Money) pour les retraits des prestataires.
    Permet au prestataire de recevoir ses paiements.
    """
    OPERATOR_CHOICES = [
        ('orange', 'Orange Money'),
        ('mtn', 'MTN Mobile Money'),
        ('moov', 'Moov Money'),
        ('wave', 'Wave'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente de vérification'),
        ('verified', 'Vérifié'),
        ('rejected', 'Rejeté'),
        ('suspended', 'Suspendu'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.CASCADE,
        related_name='payout_accounts',
        verbose_name="Prestataire"
    )
    
    operator = models.CharField(
        max_length=20,
        choices=OPERATOR_CHOICES,
        verbose_name="Opérateur Mobile Money"
    )
    
    phone_number = models.CharField(
        max_length=15,
        verbose_name="Numéro de téléphone",
        help_text="Numéro associé au compte Mobile Money"
    )
    
    account_name = models.CharField(
        max_length=200,
        verbose_name="Nom du titulaire",
        help_text="Nom affiché sur le compte Mobile Money"
    )
    
    is_primary = models.BooleanField(
        default=False,
        verbose_name="Compte principal",
        help_text="Compte utilisé par défaut pour les retraits"
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut de vérification"
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Vérifié le"
    )
    
    # Métadonnées (ex: raison de rejet, notes admin)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Compte de paiement"
        verbose_name_plural = "Comptes de paiement"
        ordering = ['-is_primary', '-created']
        indexes = [
            models.Index(fields=['provider', 'is_primary']),
            models.Index(fields=['operator', 'phone_number']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'operator', 'phone_number'],
                name='unique_payout_account_per_provider'
            ),
        ]
    
    def __str__(self):
        return f"{self.get_operator_display()} - {self.phone_number} ({self.account_name})"
    
    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'un seul compte principal par prestataire
        if self.is_primary:
            ProviderPayoutAccount.objects.filter(
                provider=self.provider,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        # Si c'est le premier compte, le rendre principal automatiquement
        if not self.pk:
            if not ProviderPayoutAccount.objects.filter(provider=self.provider).exists():
                self.is_primary = True
        
        super().save(*args, **kwargs)


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

