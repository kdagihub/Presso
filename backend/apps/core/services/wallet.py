"""
Service de gestion des portefeuilles prestataires.
Gère les crédits, débits, et calculs de solde.
"""
from decimal import Decimal
from typing import Optional, Dict, Any
from django.db import transaction
from django.utils import timezone

from apps.core.models import (
    ProviderWallet,
    WalletTransaction,
    PlatformSettings,
)
from apps.orders.models import Order
from apps.providers.models import Provider


class WalletService:
    """
    Service pour gérer les opérations sur les portefeuilles prestataires.
    """
    
    @staticmethod
    def get_or_create_wallet(provider: Provider) -> ProviderWallet:
        """
        Récupère ou crée le wallet d'un prestataire.
        """
        wallet, _ = ProviderWallet.objects.get_or_create(provider=provider)
        return wallet
    
    @staticmethod
    def get_platform_settings() -> PlatformSettings:
        """
        Récupère les paramètres de la plateforme.
        """
        return PlatformSettings.objects.first() or PlatformSettings.objects.create()
    
    @classmethod
    def credit_order_payment(
        cls,
        order: Order,
        description: str = ''
    ) -> WalletTransaction:
        """
        Crédite le wallet après livraison d'une commande.
        Le montant crédité est le montant net (total - commission - frais).
        
        Args:
            order: La commande livrée
            description: Description optionnelle
            
        Returns:
            WalletTransaction créée
        """
        wallet = cls.get_or_create_wallet(order.provider)
        
        # S'assurer que les montants sont calculés
        if not order.provider_net_amount or order.provider_net_amount <= 0:
            order.calculate_amounts()
        
        if not description:
            description = f"Commande {order.numero} - Livraison validée"
        
        with transaction.atomic():
            # Créditer le wallet
            tx = wallet.credit(
                amount=order.provider_net_amount,
                transaction_type='order_payment',
                order=order,
                description=description,
                reference=f'ORD-{order.numero}-{timezone.now().strftime("%H%M%S")}',
                metadata={
                    'order_numero': order.numero,
                    'total_commande': str(order.total_final or order.total_estime),
                    'commission_percent': str(order.commission_percent),
                    'commission_amount': str(order.commission_amount),
                    'payout_fee': str(order.payout_fee),
                    'net_amount': str(order.provider_net_amount),
                }
            )
            
            # Incrémenter le compteur de commandes
            wallet.orders_completed += 1
            wallet.save(update_fields=['orders_completed', 'updated'])
            
            return tx
    
    @classmethod
    def debit_for_payout(
        cls,
        wallet: ProviderWallet,
        amount: Decimal,
        payout_request_id: str = '',
        description: str = ''
    ) -> WalletTransaction:
        """
        Débite le wallet pour un retrait (payout).
        
        Args:
            wallet: Le wallet à débiter
            amount: Montant à débiter
            payout_request_id: ID de la demande de payout
            description: Description optionnelle
            
        Returns:
            WalletTransaction créée
        """
        if not description:
            description = f"Retrait Mobile Money"
        
        return wallet.debit(
            amount=amount,
            transaction_type='payout',
            description=description,
            reference=f'PO-{payout_request_id or timezone.now().strftime("%Y%m%d%H%M%S")}',
            metadata={
                'payout_request_id': payout_request_id,
            }
        )
    
    @classmethod
    def add_commission_transaction(
        cls,
        order: Order,
        description: str = ''
    ) -> WalletTransaction:
        """
        Enregistre la transaction de commission (pour l'historique).
        Note: Cette transaction n'affecte pas le solde du prestataire
        car la commission est déjà déduite du montant crédité.
        
        Cette méthode est utile pour la transparence et l'audit.
        """
        wallet = cls.get_or_create_wallet(order.provider)
        
        if not description:
            description = f"Commission plateforme {order.commission_percent}% sur commande {order.numero}"
        
        # Créer une transaction de type 'commission' pour l'historique
        # Note: On n'utilise pas wallet.debit() car ce n'est pas un débit réel
        return WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='commission',
            direction='debit',
            amount=order.commission_amount,
            balance_after=wallet.balance,  # Le solde ne change pas
            order=order,
            description=description,
            reference=f'COM-{order.numero}',
            status='completed',
            metadata={
                'order_numero': order.numero,
                'commission_percent': str(order.commission_percent),
                'total_commande': str(order.total_final or order.total_estime),
            }
        )
    
    @classmethod
    def refund_order(
        cls,
        order: Order,
        amount: Optional[Decimal] = None,
        reason: str = ''
    ) -> Optional[WalletTransaction]:
        """
        Rembourse une commande (débite le wallet du prestataire).
        Utilisé si le client se plaint après livraison.
        
        Args:
            order: La commande à rembourser
            amount: Montant à rembourser (si None, utilise le montant net)
            reason: Raison du remboursement
            
        Returns:
            WalletTransaction ou None si pas de wallet
        """
        wallet = cls.get_or_create_wallet(order.provider)
        
        if amount is None:
            amount = order.provider_net_amount
        
        if amount > wallet.balance:
            raise ValueError(
                f"Solde insuffisant pour le remboursement. "
                f"Disponible: {wallet.balance} FCFA, Requis: {amount} FCFA"
            )
        
        description = f"Remboursement commande {order.numero}"
        if reason:
            description += f" - {reason}"
        
        return wallet.debit(
            amount=amount,
            transaction_type='refund',
            order=order,
            description=description,
            reference=f'REF-{order.numero}-{timezone.now().strftime("%H%M%S")}',
            metadata={
                'order_numero': order.numero,
                'reason': reason,
                'original_amount': str(order.provider_net_amount),
            }
        )
    
    @classmethod
    def get_wallet_summary(cls, provider: Provider) -> Dict[str, Any]:
        """
        Retourne un résumé complet du wallet d'un prestataire.
        
        Returns:
            Dict avec balance, pending, stats, etc.
        """
        wallet = cls.get_or_create_wallet(provider)
        
        # Transactions récentes (7 derniers jours)
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        recent_transactions = wallet.transactions.filter(
            created__gte=seven_days_ago
        )
        
        # Calcul des gains cette semaine
        week_earnings = recent_transactions.filter(
            transaction_type='order_payment',
            direction='credit'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        # Calcul des retraits cette semaine
        week_payouts = recent_transactions.filter(
            transaction_type='payout',
            direction='debit'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        return {
            'wallet_id': str(wallet.id),
            'balance': wallet.balance,
            'pending_balance': wallet.pending_balance,
            'total_earned': wallet.total_earned,
            'total_withdrawn': wallet.total_withdrawn,
            'total_commission_paid': wallet.total_commission_paid,
            'orders_completed': wallet.orders_completed,
            'last_payout_at': wallet.last_payout_at,
            'is_active': wallet.is_active,
            'stats': {
                'week_earnings': week_earnings,
                'week_payouts': week_payouts,
            }
        }
    
    @classmethod
    def get_transaction_history(
        cls,
        provider: Provider,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retourne l'historique des transactions d'un wallet.
        
        Args:
            provider: Le prestataire
            limit: Nombre max de transactions
            offset: Décalage pour pagination
            transaction_type: Filtrer par type (optionnel)
            
        Returns:
            Dict avec transactions et metadata
        """
        wallet = cls.get_or_create_wallet(provider)
        
        queryset = wallet.transactions.all()
        
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        total_count = queryset.count()
        transactions = queryset[offset:offset + limit]
        
        return {
            'transactions': [
                {
                    'id': str(tx.id),
                    'type': tx.transaction_type,
                    'type_display': tx.get_transaction_type_display(),
                    'direction': tx.direction,
                    'amount': tx.amount,
                    'balance_after': tx.balance_after,
                    'reference': tx.reference,
                    'description': tx.description,
                    'order_numero': tx.order.numero if tx.order else None,
                    'status': tx.status,
                    'created': tx.created,
                    'metadata': tx.metadata,
                }
                for tx in transactions
            ],
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count,
            }
        }


# Import models pour les requêtes aggregate
from django.db import models
