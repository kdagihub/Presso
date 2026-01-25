"""
Système de notification unifié pour PRESSO

Supporte 3 canaux :
1. WebSocket (temps réel si connecté)
2. Push Notification (FCM si déconnecté mais app installée)
3. SMS (Orange API si pas d'internet)
"""
import logging
from typing import Dict, List, Optional
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """
    Service centralisé pour envoyer des notifications via différents canaux
    """
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        channels: Optional[List[str]] = None
    ):
        """
        Envoyer une notification via les canaux spécifiés
        
        Args:
            user_id: ID de l'utilisateur destinataire
            notification_type: Type de notification (order_created, etc.)
            title: Titre de la notification
            message: Message de la notification
            data: Données supplémentaires (optionnel)
            channels: Liste des canaux à utiliser (websocket, push, sms)
                     Si None, utilise tous les canaux activés
        """
        if data is None:
            data = {}
        
        if channels is None:
            # Utiliser tous les canaux activés par défaut
            channels = [
                key for key, enabled in settings.NOTIFICATION_CHANNELS.items()
                if enabled
            ]
        
        notification_data = {
            'type': notification_type,
            'title': title,
            'message': message,
            'data': data,
            'timestamp': None,  # Sera ajouté automatiquement
        }
        
        # Essayer d'envoyer via chaque canal
        for channel in channels:
            try:
                if channel == 'websocket':
                    self._send_websocket(user_id, notification_data)
                elif channel == 'push':
                    self._send_push(user_id, notification_data)
                elif channel == 'sms':
                    self._send_sms(user_id, notification_data)
            except Exception as e:
                logger.error(f"Failed to send notification via {channel}: {str(e)}")
    
    def _send_websocket(self, user_id: str, notification: Dict):
        """
        Envoyer notification via WebSocket (si utilisateur connecté)
        """
        if not settings.NOTIFICATION_CHANNELS.get('websocket', True):
            return
        
        try:
            async_to_sync(self.channel_layer.group_send)(
                f'notifications_{user_id}',
                {
                    'type': 'notification_message',
                    'notification': notification
                }
            )
            logger.info(f"WebSocket notification sent to user {user_id}")
        except Exception as e:
            logger.warning(f"WebSocket notification failed for user {user_id}: {str(e)}")
    
    def _send_push(self, user_id: str, notification: Dict):
        """
        Envoyer push notification via FCM (si utilisateur a l'app)
        """
        if not settings.NOTIFICATION_CHANNELS.get('push', True):
            return
        
        if not settings.FCM_CREDENTIALS_PATH:
            logger.warning("FCM not configured (FCM_CREDENTIALS_PATH missing), skipping push notification")
            return
        
        try:
            # Import delayed pour éviter les erreurs si FCM pas configuré
            from apps.core.utils.fcm import send_fcm_multicast, FIREBASE_AVAILABLE
            from apps.users.models import UserFCMToken
            
            if not FIREBASE_AVAILABLE:
                logger.warning("Firebase Admin SDK not available")
                return
            
            # Récupérer les tokens FCM actifs de l'utilisateur
            fcm_tokens = UserFCMToken.get_active_tokens_for_user(user_id)
            
            if not fcm_tokens:
                logger.debug(f"No FCM tokens for user {user_id}, skipping push notification")
                return
            
            # Envoyer la notification à tous les devices
            result = send_fcm_multicast(fcm_tokens, notification)
            
            # Désactiver les tokens qui ont échoué (invalid tokens)
            if result.get('failure_count', 0) > 0 and result.get('responses'):
                for i, response in enumerate(result['responses']):
                    if hasattr(response, 'exception') and response.exception:
                        # Token invalide - le désactiver
                        error_code = getattr(response.exception, 'code', '')
                        if error_code in ['UNREGISTERED', 'INVALID_ARGUMENT']:
                            try:
                                token_to_deactivate = fcm_tokens[i]
                                UserFCMToken.objects.filter(token=token_to_deactivate).update(is_active=False)
                                logger.info(f"Deactivated invalid FCM token for user {user_id}")
                            except (IndexError, Exception) as e:
                                logger.warning(f"Could not deactivate token: {e}")
            
            logger.info(
                f"Push notification sent to user {user_id}: "
                f"{result.get('success_count', 0)} success, {result.get('failure_count', 0)} failed"
            )
        except Exception as e:
            logger.warning(f"Push notification failed for user {user_id}: {str(e)}")
    
    def _send_sms(self, user_id: str, notification: Dict):
        """
        Envoyer notification via SMS (fallback si pas d'internet)
        """
        if not settings.NOTIFICATION_CHANNELS.get('sms', True):
            return
        
        try:
            # Import delayed
            from apps.core.tasks import send_sms_async
            
            # Récupérer le numéro de téléphone
            user = User.objects.get(id=user_id)
            if not user.phone:
                return
            
            # Formater le message SMS (max 160 caractères)
            sms_message = f"{notification['title']}: {notification['message']}"
            if len(sms_message) > 160:
                sms_message = sms_message[:157] + "..."
            
            # Envoyer via Celery (async)
            send_sms_async.delay(user.phone, sms_message, tag='notification')
            logger.info(f"SMS notification queued for user {user_id}")
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found for SMS notification")
        except Exception as e:
            logger.error(f"SMS notification failed for user {user_id}: {str(e)}")


# Instance globale du service
notification_service = NotificationService()


def send_order_notification(order_id: str, notification_type: str):
    """
    Helper: Envoyer une notification liée à une commande
    
    Args:
        order_id: ID de la commande
        notification_type: Type de notification (order_created, order_ready, etc.)
    """
    from apps.orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
        
        # Déterminer le destinataire
        if notification_type == 'order_created':
            # Notifier le prestataire
            user_id = str(order.provider.user.id) if hasattr(order.provider, 'user') else None
            title = "Nouvelle commande"
            message = f"Commande #{order.numero_commande} reçue"
        else:
            # Notifier le client
            user_id = str(order.client.id)
            title = settings.NOTIFICATION_TYPES.get(notification_type, {}).get('title', 'Notification')
            message = f"Commande #{order.numero_commande}"
        
        if user_id:
            notification_service.send_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                data={'order_id': str(order_id)}
            )
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")

