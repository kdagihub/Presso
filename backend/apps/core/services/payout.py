"""
Service de gestion des payouts (virements vers les prestataires).
Gère la création, l'exécution et le suivi des demandes de retrait.
"""
import logging
from decimal import Decimal
from typing import Optional, Tuple, Dict, Any
from django.db import transaction
from django.utils import timezone

from apps.core.models import (
    ProviderWallet,
    PayoutRequest,
    PlatformSettings,
    ProviderPayoutAccount,
)
from apps.orders.models import Order
from apps.providers.models import Provider

logger = logging.getLogger(__name__)


class PayoutService:
    """
    Service pour gérer les payouts vers les prestataires.
    
    Supporte deux modes:
    1. Automatique: Après validation OTP, payout programmé après délai de sécurité
    2. Manuel: Prestataire demande un retrait de son solde disponible
    """
    
    @staticmethod
    def get_platform_settings() -> PlatformSettings:
        """Récupère les paramètres de la plateforme."""
        return PlatformSettings.objects.first() or PlatformSettings.objects.create()
    
    @classmethod
    def create_payout_request_for_order(cls, order: Order) -> PayoutRequest:
        """
        Crée une demande de payout automatique après livraison d'une commande.
        
        Args:
            order: La commande livrée
            
        Returns:
            PayoutRequest créée
        """
        from apps.core.services.wallet import WalletService
        
        wallet = WalletService.get_or_create_wallet(order.provider)
        platform = cls.get_platform_settings()
        
        # Récupérer le compte de payout principal du prestataire
        payout_account = ProviderPayoutAccount.objects.filter(
            provider=order.provider,
            is_primary=True,
            status='verified'
        ).first()
        
        # Si pas de compte vérifié, prendre le premier compte disponible
        if not payout_account:
            payout_account = ProviderPayoutAccount.objects.filter(
                provider=order.provider,
                is_primary=True
            ).first()
        
        if not payout_account:
            logger.error(
                f"Pas de compte de payout pour prestataire {order.provider.id}. "
                f"Commande {order.numero}"
            )
            # Créer quand même la demande mais elle sera en erreur
            raise ValueError("Aucun compte de payout configuré pour ce prestataire.")
        
        # S'assurer que les montants sont calculés
        if not order.provider_net_amount or order.provider_net_amount <= 0:
            order.calculate_amounts()
        
        # Calculer le montant net après frais
        amount = order.provider_net_amount
        # Calculer les frais de payout
        fee = platform.calculate_payout_fee(amount)
        net_amount = amount - fee  # Montant net après frais de transfert
        
        # Programmer l'exécution
        delay_hours = platform.payout_delay_hours
        scheduled_at = timezone.now() + timezone.timedelta(hours=delay_hours)
        
        with transaction.atomic():
            # Ajouter au solde en attente
            wallet.add_pending(amount)
            
            # Créer la demande de payout
            payout_request = PayoutRequest.objects.create(
                wallet=wallet,
                payout_account=payout_account,
                amount=amount,
                fee=fee,
                net_amount=net_amount,
                order=order,
                status='scheduled',
                scheduled_at=scheduled_at,
                is_automatic=True,
                metadata={
                    'order_numero': order.numero,
                    'total_commande': str(order.total_final or order.total_estime),
                    'commission_percent': str(order.commission_percent),
                    'commission_amount': str(order.commission_amount),
                    'provider_name': order.provider.nom_commercial,
                }
            )
        
        logger.info(
            f"PayoutRequest créé pour commande {order.numero}: "
            f"{amount} FCFA programmé pour {scheduled_at}"
        )
        
        return payout_request
    
    @classmethod
    def create_manual_payout_request(
        cls,
        provider: Provider,
        amount: Optional[Decimal] = None
    ) -> Tuple[PayoutRequest, str]:
        """
        Crée une demande de retrait manuel par le prestataire.
        
        Args:
            provider: Le prestataire
            amount: Montant à retirer (si None, retire tout le solde)
            
        Returns:
            Tuple (PayoutRequest, message)
        """
        from apps.core.services.wallet import WalletService
        
        wallet = WalletService.get_or_create_wallet(provider)
        platform = cls.get_platform_settings()
        
        # Vérifier que le wallet est actif
        if not wallet.is_active:
            raise ValueError(f"Votre portefeuille est suspendu: {wallet.suspended_reason}")
        
        # Montant à retirer
        if amount is None:
            amount = wallet.balance
        
        # Vérifications
        if amount <= 0:
            raise ValueError("Le montant doit être supérieur à 0.")
        
        if amount > wallet.balance:
            raise ValueError(
                f"Solde insuffisant. Disponible: {wallet.balance} FCFA, Demandé: {amount} FCFA"
            )
        
        if amount < platform.min_payout_amount:
            raise ValueError(
                f"Montant minimum de retrait: {platform.min_payout_amount} FCFA"
            )
        
        # Récupérer le compte de payout
        payout_account = ProviderPayoutAccount.objects.filter(
            provider=provider,
            is_primary=True
        ).first()
        
        if not payout_account:
            raise ValueError("Aucun compte de payout configuré. Ajoutez un compte Mobile Money.")
        
        # Calculer le net avec les frais de payout
        fee = platform.calculate_payout_fee(amount)
        net_amount = amount - fee
        
        if net_amount <= 0:
            raise ValueError(
                f"Le montant après frais ({fee:.2f} FCFA) doit être positif."
            )
        
        with transaction.atomic():
            # Débiter le wallet immédiatement
            WalletService.debit_for_payout(
                wallet=wallet,
                amount=amount,
                description=f"Retrait manuel vers {payout_account.get_operator_display()}"
            )
            
            # Créer la demande (exécution immédiate)
            payout_request = PayoutRequest.objects.create(
                wallet=wallet,
                payout_account=payout_account,
                amount=amount,
                fee=fee,
                net_amount=net_amount,
                status='pending',
                scheduled_at=timezone.now(),
                is_automatic=False,
                metadata={
                    'provider_name': provider.nom_commercial,
                    'manual_request': True,
                }
            )
        
        logger.info(
            f"Demande de retrait manuel créée pour {provider.nom_commercial}: "
            f"{amount} FCFA"
        )
        
        return payout_request, f"Demande de retrait de {net_amount} FCFA créée."
    
    @classmethod
    def execute_payout(cls, payout_request: PayoutRequest) -> Tuple[bool, str]:
        """
        Exécute un payout via Moneroo.
        
        Args:
            payout_request: La demande de payout à exécuter
            
        Returns:
            Tuple (success: bool, message: str)
        """
        from apps.core.services.moneroo import MonerooService
        
        # Vérifications préliminaires
        if payout_request.status not in ['pending', 'scheduled', 'failed']:
            return False, f"Payout déjà traité (statut: {payout_request.status})"
        
        if payout_request.retry_count >= 5:
            payout_request.status = 'cancelled'
            payout_request.error_message = "Nombre maximum de tentatives atteint"
            payout_request.save()
            return False, "Payout annulé après 5 tentatives échouées"
        
        # Marquer comme en cours
        payout_request.mark_processing()
        
        try:
            # Appeler l'API Moneroo
            result = MonerooService.send_payout(
                phone_number=payout_request.payout_account.phone_number,
                amount=payout_request.net_amount,
                operator=payout_request.payout_account.operator,
                reference=payout_request.reference,
                metadata={
                    'payout_request_id': str(payout_request.id),
                    'provider_id': str(payout_request.wallet.provider.id),
                }
            )
            
            if result['success']:
                # Mettre à jour avec l'ID Moneroo
                payout_request.moneroo_payout_id = result.get('transaction_id', '')
                payout_request.mark_completed()
                
                # Si c'est un payout automatique (lié à une commande)
                if payout_request.order:
                    # Créditer le wallet et marquer la commande
                    from apps.core.services.wallet import WalletService
                    
                    # Libérer le solde en attente
                    payout_request.wallet.release_pending(payout_request.amount)
                    
                    # Créditer le wallet (pour l'historique)
                    WalletService.credit_order_payment(payout_request.order)
                    
                    # Marquer la commande comme payée
                    payout_request.order.mark_payout_completed()
                
                logger.info(
                    f"Payout {payout_request.reference} exécuté avec succès. "
                    f"Moneroo ID: {payout_request.moneroo_payout_id}"
                )
                
                return True, "Virement effectué avec succès !"
            else:
                # Erreur Moneroo
                error_msg = result.get('error', 'Erreur inconnue')
                payout_request.mark_failed(error_msg, should_retry=True)
                
                logger.error(
                    f"Payout {payout_request.reference} échoué: {error_msg}"
                )
                
                return False, f"Erreur de virement: {error_msg}"
                
        except Exception as e:
            error_msg = str(e)
            payout_request.mark_failed(error_msg, should_retry=True)
            
            logger.exception(
                f"Exception lors du payout {payout_request.reference}: {error_msg}"
            )
            
            return False, f"Erreur technique: {error_msg}"
    
    @classmethod
    def get_pending_payouts(cls) -> list:
        """
        Retourne les payouts programmés qui doivent être exécutés.
        Utilisé par la tâche Celery.
        """
        now = timezone.now()
        
        return PayoutRequest.objects.filter(
            status='scheduled',
            scheduled_at__lte=now,
            retry_count__lt=5
        ).select_related('wallet', 'payout_account', 'order')
    
    @classmethod
    def get_failed_payouts_to_retry(cls) -> list:
        """
        Retourne les payouts échoués qui peuvent être réessayés.
        """
        return PayoutRequest.objects.filter(
            status='failed',
            retry_count__lt=5
        ).select_related('wallet', 'payout_account', 'order')
    
    @classmethod
    def get_payout_history(
        cls,
        provider: Provider,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retourne l'historique des payouts d'un prestataire.
        """
        from apps.core.services.wallet import WalletService
        
        wallet = WalletService.get_or_create_wallet(provider)
        
        queryset = PayoutRequest.objects.filter(wallet=wallet)
        
        if status:
            queryset = queryset.filter(status=status)
        
        total_count = queryset.count()
        payouts = queryset[offset:offset + limit]
        
        return {
            'payouts': [
                {
                    'id': str(p.id),
                    'reference': p.reference,
                    'amount': p.amount,
                    'fee': p.fee,
                    'net_amount': p.net_amount,
                    'status': p.status,
                    'status_display': p.get_status_display(),
                    'operator': p.payout_account.operator,
                    'operator_display': p.payout_account.get_operator_display(),
                    'phone_number': p.payout_account.phone_number,
                    'order_numero': p.order.numero if p.order else None,
                    'is_automatic': p.is_automatic,
                    'scheduled_at': p.scheduled_at,
                    'completed_at': p.completed_at,
                    'error_message': p.error_message,
                    'created': p.created,
                }
                for p in payouts
            ],
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count,
            }
        }
    
    @classmethod
    def cancel_payout_request(cls, payout_request: PayoutRequest, reason: str = '') -> bool:
        """
        Annule une demande de payout (si elle n'a pas encore été exécutée).
        """
        if payout_request.status in ['completed', 'processing']:
            return False
        
        with transaction.atomic():
            # Remettre l'argent dans le wallet
            if payout_request.status == 'scheduled':
                payout_request.wallet.release_pending(payout_request.amount)
            
            # Pour les payouts manuels, recréditer
            if not payout_request.is_automatic and payout_request.status == 'pending':
                payout_request.wallet.balance += payout_request.amount
                payout_request.wallet.total_withdrawn -= payout_request.amount
                payout_request.wallet.save()
            
            payout_request.status = 'cancelled'
            payout_request.error_message = reason or "Annulé par l'utilisateur"
            payout_request.save()
        
        logger.info(f"Payout {payout_request.reference} annulé: {reason}")
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════════
    # MÉTHODES POUR TÂCHES CELERY
    # ═══════════════════════════════════════════════════════════════════════════
    
    @classmethod
    def execute_order_payout(cls, order: Order) -> Dict[str, Any]:
        """
        Exécute le payout pour une commande livrée.
        Appelé par la tâche Celery après le délai de sécurité.
        
        Args:
            order: La commande à payer
            
        Returns:
            Dict avec success, amount, transaction_id, etc.
        """
        from apps.core.services import PaymentGatewayService
        from apps.core.services.wallet import WalletService
        
        # Vérifications
        if order.payout_status == 'completed':
            return {'success': False, 'error': 'Payout déjà effectué'}
        
        # Accepter 'paid' ou 'escrow' (argent bloqué prêt pour payout)
        if order.payment_status not in ('paid', 'escrow'):
            return {'success': False, 'error': 'Commande non payée'}
        
        if order.statut != 'delivered':
            return {'success': False, 'error': 'Commande non livrée'}
        
        # Récupérer le compte de payout du prestataire
        payout_account = ProviderPayoutAccount.objects.filter(
            provider=order.provider,
            is_primary=True
        ).first()
        
        if not payout_account:
            return {'success': False, 'error': 'Aucun compte de payout configuré'}
        
        # Calculer le montant net
        platform = cls.get_platform_settings()
        breakdown = platform.calculate_provider_payout(
            order.total_final or order.total_estime
        )
        net_payout = breakdown['net_payout']
        
        try:
            with transaction.atomic():
                # Marquer le payout comme en cours
                order.payout_status = 'processing'
                order.save(update_fields=['payout_status'])
                
                # Envoyer le payout via la passerelle
                result = PaymentGatewayService.send_payout(
                    amount=net_payout,
                    phone_number=payout_account.phone_number,
                    operator=payout_account.operator,
                    reference=f"PRESSO_{order.numero}",
                    provider_name=order.provider.nom_commercial,
                    metadata={
                        'order_id': str(order.id),
                        'order_numero': order.numero,
                    }
                )
                
                if result.get('success'):
                    # Créditer le wallet du prestataire
                    WalletService.credit_order_payment(order)
                    
                    # Marquer le payout comme terminé
                    order.payout_status = 'completed'
                    order.payout_completed_at = timezone.now()
                    order.save(update_fields=['payout_status', 'payout_completed_at'])
                    
                    logger.info(f"✅ Payout commande {order.numero}: {net_payout} FCFA")
                    
                    return {
                        'success': True,
                        'amount': net_payout,
                        'transaction_id': result.get('transaction_id'),
                        'order_numero': order.numero,
                    }
                else:
                    # Échec - marquer pour retry
                    order.payout_status = 'failed'
                    order.save(update_fields=['payout_status'])
                    
                    return {
                        'success': False,
                        'error': result.get('error', 'Erreur de paiement'),
                    }
                    
        except Exception as e:
            logger.error(f"❌ Erreur payout commande {order.numero}: {e}")
            order.payout_status = 'failed'
            order.save(update_fields=['payout_status'])
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def execute_payout_request(cls, payout_request: PayoutRequest) -> Dict[str, Any]:
        """
        Exécute une demande de retrait manuel.
        
        Args:
            payout_request: La demande de payout
            
        Returns:
            Dict avec success, amount, transaction_id, etc.
        """
        from apps.core.services import PaymentGatewayService
        
        if payout_request.status not in ['pending', 'failed']:
            return {'success': False, 'error': f'Statut invalide: {payout_request.status}'}
        
        try:
            # Marquer comme en cours
            payout_request.mark_processing()
            
            # Envoyer le payout
            result = PaymentGatewayService.send_payout(
                amount=payout_request.net_amount,
                phone_number=payout_request.payout_account.phone_number,
                operator=payout_request.payout_account.operator,
                reference=payout_request.reference,
                metadata={
                    'payout_request_id': str(payout_request.id),
                    'provider_id': str(payout_request.provider.id),
                }
            )
            
            if result.get('success'):
                payout_request.moneroo_payout_id = result.get('transaction_id', '')
                payout_request.mark_completed()
                
                logger.info(f"✅ Retrait {payout_request.reference} effectué")
                
                return {
                    'success': True,
                    'amount': payout_request.net_amount,
                    'transaction_id': result.get('transaction_id'),
                    'reference': payout_request.reference,
                }
            else:
                error = result.get('error', 'Erreur inconnue')
                payout_request.mark_failed(error, should_retry=True)
                return {'success': False, 'error': error}
                
        except Exception as e:
            logger.error(f"❌ Erreur retrait {payout_request.reference}: {e}")
            payout_request.mark_failed(str(e), should_retry=True)
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def retry_payout(cls, payout_request: PayoutRequest) -> Dict[str, Any]:
        """
        Réessaie un payout qui a échoué.
        
        Args:
            payout_request: La demande de payout échouée
            
        Returns:
            Dict avec success, etc.
        """
        if payout_request.status != 'failed':
            return {'success': False, 'error': 'Payout non en échec'}
        
        if payout_request.retry_count >= 3:
            payout_request.should_retry = False
            payout_request.error_message = "Nombre max de tentatives atteint"
            payout_request.save()
            return {'success': False, 'error': 'Max retries exceeded'}
        
        # Incrémenter le compteur de retry
        payout_request.retry_count += 1
        payout_request.save(update_fields=['retry_count'])
        
        # Si lié à une commande
        if payout_request.order:
            return cls.execute_order_payout(payout_request.order)
        else:
            return cls.execute_payout_request(payout_request)
