"""
Service de passerelle de paiement unifié.
Supporte CinetPay, Moneroo, et le mode simulation locale.

MODÈLE ÉCONOMIQUE:
==================
Client paie 500 FCFA → CinetPay prélève ~3% (Collect) → Pressow reçoit 485 FCFA
→ Commission Pressow 3% = 15 FCFA → À reverser au prestataire 485 FCFA
→ CinetPay prélève ~1.5% (Payout) → Prestataire reçoit ~478 FCFA

Total prélevé : ~7.5%
Prestataire garde : ~92.5%
"""
import logging
import uuid
from decimal import Decimal
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# Stockage en mémoire des transactions simulées
_simulated_transactions: Dict[str, Dict[str, Any]] = {}


class PaymentGatewayService:
    """
    Service unifié pour les paiements.
    Détecte automatiquement la passerelle configurée.
    """
    
    # Frais par opérateur (CinetPay)
    COLLECT_FEES = {
        'orange': Decimal('3.00'),
        'mtn': Decimal('1.80'),
        'wave': Decimal('2.00'),
        'moov': Decimal('2.50'),
        'visa': Decimal('3.50'),
        'mastercard': Decimal('3.50'),
    }
    
    PAYOUT_FEES = {
        'orange': Decimal('1.50'),
        'mtn': Decimal('1.30'),
        'wave': Decimal('2.00'),
        'moov': Decimal('1.80'),
    }
    
    @classmethod
    def get_platform_settings(cls):
        """Récupère les paramètres de la plateforme."""
        from apps.core.models import PlatformSettings
        return PlatformSettings.get_settings()
    
    @classmethod
    def is_simulation_mode(cls) -> bool:
        """Vérifie si on est en mode simulation."""
        settings = cls.get_platform_settings()
        return settings.is_simulation_mode()
    
    @classmethod
    def get_gateway(cls) -> str:
        """Retourne la passerelle configurée."""
        settings = cls.get_platform_settings()
        if cls.is_simulation_mode():
            return 'simulation'
        return settings.payment_gateway
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CALCULS FINANCIERS
    # ═══════════════════════════════════════════════════════════════════════════
    
    @classmethod
    def calculate_order_breakdown(
        cls,
        order_amount: Decimal,
        operator: str = 'orange'
    ) -> Dict[str, Any]:
        """
        Calcule la répartition complète pour une commande.
        
        Args:
            order_amount: Montant de la commande
            operator: Opérateur Mobile Money (orange, mtn, wave, moov)
            
        Returns:
            Dict avec tous les montants détaillés
        """
        settings = cls.get_platform_settings()
        
        # Frais Collect (selon opérateur ou valeur par défaut)
        collect_fee_pct = cls.COLLECT_FEES.get(operator, settings.collect_fee_percent)
        collect_fee = (order_amount * collect_fee_pct / Decimal('100')).quantize(Decimal('1'))
        
        # Ce que Pressow reçoit après Collect
        net_received = order_amount - collect_fee
        
        # Commission Pressow
        commission_pct = settings.commission_percent
        commission = (order_amount * commission_pct / Decimal('100')).quantize(Decimal('1'))
        
        # Montant à reverser au prestataire (avant payout)
        gross_payout = order_amount - commission
        
        # Frais Payout (selon opérateur ou valeur par défaut)
        payout_fee_pct = cls.PAYOUT_FEES.get(operator, settings.payout_fee_percent)
        payout_fee = (gross_payout * payout_fee_pct / Decimal('100')).quantize(Decimal('1'))
        
        # Ce que le prestataire recevra vraiment
        net_payout = gross_payout - payout_fee
        
        # Marge nette Pressow
        total_fees = collect_fee + payout_fee
        pressow_net_margin = commission - total_fees
        
        # Pourcentages
        total_deducted_pct = (
            (order_amount - net_payout) / order_amount * Decimal('100')
        ).quantize(Decimal('0.1'))
        
        provider_keeps_pct = (
            net_payout / order_amount * Decimal('100')
        ).quantize(Decimal('0.1'))
        
        return {
            # Montants
            'order_amount': order_amount,
            'collect_fee': collect_fee,
            'net_received': net_received,
            'commission': commission,
            'gross_payout': gross_payout,
            'payout_fee': payout_fee,
            'net_payout': net_payout,
            'pressow_net_margin': pressow_net_margin,
            
            # Pourcentages
            'collect_fee_percent': collect_fee_pct,
            'commission_percent': commission_pct,
            'payout_fee_percent': payout_fee_pct,
            'total_deducted_percent': total_deducted_pct,
            'provider_keeps_percent': provider_keeps_pct,
            
            # Métadonnées
            'operator': operator,
            'currency': 'XOF',
        }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # COLLECT (Encaissement client)
    # ═══════════════════════════════════════════════════════════════════════════
    
    @classmethod
    def initiate_payment(
        cls,
        amount: Decimal,
        order_id: str,
        order_numero: str,
        customer_phone: str,
        customer_name: str = '',
        customer_email: str = '',
        description: str = '',
        return_url: str = '',
        notify_url: str = '',
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Initie un paiement (Collect).
        
        Args:
            amount: Montant en FCFA
            order_id: ID de la commande
            order_numero: Numéro de la commande
            customer_phone: Téléphone du client
            customer_name: Nom du client
            description: Description du paiement
            return_url: URL de retour après paiement
            notify_url: URL de notification (webhook)
            
        Returns:
            Dict avec payment_url, transaction_id, etc.
        """
        gateway = cls.get_gateway()
        
        if gateway == 'simulation':
            return cls._simulate_initiate_payment(
                amount, order_id, order_numero, customer_phone,
                customer_name, metadata
            )
        elif gateway == 'cinetpay':
            return cls._cinetpay_initiate_payment(
                amount, order_id, order_numero, customer_phone,
                customer_name, customer_email, description,
                return_url, notify_url, metadata
            )
        else:
            # Fallback simulation
            logger.warning(f"Gateway {gateway} non supportée, utilisation simulation")
            return cls._simulate_initiate_payment(
                amount, order_id, order_numero, customer_phone,
                customer_name, metadata
            )
    
    @classmethod
    def verify_payment(cls, transaction_id: str) -> Dict[str, Any]:
        """Vérifie le statut d'un paiement."""
        gateway = cls.get_gateway()
        
        if gateway == 'simulation':
            return cls._simulate_verify_payment(transaction_id)
        elif gateway == 'cinetpay':
            return cls._cinetpay_verify_payment(transaction_id)
        else:
            return cls._simulate_verify_payment(transaction_id)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PAYOUT (Virement prestataire)
    # ═══════════════════════════════════════════════════════════════════════════
    
    @classmethod
    def send_payout(
        cls,
        amount: Decimal,
        phone_number: str,
        operator: str,
        reference: str,
        provider_name: str = '',
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Envoie un virement au prestataire (Payout).
        
        Args:
            amount: Montant à envoyer (net, après commission)
            phone_number: Numéro Mobile Money du prestataire
            operator: Opérateur (orange, mtn, wave, moov)
            reference: Référence interne
            provider_name: Nom du prestataire
            
        Returns:
            Dict avec transaction_id, status, etc.
        """
        gateway = cls.get_gateway()
        
        logger.info(f"Payout: {amount} FCFA vers {phone_number} ({operator}) via {gateway}")
        
        if gateway == 'simulation':
            return cls._simulate_send_payout(
                amount, phone_number, operator, reference, metadata
            )
        elif gateway == 'cinetpay':
            return cls._cinetpay_send_payout(
                amount, phone_number, operator, reference,
                provider_name, metadata
            )
        else:
            return cls._simulate_send_payout(
                amount, phone_number, operator, reference, metadata
            )
    
    # ═══════════════════════════════════════════════════════════════════════════
    # SIMULATION LOCALE
    # ═══════════════════════════════════════════════════════════════════════════
    
    @classmethod
    def _simulate_initiate_payment(
        cls,
        amount: Decimal,
        order_id: str,
        order_numero: str,
        customer_phone: str,
        customer_name: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Simule l'initiation d'un paiement."""
        tx_id = f"SIM_PAY_{uuid.uuid4().hex[:12].upper()}"
        
        _simulated_transactions[tx_id] = {
            'id': tx_id,
            'type': 'payment',
            'amount': int(amount),
            'currency': 'XOF',
            'order_id': order_id,
            'order_numero': order_numero,
            'customer_phone': customer_phone,
            'customer_name': customer_name,
            'status': 'pending',
            'metadata': metadata or {},
            'created_at': timezone.now().isoformat(),
        }
        
        logger.info(f"[SIMULATION] Paiement initié: {tx_id} - {amount} FCFA")
        
        return {
            'success': True,
            'transaction_id': tx_id,
            'payment_url': f'/api/simulation/payment/{tx_id}/confirm/',
            'status': 'pending',
            'message': '[SIMULATION] Appelez /api/simulation/payment/{id}/confirm/ pour confirmer',
        }
    
    @classmethod
    def _simulate_verify_payment(cls, transaction_id: str) -> Dict[str, Any]:
        """Vérifie un paiement simulé."""
        tx = _simulated_transactions.get(transaction_id, {})
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': tx.get('status', 'unknown'),
            'amount': tx.get('amount', 0),
            'currency': 'XOF',
        }
    
    @classmethod
    def _simulate_send_payout(
        cls,
        amount: Decimal,
        phone_number: str,
        operator: str,
        reference: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Simule l'envoi d'un payout."""
        tx_id = f"SIM_POUT_{uuid.uuid4().hex[:12].upper()}"
        
        _simulated_transactions[tx_id] = {
            'id': tx_id,
            'type': 'payout',
            'amount': int(amount),
            'currency': 'XOF',
            'phone_number': phone_number,
            'operator': operator,
            'reference': reference,
            'status': 'success',  # Succès instantané en simulation
            'metadata': metadata or {},
            'created_at': timezone.now().isoformat(),
            'completed_at': timezone.now().isoformat(),
        }
        
        logger.info(f"[SIMULATION] Payout réussi: {tx_id} - {amount} FCFA vers {phone_number}")
        
        return {
            'success': True,
            'transaction_id': tx_id,
            'status': 'success',
            'message': f'[SIMULATION] Virement de {amount} FCFA vers {phone_number} ({operator})',
        }
    
    @classmethod
    def simulate_confirm_payment(cls, transaction_id: str) -> Dict[str, Any]:
        """Confirme manuellement un paiement simulé."""
        tx = _simulated_transactions.get(transaction_id)
        
        if not tx:
            return {'success': False, 'error': 'Transaction non trouvée'}
        
        if tx['type'] != 'payment':
            return {'success': False, 'error': 'Ce n\'est pas un paiement'}
        
        if tx['status'] != 'pending':
            return {'success': False, 'error': f'Paiement déjà {tx["status"]}'}
        
        tx['status'] = 'success'
        tx['paid_at'] = timezone.now().isoformat()
        
        logger.info(f"[SIMULATION] Paiement confirmé: {transaction_id}")
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'status': 'success',
            'order_id': tx.get('order_id'),
        }
    
    @classmethod
    def get_simulated_transactions(cls, tx_type: str = None) -> list:
        """Liste les transactions simulées."""
        txs = list(_simulated_transactions.values())
        if tx_type:
            txs = [t for t in txs if t.get('type') == tx_type]
        return sorted(txs, key=lambda x: x.get('created_at', ''), reverse=True)
    
    @classmethod
    def clear_simulated_transactions(cls) -> int:
        """Efface les transactions simulées."""
        count = len(_simulated_transactions)
        _simulated_transactions.clear()
        return count
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CINETPAY (À implémenter quand tu auras le compte)
    # ═══════════════════════════════════════════════════════════════════════════
    
    @classmethod
    def _cinetpay_initiate_payment(
        cls,
        amount: Decimal,
        order_id: str,
        order_numero: str,
        customer_phone: str,
        customer_name: str,
        customer_email: str,
        description: str,
        return_url: str,
        notify_url: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Initie un paiement via CinetPay.
        
        Documentation: https://docs.cinetpay.com/
        """
        # TODO: Implémenter quand tu auras les clés CinetPay
        # 
        # import requests
        # 
        # settings = cls.get_platform_settings()
        # 
        # payload = {
        #     'apikey': settings.gateway_api_key,
        #     'site_id': settings.gateway_site_id,
        #     'transaction_id': f'PRESSO_{order_numero}_{uuid.uuid4().hex[:8]}',
        #     'amount': int(amount),
        #     'currency': 'XOF',
        #     'description': description or f'Commande {order_numero}',
        #     'customer_name': customer_name,
        #     'customer_surname': '',
        #     'customer_email': customer_email,
        #     'customer_phone_number': customer_phone,
        #     'customer_address': '',
        #     'customer_city': 'Abidjan',
        #     'customer_country': 'CI',
        #     'return_url': return_url,
        #     'notify_url': notify_url,
        #     'channels': 'ALL',
        #     'metadata': str(metadata or {}),
        # }
        # 
        # response = requests.post(
        #     'https://api-checkout.cinetpay.com/v2/payment',
        #     json=payload
        # )
        # 
        # if response.status_code == 200:
        #     data = response.json()
        #     return {
        #         'success': True,
        #         'transaction_id': data.get('data', {}).get('payment_token'),
        #         'payment_url': data.get('data', {}).get('payment_url'),
        #         'status': 'pending',
        #     }
        
        logger.warning("CinetPay non configuré, utilisation de la simulation")
        return cls._simulate_initiate_payment(
            amount, order_id, order_numero, customer_phone,
            customer_name, metadata
        )
    
    @classmethod
    def _cinetpay_verify_payment(cls, transaction_id: str) -> Dict[str, Any]:
        """Vérifie un paiement CinetPay."""
        # TODO: Implémenter
        return cls._simulate_verify_payment(transaction_id)
    
    @classmethod
    def _cinetpay_send_payout(
        cls,
        amount: Decimal,
        phone_number: str,
        operator: str,
        reference: str,
        provider_name: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Envoie un payout via CinetPay Mass Payout."""
        # TODO: Implémenter
        return cls._simulate_send_payout(
            amount, phone_number, operator, reference, metadata
        )
