"""
Service de gestion des OTP de livraison.
Gère la génération, l'envoi et la validation des codes OTP.
"""
import logging
from typing import Tuple, Optional
from django.utils import timezone
from django.db import transaction

from apps.orders.models import Order
from apps.core.models import PlatformSettings

logger = logging.getLogger(__name__)


class DeliveryOTPService:
    """
    Service pour gérer les OTP de livraison.
    
    Workflow:
    1. Quand la commande est "ready", générer l'OTP
    2. Envoyer l'OTP au client (SMS/WhatsApp)
    3. Le livreur saisit l'OTP pour valider la livraison
    4. Si valide, déclencher le workflow de payout
    """
    
    @staticmethod
    def get_platform_settings() -> PlatformSettings:
        """Récupère les paramètres de la plateforme."""
        return PlatformSettings.objects.first() or PlatformSettings.objects.create()
    
    @classmethod
    def generate_otp(cls, order: Order, send_notification: bool = True) -> str:
        """
        Génère un nouvel OTP pour une commande.
        
        Args:
            order: La commande pour laquelle générer l'OTP
            send_notification: Si True, envoie une notification au client
            
        Returns:
            Le code OTP généré
        """
        # Vérifier que la commande est dans un état approprié
        if order.statut not in ['ready', 'in_progress', 'collected']:
            logger.warning(
                f"Tentative de génération OTP pour commande {order.numero} "
                f"avec statut invalide: {order.statut}"
            )
        
        # Générer le code
        otp_code = order.generate_delivery_otp()
        
        logger.info(f"OTP généré pour commande {order.numero}: {otp_code}")
        
        # Envoyer la notification au client
        if send_notification:
            cls._send_otp_to_client(order, otp_code)
        
        return otp_code
    
    @classmethod
    def validate_otp(
        cls,
        order: Order,
        code: str,
        validated_by=None
    ) -> Tuple[bool, str]:
        """
        Valide le code OTP de livraison.
        
        Args:
            order: La commande
            code: Le code OTP saisi
            validated_by: L'utilisateur qui valide (livreur/prestataire)
            
        Returns:
            Tuple (success: bool, message: str)
        """
        # Vérifications préliminaires
        if not order.delivery_otp:
            return False, "Aucun code OTP n'a été généré pour cette commande."
        
        if order.delivery_otp_validated_at:
            return False, "Cette commande a déjà été validée."
        
        if order.statut == 'delivered':
            return False, "Cette commande a déjà été livrée."
        
        if order.statut == 'cancelled':
            return False, "Cette commande a été annulée."
        
        # Valider le code
        if not order.validate_delivery_otp(code, validated_by):
            # Vérifier si c'est une erreur de code ou d'expiration
            platform = cls.get_platform_settings()
            validity_minutes = platform.delivery_otp_validity_minutes
            
            if order.delivery_otp_generated_at:
                expiry_time = order.delivery_otp_generated_at + timezone.timedelta(minutes=validity_minutes)
                if timezone.now() > expiry_time:
                    return False, f"Le code OTP a expiré (validité: {validity_minutes} minutes). Demandez un nouveau code."
            
            return False, "Code OTP invalide. Veuillez réessayer."
        
        # OTP valide - procéder à la livraison
        with transaction.atomic():
            # Mettre à jour le statut de la commande
            previous_status = order.statut
            order.statut = 'delivered'
            order.statut_changed_at = timezone.now()
            order.date_livraison = timezone.now()
            order.save(update_fields=[
                'statut', 
                'statut_changed_at', 
                'date_livraison',
                'updated'
            ])
            
            # Logger le changement de statut
            order.log_status(
                event='status_change',
                new_status='delivered',
                previous_status=previous_status,
                comment=f"Livraison validée par OTP",
                performed_by=validated_by,
            )
            
            # Calculer les montants si pas déjà fait
            order.calculate_amounts()
            
            # ═══════════════════════════════════════════════════════════════
            # LIBÉRATION IMMÉDIATE DU PAIEMENT (Nouveau système)
            # Pas de payout automatique différé - l'argent va directement
            # sur le portefeuille du prestataire
            # ═══════════════════════════════════════════════════════════════
            release_result = cls._release_immediate_payment(order)
        
        logger.info(
            f"OTP validé pour commande {order.numero}. "
            f"Paiement libéré immédiatement: {order.provider_net_amount} FCFA. "
            f"Délai réclamation client: {order.claim_deadline}"
        )
        
        return True, f"Livraison validée avec succès ! {order.provider_net_amount} FCFA ont été crédités à votre portefeuille."
    
    @classmethod
    def regenerate_otp(cls, order: Order) -> Tuple[str, str]:
        """
        Régénère un nouveau code OTP (si l'ancien a expiré ou est perdu).
        
        Args:
            order: La commande
            
        Returns:
            Tuple (otp_code: str, message: str)
        """
        if order.delivery_otp_validated_at:
            return '', "Cette commande a déjà été validée. Impossible de régénérer l'OTP."
        
        if order.statut in ['delivered', 'cancelled']:
            return '', f"Impossible de régénérer l'OTP pour une commande {order.get_statut_display()}."
        
        otp_code = cls.generate_otp(order, send_notification=True)
        
        return otp_code, f"Nouveau code OTP généré et envoyé au client."
    
    @classmethod
    def _send_otp_to_client(cls, order: Order, otp_code: str) -> bool:
        """
        Envoie le code OTP au client par SMS/WhatsApp.
        
        TODO: Implémenter l'envoi réel via service de notification
        """
        client = order.client
        client_phone = client.phone
        provider_name = order.provider.nom_commercial
        
        message = (
            f"Presso - Commande {order.numero}\n"
            f"Votre code de livraison: {otp_code}\n"
            f"Donnez ce code au livreur de {provider_name}.\n"
            f"Validité: 60 minutes."
        )
        
        # TODO: Intégrer avec le service SMS (Orange, Twilio, etc.)
        logger.info(
            f"[MOCK] Envoi OTP au client {client_phone}: {message}"
        )
        
        # Pour l'instant, on simule l'envoi
        # En production, utiliser le service de notification
        return True
    
    @classmethod
    def _release_immediate_payment(cls, order: Order, claim_window_minutes: int = 30) -> dict:
        """
        Libère immédiatement le paiement vers le portefeuille du prestataire.
        
        Nouveau système : Pas de payout automatique différé.
        L'argent est crédité directement sur le portefeuille du prestataire
        dès la validation de l'OTP. Le client a ensuite X minutes pour
        faire une réclamation si problème.
        
        Args:
            order: La commande livrée
            claim_window_minutes: Délai en minutes pour réclamation client (défaut: 30)
            
        Returns:
            dict avec les détails de la libération
        """
        try:
            # Utiliser la méthode du modèle Order pour libérer le paiement
            result = order.release_payment_to_provider(claim_window_minutes=claim_window_minutes)
            
            logger.info(
                f"Paiement libéré immédiatement pour commande {order.numero}: "
                f"{order.provider_net_amount} FCFA. "
                f"Réclamation possible jusqu'à {order.claim_deadline}"
            )
            
            # Envoyer notifications
            cls._send_payment_notifications(order)
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur libération paiement commande {order.numero}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def _send_payment_notifications(cls, order: Order) -> None:
        """
        Envoie les notifications après libération du paiement.
        
        - Notifie le prestataire du crédit reçu
        - Notifie le client de la livraison avec délai de réclamation
        """
        try:
            from apps.core.services.notification_dispatcher import notification_dispatcher
            
            # Notifier le prestataire
            try:
                notification_dispatcher.notify_provider_payment_released(
                    order=order,
                    amount=order.provider_net_amount
                )
            except AttributeError:
                # La méthode n'existe peut-être pas encore
                logger.warning("notify_provider_payment_released non disponible")
            
            # Notifier le client
            try:
                notification_dispatcher.notify_client_order_delivered(
                    order=order,
                    claim_deadline=order.claim_deadline
                )
            except AttributeError:
                # La méthode n'existe peut-être pas encore
                logger.warning("notify_client_order_delivered non disponible")
                
        except ImportError as e:
            logger.warning(f"Service notification non disponible: {e}")
        except Exception as e:
            logger.error(f"Erreur envoi notifications paiement: {e}")
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTHODE LEGACY (Commentée - À supprimer plus tard si non nécessaire)
    # ═══════════════════════════════════════════════════════════════════
    
    # @classmethod
    # def _schedule_automatic_payout(cls, order: Order) -> None:
    #     """
    #     [DÉSACTIVÉ] Programme le payout automatique après le délai de sécurité.
    #     Remplacé par _release_immediate_payment() pour un système plus transparent.
    #     """
    #     from apps.core.services.payout import PayoutService
    #     
    #     platform = cls.get_platform_settings()
    #     delay_hours = platform.payout_delay_hours
    #     
    #     order.schedule_payout(delay_hours=delay_hours)
    #     PayoutService.create_payout_request_for_order(order)
    #     
    #     logger.info(
    #         f"Payout automatique programmé pour commande {order.numero} "
    #         f"à {order.payout_scheduled_at}"
    #     )
    
    @classmethod
    def get_otp_status(cls, order: Order) -> dict:
        """
        Retourne le statut de l'OTP pour une commande.
        
        Returns:
            Dict avec les informations sur l'OTP
        """
        platform = cls.get_platform_settings()
        validity_minutes = platform.delivery_otp_validity_minutes
        
        is_expired = False
        if order.delivery_otp_generated_at and not order.delivery_otp_validated_at:
            expiry_time = order.delivery_otp_generated_at + timezone.timedelta(minutes=validity_minutes)
            is_expired = timezone.now() > expiry_time
        
        return {
            'has_otp': bool(order.delivery_otp),
            'otp_generated_at': order.delivery_otp_generated_at,
            'otp_validated_at': order.delivery_otp_validated_at,
            'is_validated': order.delivery_otp_validated_at is not None,
            'is_expired': is_expired,
            'validity_minutes': validity_minutes,
            'can_regenerate': (
                not order.delivery_otp_validated_at 
                and order.statut not in ['delivered', 'cancelled']
            ),
        }
