"""
Service d'intégration avec Moneroo.
Gère les paiements (collect) et les virements (payout) via l'API Moneroo.

Documentation Moneroo: https://docs.moneroo.io/

MODE SIMULATION LOCALE:
=======================
Ce service fonctionne en mode simulation quand:
- sandbox_mode = True ET api_key est vide
- Tous les paiements/payouts sont simulés instantanément
- Utile pour tester le flux complet sans compte Moneroo

Pour passer en mode réel:
1. Créer un compte sur moneroo.io
2. Récupérer les clés API (sandbox ou production)
3. Configurer dans PlatformSettings ou settings.py
"""
import logging
import uuid
import time
from decimal import Decimal
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone

from apps.core.models import PlatformSettings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SIMULATION STORAGE (pour garder l'état des transactions mockées)
# ═══════════════════════════════════════════════════════════════════════════════

# Stockage en mémoire des transactions simulées (en production, utiliser Redis/DB)
_mock_transactions: Dict[str, Dict[str, Any]] = {}


class MonerooService:
    """
    Service pour interagir avec l'API Moneroo.
    
    Fonctionnalités:
    - Collect (encaissement): Recevoir un paiement du client
    - Payout (décaissement): Envoyer de l'argent au prestataire
    """
    
    # Mapping des opérateurs vers les codes Moneroo
    OPERATOR_MAPPING = {
        'orange': 'orange_ci',
        'mtn': 'mtn_ci',
        'moov': 'moov_ci',
        'wave': 'wave_ci',
    }
    
    @classmethod
    def get_api_config(cls) -> Dict[str, Any]:
        """
        Récupère la configuration API Moneroo.
        """
        try:
            platform = PlatformSettings.objects.first()
            if platform:
                return {
                    'api_key': platform.moneroo_api_key,
                    'webhook_secret': platform.moneroo_webhook_secret,
                    'sandbox_mode': platform.moneroo_sandbox_mode,
                }
        except Exception:
            pass
        
        # Fallback sur les settings Django
        return {
            'api_key': getattr(settings, 'MONEROO_API_KEY', ''),
            'webhook_secret': getattr(settings, 'MONEROO_WEBHOOK_SECRET', ''),
            'sandbox_mode': getattr(settings, 'MONEROO_SANDBOX_MODE', True),
        }
    
    @classmethod
    def get_base_url(cls) -> str:
        """Retourne l'URL de base de l'API Moneroo."""
        config = cls.get_api_config()
        if config.get('sandbox_mode', True):
            return 'https://sandbox.moneroo.io/v1'
        return 'https://api.moneroo.io/v1'
    
    # ═══════════════════════════════════════════════════════════════════
    # COLLECT (Encaissement - Paiement client)
    # ═══════════════════════════════════════════════════════════════════
    
    @classmethod
    def initiate_payment(
        cls,
        amount: Decimal,
        phone_number: str,
        operator: str,
        order_reference: str,
        customer_email: str = '',
        description: str = '',
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Initie un paiement Mobile Money (collect).
        
        Args:
            amount: Montant en FCFA
            phone_number: Numéro du client (+225...)
            operator: Code opérateur (orange, mtn, moov, wave)
            order_reference: Référence de la commande
            customer_email: Email du client (optionnel)
            description: Description du paiement
            metadata: Données supplémentaires
            
        Returns:
            Dict avec success, transaction_id, checkout_url, etc.
        """
        config = cls.get_api_config()
        
        # En mode développement, simuler le paiement
        if config.get('sandbox_mode', True) and not config.get('api_key'):
            return cls._mock_initiate_payment(
                amount, phone_number, operator, order_reference, metadata
            )
        
        # TODO: Implémenter l'appel réel à l'API Moneroo
        # import requests
        # response = requests.post(
        #     f"{cls.get_base_url()}/payments/initialize",
        #     headers={
        #         'Authorization': f'Bearer {config["api_key"]}',
        #         'Content-Type': 'application/json',
        #     },
        #     json={
        #         'amount': int(amount),
        #         'currency': 'XOF',
        #         'customer': {
        #             'email': customer_email,
        #             'phone': phone_number,
        #         },
        #         'metadata': metadata or {},
        #         'return_url': f'{settings.FRONTEND_URL}/payment/callback',
        #         'description': description or f'Paiement commande {order_reference}',
        #     }
        # )
        
        logger.warning("Moneroo API non configurée. Utilisation du mock.")
        return cls._mock_initiate_payment(
            amount, phone_number, operator, order_reference, metadata
        )
    
    @classmethod
    def verify_payment(cls, transaction_id: str) -> Dict[str, Any]:
        """
        Vérifie le statut d'un paiement.
        
        Args:
            transaction_id: ID de la transaction Moneroo
            
        Returns:
            Dict avec status, amount, etc.
        """
        config = cls.get_api_config()
        
        if config.get('sandbox_mode', True) and not config.get('api_key'):
            return cls._mock_verify_payment(transaction_id)
        
        # TODO: Implémenter l'appel réel
        logger.warning("Moneroo API non configurée. Utilisation du mock.")
        return cls._mock_verify_payment(transaction_id)
    
    # ═══════════════════════════════════════════════════════════════════
    # PAYOUT (Décaissement - Virement prestataire)
    # ═══════════════════════════════════════════════════════════════════
    
    @classmethod
    def send_payout(
        cls,
        phone_number: str,
        amount: Decimal,
        operator: str,
        reference: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Envoie un virement Mobile Money au prestataire (payout).
        
        Args:
            phone_number: Numéro du bénéficiaire (+225...)
            amount: Montant en FCFA
            operator: Code opérateur (orange, mtn, moov, wave)
            reference: Référence interne du payout
            metadata: Données supplémentaires
            
        Returns:
            Dict avec success, transaction_id, etc.
        """
        config = cls.get_api_config()
        
        logger.info(
            f"Envoi payout: {amount} FCFA vers {phone_number} ({operator})"
        )
        
        # En mode développement, simuler le payout
        if config.get('sandbox_mode', True) and not config.get('api_key'):
            return cls._mock_send_payout(
                phone_number, amount, operator, reference, metadata
            )
        
        # TODO: Implémenter l'appel réel à l'API Moneroo
        # moneroo_operator = cls.OPERATOR_MAPPING.get(operator, operator)
        # 
        # import requests
        # response = requests.post(
        #     f"{cls.get_base_url()}/payouts",
        #     headers={
        #         'Authorization': f'Bearer {config["api_key"]}',
        #         'Content-Type': 'application/json',
        #     },
        #     json={
        #         'amount': int(amount),
        #         'currency': 'XOF',
        #         'method': moneroo_operator,
        #         'recipient': {
        #             'phone': phone_number,
        #         },
        #         'metadata': {
        #             'reference': reference,
        #             **(metadata or {}),
        #         },
        #     }
        # )
        # 
        # if response.status_code == 200:
        #     data = response.json()
        #     return {
        #         'success': True,
        #         'transaction_id': data.get('id'),
        #         'status': data.get('status'),
        #     }
        # else:
        #     return {
        #         'success': False,
        #         'error': response.json().get('message', 'Erreur inconnue'),
        #     }
        
        logger.warning("Moneroo API non configurée. Utilisation du mock.")
        return cls._mock_send_payout(
            phone_number, amount, operator, reference, metadata
        )
    
    @classmethod
    def verify_payout(cls, transaction_id: str) -> Dict[str, Any]:
        """
        Vérifie le statut d'un payout.
        
        Args:
            transaction_id: ID de la transaction Moneroo
            
        Returns:
            Dict avec status, etc.
        """
        config = cls.get_api_config()
        
        if config.get('sandbox_mode', True) and not config.get('api_key'):
            return cls._mock_verify_payout(transaction_id)
        
        # TODO: Implémenter l'appel réel
        logger.warning("Moneroo API non configurée. Utilisation du mock.")
        return cls._mock_verify_payout(transaction_id)
    
    # ═══════════════════════════════════════════════════════════════════
    # WEBHOOKS
    # ═══════════════════════════════════════════════════════════════════
    
    @classmethod
    def verify_webhook_signature(cls, payload: bytes, signature: str) -> bool:
        """
        Vérifie la signature d'un webhook Moneroo.
        
        Args:
            payload: Corps de la requête
            signature: Header X-Moneroo-Signature
            
        Returns:
            True si valide
        """
        import hmac
        import hashlib
        
        config = cls.get_api_config()
        secret = config.get('webhook_secret', '')
        
        if not secret:
            logger.warning("Webhook secret non configuré. Signature non vérifiée.")
            return True  # En dev, accepter tout
        
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    @classmethod
    def process_webhook(cls, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un webhook Moneroo.
        
        Args:
            event_type: Type d'événement (payment.success, payout.success, etc.)
            data: Données du webhook
            
        Returns:
            Dict avec le résultat du traitement
        """
        logger.info(f"Webhook Moneroo reçu: {event_type}")
        
        if event_type == 'payment.success':
            return cls._handle_payment_success(data)
        elif event_type == 'payment.failed':
            return cls._handle_payment_failed(data)
        elif event_type == 'payout.success':
            return cls._handle_payout_success(data)
        elif event_type == 'payout.failed':
            return cls._handle_payout_failed(data)
        else:
            logger.warning(f"Type de webhook non géré: {event_type}")
            return {'handled': False, 'reason': 'Unknown event type'}
    
    @classmethod
    def _handle_payment_success(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite un webhook de paiement réussi."""
        from apps.orders.models import Order
        
        transaction_id = data.get('id')
        metadata = data.get('metadata', {})
        order_id = metadata.get('order_id')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.payment_status = 'paid'
                order.moneroo_payment_id = transaction_id
                order.paid_at = timezone.now()
                order.save()
                
                logger.info(f"Paiement confirmé pour commande {order.numero}")
                
                # ═══════════════════════════════════════════════════════════════
                # NOTIFICATION : Paiement reçu pour le prestataire
                # ═══════════════════════════════════════════════════════════════
                try:
                    from apps.core.services.notification_dispatcher import notification_dispatcher
                    notification_dispatcher.notify_provider_payment_received(order)
                except Exception as e:
                    logger.error(f"Erreur envoi notification paiement: {e}")
                
                return {'handled': True, 'order': order.numero}
            except Order.DoesNotExist:
                logger.error(f"Commande {order_id} introuvable")
        
        return {'handled': False, 'reason': 'Order not found'}
    
    @classmethod
    def _handle_payment_failed(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite un webhook de paiement échoué."""
        from apps.orders.models import Order
        
        metadata = data.get('metadata', {})
        order_id = metadata.get('order_id')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order.payment_status = 'failed'
                order.save()
                
                logger.info(f"Paiement échoué pour commande {order.numero}")
                return {'handled': True}
            except Order.DoesNotExist:
                pass
        
        return {'handled': False}
    
    @classmethod
    def _handle_payout_success(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite un webhook de payout réussi."""
        from apps.core.models import PayoutRequest
        
        transaction_id = data.get('id')
        
        try:
            payout = PayoutRequest.objects.get(moneroo_payout_id=transaction_id)
            payout.mark_completed()
            
            # Mettre à jour la commande si liée
            if payout.order:
                payout.order.mark_payout_completed()
            
            logger.info(f"Payout {payout.reference} confirmé")
            return {'handled': True, 'payout': payout.reference}
        except PayoutRequest.DoesNotExist:
            logger.error(f"PayoutRequest avec moneroo_id {transaction_id} introuvable")
        
        return {'handled': False}
    
    @classmethod
    def _handle_payout_failed(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Traite un webhook de payout échoué."""
        from apps.core.models import PayoutRequest
        
        transaction_id = data.get('id')
        error = data.get('error', 'Erreur inconnue')
        
        try:
            payout = PayoutRequest.objects.get(moneroo_payout_id=transaction_id)
            payout.mark_failed(error, should_retry=True)
            
            logger.info(f"Payout {payout.reference} échoué: {error}")
            return {'handled': True}
        except PayoutRequest.DoesNotExist:
            pass
        
        return {'handled': False}
    
    # ═══════════════════════════════════════════════════════════════════
    # MOCKS (Simulation Locale)
    # ═══════════════════════════════════════════════════════════════════
    
    @classmethod
    def _mock_initiate_payment(
        cls,
        amount: Decimal,
        phone_number: str,
        operator: str,
        order_reference: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Mock pour initier un paiement.
        Simule un paiement en attente qui sera confirmé automatiquement.
        """
        mock_id = f"pay_mock_{uuid.uuid4().hex[:12]}"
        
        # Stocker la transaction pour pouvoir la confirmer plus tard
        _mock_transactions[mock_id] = {
            'type': 'payment',
            'id': mock_id,
            'amount': int(amount),
            'currency': 'XOF',
            'phone_number': phone_number,
            'operator': operator,
            'reference': order_reference,
            'metadata': metadata or {},
            'status': 'pending',
            'created_at': timezone.now().isoformat(),
        }
        
        logger.info(f"[SIMULATION] Paiement initié: {mock_id} - {amount} FCFA")
        
        return {
            'success': True,
            'transaction_id': mock_id,
            'checkout_url': f'/api/simulation/payment/{mock_id}/confirm/',
            'status': 'pending',
            'message': '[SIMULATION] Utilisez l\'URL checkout pour confirmer le paiement',
        }
    
    @classmethod
    def _mock_verify_payment(cls, transaction_id: str) -> Dict[str, Any]:
        """Mock pour vérifier un paiement."""
        tx = _mock_transactions.get(transaction_id, {})
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': tx.get('status', 'success'),
            'amount': tx.get('amount', 0),
            'currency': 'XOF',
        }
    
    @classmethod
    def _mock_send_payout(
        cls,
        phone_number: str,
        amount: Decimal,
        operator: str,
        reference: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Mock pour envoyer un payout.
        Simule un payout qui réussit instantanément (en mode simulation).
        """
        mock_id = f"pout_mock_{uuid.uuid4().hex[:12]}"
        
        # Stocker la transaction
        _mock_transactions[mock_id] = {
            'type': 'payout',
            'id': mock_id,
            'amount': int(amount),
            'currency': 'XOF',
            'phone_number': phone_number,
            'operator': operator,
            'reference': reference,
            'metadata': metadata or {},
            'status': 'success',  # En simulation, succès instantané
            'created_at': timezone.now().isoformat(),
            'completed_at': timezone.now().isoformat(),
        }
        
        logger.info(
            f"[SIMULATION] Payout réussi: {mock_id} - {amount} FCFA vers {phone_number} ({operator})"
        )
        
        # En simulation, le payout réussit toujours
        return {
            'success': True,
            'transaction_id': mock_id,
            'status': 'success',
            'message': f'[SIMULATION] Virement de {amount} FCFA envoyé vers {phone_number}',
        }
    
    @classmethod
    def _mock_verify_payout(cls, transaction_id: str) -> Dict[str, Any]:
        """Mock pour vérifier un payout."""
        tx = _mock_transactions.get(transaction_id, {})
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': tx.get('status', 'success'),
            'amount': tx.get('amount', 0),
        }
    
    # ═══════════════════════════════════════════════════════════════════
    # SIMULATION HELPERS (pour tests et développement)
    # ═══════════════════════════════════════════════════════════════════
    
    @classmethod
    def simulate_payment_success(cls, transaction_id: str) -> Dict[str, Any]:
        """
        Simule la confirmation d'un paiement (comme si le client avait payé).
        Utile pour tester le flux complet sans interface de paiement.
        """
        tx = _mock_transactions.get(transaction_id)
        
        if not tx:
            return {'success': False, 'error': 'Transaction non trouvée'}
        
        if tx['type'] != 'payment':
            return {'success': False, 'error': 'Ce n\'est pas un paiement'}
        
        if tx['status'] != 'pending':
            return {'success': False, 'error': f'Paiement déjà {tx["status"]}'}
        
        # Mettre à jour le statut
        tx['status'] = 'success'
        tx['paid_at'] = timezone.now().isoformat()
        _mock_transactions[transaction_id] = tx
        
        # Traiter comme un webhook
        cls.process_webhook('payment.success', {
            'id': transaction_id,
            'status': 'success',
            'amount': tx['amount'],
            'metadata': tx['metadata'],
        })
        
        logger.info(f"[SIMULATION] Paiement confirmé: {transaction_id}")
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'message': 'Paiement simulé avec succès',
        }
    
    @classmethod
    def simulate_payment_failure(cls, transaction_id: str, reason: str = 'Solde insuffisant') -> Dict[str, Any]:
        """
        Simule l'échec d'un paiement.
        """
        tx = _mock_transactions.get(transaction_id)
        
        if not tx:
            return {'success': False, 'error': 'Transaction non trouvée'}
        
        tx['status'] = 'failed'
        tx['error'] = reason
        _mock_transactions[transaction_id] = tx
        
        cls.process_webhook('payment.failed', {
            'id': transaction_id,
            'status': 'failed',
            'error': reason,
            'metadata': tx.get('metadata', {}),
        })
        
        logger.info(f"[SIMULATION] Paiement échoué: {transaction_id} - {reason}")
        
        return {
            'success': True,
            'message': f'Échec de paiement simulé: {reason}',
        }
    
    @classmethod
    def get_mock_transaction(cls, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les détails d'une transaction simulée."""
        return _mock_transactions.get(transaction_id)
    
    @classmethod
    def list_mock_transactions(cls, tx_type: str = None) -> list:
        """Liste toutes les transactions simulées."""
        txs = list(_mock_transactions.values())
        if tx_type:
            txs = [t for t in txs if t.get('type') == tx_type]
        return sorted(txs, key=lambda x: x.get('created_at', ''), reverse=True)
    
    @classmethod
    def clear_mock_transactions(cls) -> int:
        """Efface toutes les transactions simulées."""
        count = len(_mock_transactions)
        _mock_transactions.clear()
        logger.info(f"[SIMULATION] {count} transactions effacées")
        return count
    
    @classmethod
    def is_simulation_mode(cls) -> bool:
        """Vérifie si le service est en mode simulation."""
        config = cls.get_api_config()
        return config.get('sandbox_mode', True) and not config.get('api_key')
