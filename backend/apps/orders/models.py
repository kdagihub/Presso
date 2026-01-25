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
        ('paid_pending_verification', 'Payé - Vérification en cours'),
        ('paid', 'Payé'),
        ('adjustment_required', 'Complément requis'),
        ('escrow', 'En séquestre'),
        ('released', 'Libéré'),
        ('refunded', 'Remboursé'),
        ('partially_refunded', 'Partiellement remboursé'),
        ('failed', 'Échoué'),
    ]
    
    COUNTING_MODE_CHOICES = [
        ('client', 'Client compte lui-même'),
        ('collector', 'Livreur compte à la collecte'),
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
    
    # ═══════════════════════════════════════════════════════════════════
    # MODE DE COMPTAGE & VÉRIFICATION À LA COLLECTE
    # ═══════════════════════════════════════════════════════════════════
    
    counting_mode = models.CharField(
        max_length=20,
        choices=COUNTING_MODE_CHOICES,
        default='client',
        verbose_name="Mode de comptage",
        help_text="Qui compte les articles : client ou livreur à la collecte"
    )
    
    # Quantités estimées par le client
    estimated_weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Poids estimé (kg)",
        help_text="Poids déclaré par le client"
    )
    
    estimated_pieces = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de pièces estimé",
        help_text="Nombre de pièces déclaré par le client"
    )
    
    # Quantités vérifiées par le livreur
    verified_weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Poids vérifié (kg)",
        help_text="Poids réel constaté par le livreur"
    )
    
    verified_pieces = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name="Nombre de pièces vérifié",
        help_text="Nombre de pièces réel constaté par le livreur"
    )
    
    quantity_verified_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Quantité vérifiée le"
    )
    
    quantity_verified_by = models.ForeignKey(
        ProviderStaff,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='verified_orders',
        verbose_name="Quantité vérifiée par"
    )
    
    # Ajustement de paiement suite à vérification
    initial_amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant initial payé (FCFA)",
        help_text="Premier paiement du client basé sur son estimation"
    )
    
    adjustment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Montant d'ajustement (FCFA)",
        help_text="Différence positive = client doit payer plus, négative = crédit client"
    )
    
    adjustment_paid_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Ajustement payé le"
    )
    
    adjustment_moneroo_payment_id = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="ID Paiement ajustement Moneroo"
    )
    
    # Pour le remboursement si client a trop payé
    credit_issued = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Crédit émis (FCFA)",
        help_text="Crédit ajouté au portefeuille client si trop-perçu"
    )
    
    # Délai de réponse client pour complément
    adjustment_deadline = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date limite pour complément",
        help_text="Passé ce délai, le livreur ne prend que ce qui correspond au montant payé"
    )
    
    # Client a accepté de réduire le linge
    client_accepted_reduction = models.BooleanField(
        default=False,
        verbose_name="Client a accepté la réduction",
        help_text="True si le client a choisi de retirer du linge plutôt que compléter"
    )
    
    # Photos des articles (pour mode collector)
    photos_submitted = models.BooleanField(
        default=False,
        verbose_name="Photos soumises",
        help_text="Le client a soumis des photos des articles"
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
        max_length=30,
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
    
    # ═══════════════════════════════════════════════════════════════════
    # RÉCLAMATION CLIENT (Après livraison)
    # ═══════════════════════════════════════════════════════════════════
    
    CLAIM_STATUS_CHOICES = [
        ('none', 'Aucune réclamation'),
        ('pending', 'En attente de traitement'),
        ('under_review', 'En cours d\'examen'),
        ('resolved', 'Résolue'),
        ('rejected', 'Rejetée'),
    ]
    
    CLAIM_REASON_CHOICES = [
        ('damaged', 'Vêtements endommagés'),
        ('lost', 'Vêtements perdus'),
        ('stained', 'Taches non enlevées'),
        ('wrong_items', 'Mauvais articles reçus'),
        ('incomplete', 'Commande incomplète'),
        ('quality', 'Qualité insuffisante'),
        ('other', 'Autre'),
    ]
    
    claim_deadline = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date limite de réclamation",
        help_text="Le client a 30 minutes après livraison pour faire une réclamation"
    )
    
    claim_status = models.CharField(
        max_length=20,
        choices=CLAIM_STATUS_CHOICES,
        default='none',
        verbose_name="Statut de réclamation"
    )
    
    claim_reason = models.CharField(
        max_length=30,
        choices=CLAIM_REASON_CHOICES,
        blank=True,
        verbose_name="Raison de la réclamation"
    )
    
    claim_details = models.TextField(
        blank=True,
        verbose_name="Détails de la réclamation",
        help_text="Description détaillée du problème par le client"
    )
    
    claim_photos = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Photos de réclamation",
        help_text="URLs des photos téléchargées par le client"
    )
    
    claim_submitted_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Réclamation soumise le"
    )
    
    claim_resolved_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Réclamation résolue le"
    )
    
    claim_admin_notes = models.TextField(
        blank=True,
        verbose_name="Notes admin sur la réclamation",
        help_text="Notes internes de Pressow pour le traitement"
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
            models.Index(fields=['claim_deadline', 'claim_status']),
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
    # LIBÉRATION IMMÉDIATE DU PAIEMENT (Nouveau système sans payout auto)
    # ═══════════════════════════════════════════════════════════════════
    
    def release_payment_to_provider(self, claim_window_minutes: int = 30) -> dict:
        """
        Libère immédiatement le paiement vers le portefeuille du prestataire.
        
        Appelé après validation de l'OTP de livraison.
        Le client a ensuite X minutes pour faire une réclamation.
        
        Args:
            claim_window_minutes: Délai en minutes pour soumettre une réclamation (défaut: 30)
        
        Returns:
            dict avec les détails de la libération
        """
        from apps.core.services.wallet import WalletService
        from apps.core.models import PlatformSettings
        
        # S'assurer que les montants sont calculés
        if not self.provider_net_amount or self.provider_net_amount <= 0:
            self.calculate_amounts()
        
        # Récupérer ou créer le wallet du prestataire
        wallet = WalletService.get_or_create_wallet(self.provider)
        
        # Créditer le wallet du prestataire
        transaction = WalletService.credit_order_payment(self)
        
        # Définir la date limite de réclamation
        self.claim_deadline = timezone.now() + timezone.timedelta(minutes=claim_window_minutes)
        
        # Marquer le paiement comme libéré (pas de payout automatique)
        self.payout_status = 'completed'
        self.payout_completed_at = timezone.now()
        self.payment_status = 'released'
        
        self.save(update_fields=[
            'claim_deadline',
            'payout_status',
            'payout_completed_at',
            'payment_status',
            'updated'
        ])
        
        self.log_status(
            event='note',
            new_status=self.statut,
            comment=f"Paiement libéré: {self.provider_net_amount} FCFA crédité au portefeuille du prestataire. "
                    f"Délai réclamation: {claim_window_minutes} min",
        )
        
        return {
            'success': True,
            'amount_released': self.provider_net_amount,
            'wallet_balance': wallet.balance,
            'claim_deadline': self.claim_deadline,
            'claim_window_minutes': claim_window_minutes,
            'transaction_id': str(transaction.id) if transaction else None,
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # RÉCLAMATION CLIENT
    # ═══════════════════════════════════════════════════════════════════
    
    def can_submit_claim(self) -> tuple:
        """
        Vérifie si le client peut encore soumettre une réclamation.
        
        Returns:
            tuple (can_submit: bool, reason: str)
        """
        # Vérifier que la commande est livrée
        if self.statut != 'delivered':
            return False, "La commande n'est pas encore livrée."
        
        # Vérifier qu'il n'y a pas déjà une réclamation
        if self.claim_status != 'none':
            return False, "Une réclamation a déjà été soumise pour cette commande."
        
        # Vérifier le délai
        if not self.claim_deadline:
            return False, "Le délai de réclamation n'a pas été défini."
        
        if timezone.now() > self.claim_deadline:
            return False, "Le délai de réclamation est dépassé."
        
        return True, "OK"
    
    def get_claim_remaining_time(self) -> dict:
        """
        Retourne le temps restant pour soumettre une réclamation.
        
        Returns:
            dict avec minutes, seconds, expired, deadline
        """
        if not self.claim_deadline:
            return {
                'minutes': 0,
                'seconds': 0,
                'expired': True,
                'deadline': None,
            }
        
        now = timezone.now()
        if now > self.claim_deadline:
            return {
                'minutes': 0,
                'seconds': 0,
                'expired': True,
                'deadline': self.claim_deadline,
            }
        
        remaining = self.claim_deadline - now
        total_seconds = int(remaining.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        
        return {
            'minutes': minutes,
            'seconds': seconds,
            'expired': False,
            'deadline': self.claim_deadline,
        }
    
    def submit_claim(
        self,
        reason: str,
        details: str = '',
        photos: list = None
    ) -> dict:
        """
        Soumet une réclamation pour cette commande.
        
        Args:
            reason: Code raison (damaged, lost, stained, etc.)
            details: Description détaillée du problème
            photos: Liste d'URLs de photos
        
        Returns:
            dict avec le résultat
        
        Raises:
            ValueError si la réclamation n'est pas possible
        """
        can_submit, msg = self.can_submit_claim()
        if not can_submit:
            raise ValueError(msg)
        
        # Valider la raison
        valid_reasons = [choice[0] for choice in self.CLAIM_REASON_CHOICES]
        if reason not in valid_reasons:
            raise ValueError(f"Raison invalide. Choix possibles: {valid_reasons}")
        
        self.claim_status = 'pending'
        self.claim_reason = reason
        self.claim_details = details or ''
        self.claim_photos = photos or []
        self.claim_submitted_at = timezone.now()
        
        self.save(update_fields=[
            'claim_status',
            'claim_reason',
            'claim_details',
            'claim_photos',
            'claim_submitted_at',
            'updated'
        ])
        
        self.log_status(
            event='note',
            new_status=self.statut,
            comment=f"Réclamation soumise: {self.get_claim_reason_display()}. {details[:100]}...",
        )
        
        return {
            'success': True,
            'claim_status': self.claim_status,
            'claim_reason': self.claim_reason,
            'claim_submitted_at': self.claim_submitted_at,
            'message': "Votre réclamation a été enregistrée. Notre équipe vous contactera rapidement.",
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTHODES VÉRIFICATION À LA COLLECTE
    # ═══════════════════════════════════════════════════════════════════
    
    def verify_quantity(
        self,
        verified_weight: Decimal = None,
        verified_pieces: int = None,
        verified_by=None,
        adjustment_timeout_minutes: int = 10
    ) -> dict:
        """
        Vérifie la quantité réelle à la collecte par le livreur.
        
        Compare avec l'estimation du client et calcule l'ajustement si nécessaire.
        
        Args:
            verified_weight: Poids réel constaté (kg)
            verified_pieces: Nombre de pièces réel constaté
            verified_by: ProviderStaff qui fait la vérification
            adjustment_timeout_minutes: Délai accordé au client pour compléter (défaut: 10 min)
        
        Returns:
            dict avec les détails de la vérification et l'ajustement requis
        """
        from apps.tariffs.models import ProviderService
        
        # Stocker les valeurs vérifiées
        if verified_weight is not None:
            self.verified_weight = Decimal(str(verified_weight))
        if verified_pieces is not None:
            self.verified_pieces = verified_pieces
        
        self.quantity_verified_at = timezone.now()
        self.quantity_verified_by = verified_by
        
        # Calculer l'écart
        adjustment_needed = False
        adjustment_amount = Decimal('0.00')
        new_total = self.total_estime
        
        # Récupérer le prix unitaire du service
        service_item = self.items.first()
        if service_item:
            prix_unitaire = service_item.prix_unitaire
            service = service_item.service
            
            if service.mode_tarif == 'kg' and self.estimated_weight and self.verified_weight:
                # Mode poids : calcul basé sur le poids
                estimated = self.estimated_weight
                verified = self.verified_weight
                
                new_total = (verified * prix_unitaire).quantize(Decimal('0.01'))
                old_total = (estimated * prix_unitaire).quantize(Decimal('0.01'))
                
                adjustment_amount = new_total - self.initial_amount_paid
                
            elif service.mode_tarif == 'piece' and self.estimated_pieces and self.verified_pieces:
                # Mode pièce : calcul basé sur le nombre de pièces
                estimated = self.estimated_pieces
                verified = self.verified_pieces
                
                new_total = (Decimal(str(verified)) * prix_unitaire).quantize(Decimal('0.01'))
                old_total = (Decimal(str(estimated)) * prix_unitaire).quantize(Decimal('0.01'))
                
                adjustment_amount = new_total - self.initial_amount_paid
        
        # Ajouter les frais de livraison au nouveau total
        new_total += self.frais_livraison
        
        # Mettre à jour le total estimé/final
        self.total_estime = new_total
        
        # Déterminer si un ajustement est nécessaire
        if adjustment_amount > Decimal('0.00'):
            # Client doit payer plus
            self.adjustment_amount = adjustment_amount
            self.payment_status = 'adjustment_required'
            self.adjustment_deadline = timezone.now() + timezone.timedelta(minutes=adjustment_timeout_minutes)
            adjustment_needed = True
            
        elif adjustment_amount < Decimal('0.00'):
            # Client a trop payé → crédit
            self.adjustment_amount = adjustment_amount
            self.credit_issued = abs(adjustment_amount)
            # Le statut reste 'paid' car le client a payé assez
            self.payment_status = 'paid'
            
        else:
            # Estimation correcte
            self.adjustment_amount = Decimal('0.00')
            self.payment_status = 'paid'
        
        self.save(update_fields=[
            'verified_weight',
            'verified_pieces',
            'quantity_verified_at',
            'quantity_verified_by',
            'total_estime',
            'adjustment_amount',
            'payment_status',
            'adjustment_deadline',
            'credit_issued',
            'updated'
        ])
        
        # Logger la vérification
        self.log_status(
            event='note',
            new_status=self.statut,
            comment=f"Vérification quantité: estimé={self.estimated_weight or self.estimated_pieces}, "
                    f"vérifié={self.verified_weight or self.verified_pieces}, "
                    f"ajustement={adjustment_amount} FCFA",
            performed_by=verified_by.user if verified_by else None,
        )
        
        return {
            'adjustment_needed': adjustment_needed,
            'adjustment_amount': adjustment_amount,
            'new_total': new_total,
            'initial_paid': self.initial_amount_paid,
            'estimated': {
                'weight': self.estimated_weight,
                'pieces': self.estimated_pieces,
            },
            'verified': {
                'weight': self.verified_weight,
                'pieces': self.verified_pieces,
            },
            'deadline': self.adjustment_deadline,
            'credit_issued': self.credit_issued,
        }
    
    def complete_adjustment_payment(
        self,
        payment_id: str = '',
        payment_method: str = ''
    ) -> bool:
        """
        Enregistre le paiement du complément par le client.
        
        Args:
            payment_id: ID du paiement Moneroo
            payment_method: Méthode de paiement utilisée
        
        Returns:
            True si succès
        """
        if self.adjustment_amount <= Decimal('0.00'):
            return False
        
        self.adjustment_paid_at = timezone.now()
        self.adjustment_moneroo_payment_id = payment_id
        self.payment_status = 'paid'
        
        # Mettre à jour le total final
        self.total_final = self.total_estime
        
        self.save(update_fields=[
            'adjustment_paid_at',
            'adjustment_moneroo_payment_id',
            'payment_status',
            'total_final',
            'updated'
        ])
        
        self.log_status(
            event='note',
            new_status=self.statut,
            comment=f"Complément de paiement reçu: {self.adjustment_amount} FCFA",
        )
        
        return True
    
    def accept_reduction(self) -> dict:
        """
        Le client accepte de réduire le linge pour correspondre au montant déjà payé.
        
        Le livreur ne prendra que ce qui correspond au montant payé.
        
        Returns:
            dict avec les détails de la réduction
        """
        self.client_accepted_reduction = True
        self.adjustment_amount = Decimal('0.00')
        self.payment_status = 'paid'
        
        # Recalculer le total basé sur ce qui a été payé
        self.total_final = self.initial_amount_paid
        self.total_estime = self.initial_amount_paid
        
        # Recalculer les quantités acceptées
        service_item = self.items.first()
        if service_item:
            prix_unitaire = service_item.prix_unitaire
            montant_service = self.initial_amount_paid - self.frais_livraison
            
            if service_item.service.mode_tarif == 'kg':
                # Calculer le poids correspondant au montant payé
                accepted_weight = (montant_service / prix_unitaire).quantize(Decimal('0.01'))
                self.verified_weight = accepted_weight
            elif service_item.service.mode_tarif == 'piece':
                # Calculer le nombre de pièces correspondant
                accepted_pieces = int(montant_service / prix_unitaire)
                self.verified_pieces = accepted_pieces
        
        self.save(update_fields=[
            'client_accepted_reduction',
            'adjustment_amount',
            'payment_status',
            'total_final',
            'total_estime',
            'verified_weight',
            'verified_pieces',
            'updated'
        ])
        
        self.log_status(
            event='note',
            new_status=self.statut,
            comment=f"Client a accepté la réduction. Linge traité: {self.verified_weight or self.verified_pieces}",
        )
        
        return {
            'accepted_weight': self.verified_weight,
            'accepted_pieces': self.verified_pieces,
            'final_total': self.total_final,
        }
    
    def check_adjustment_timeout(self) -> bool:
        """
        Vérifie si le délai de réponse du client est dépassé.
        
        Si oui, applique automatiquement la réduction.
        
        Returns:
            True si le timeout est dépassé et la réduction a été appliquée
        """
        if not self.adjustment_deadline:
            return False
        
        if self.payment_status != 'adjustment_required':
            return False
        
        if timezone.now() > self.adjustment_deadline:
            # Timeout dépassé → appliquer la réduction automatiquement
            self.accept_reduction()
            
            self.log_status(
                event='note',
                new_status=self.statut,
                comment="Délai de réponse dépassé. Réduction automatique appliquée.",
            )
            
            return True
        
        return False
    
    def issue_credit_to_client(self):
        """
        Crédite le portefeuille client si trop-perçu.
        
        À appeler après la collecte si le client a payé plus que nécessaire.
        
        Returns:
            ClientWalletTransaction créée ou None
        """
        from apps.core.models import ClientWallet
        
        if self.credit_issued <= Decimal('0.00'):
            return None
        
        wallet = ClientWallet.get_or_create_for_user(self.client)
        
        transaction = wallet.credit(
            amount=self.credit_issued,
            transaction_type='overpayment',
            order=self,
            description=f"Trop-perçu sur commande {self.numero}. "
                        f"Estimé: {self.estimated_weight or self.estimated_pieces}, "
                        f"Réel: {self.verified_weight or self.verified_pieces}",
            reference=f'OP-{self.numero}-{timezone.now().strftime("%H%M%S")}'
        )
        
        self.log_status(
            event='note',
            new_status=self.statut,
            comment=f"Crédit de {self.credit_issued} FCFA ajouté au portefeuille client",
        )
        
        return transaction
    
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
