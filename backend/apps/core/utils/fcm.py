"""
Firebase Cloud Messaging (FCM) - Push Notifications
"""
import logging
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Import conditionnel de Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    
    # Initialiser Firebase Admin SDK
    def initialize_firebase():
        """
        Initialiser Firebase Admin SDK avec les credentials
        """
        if not firebase_admin._apps:
            if settings.FCM_CREDENTIALS_PATH:
                cred = credentials.Certificate(settings.FCM_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized")
            else:
                logger.warning("FCM_CREDENTIALS_PATH not configured")
    
    FIREBASE_AVAILABLE = True
except ImportError:
    logger.warning("firebase-admin not installed, push notifications disabled")
    FIREBASE_AVAILABLE = False
    
    def initialize_firebase():
        pass


def send_fcm_notification(
    fcm_token: str,
    notification: Dict,
    priority: str = 'high'
) -> bool:
    """
    Envoyer une push notification via FCM
    
    Args:
        fcm_token: Token FCM du device de l'utilisateur
        notification: Dict contenant title, message, data
        priority: Priorité (high, normal)
    
    Returns:
        bool: True si succès, False sinon
    """
    if not FIREBASE_AVAILABLE:
        logger.warning("Firebase not available, cannot send push notification")
        return False
    
    if not fcm_token:
        logger.warning("No FCM token provided")
        return False
    
    try:
        initialize_firebase()
        
        # Construire le message FCM
        message = messaging.Message(
            notification=messaging.Notification(
                title=notification.get('title', 'PRESSO'),
                body=notification.get('message', ''),
            ),
            data=notification.get('data', {}),
            android=messaging.AndroidConfig(
                priority=priority,
                notification=messaging.AndroidNotification(
                    sound='default',
                    channel_id='presso_notifications',
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1,
                    ),
                ),
            ),
            token=fcm_token,
        )
        
        # Envoyer le message
        response = messaging.send(message)
        logger.info(f"FCM notification sent successfully: {response}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send FCM notification: {str(e)}")
        return False


def send_fcm_multicast(
    fcm_tokens: list,
    notification: Dict,
    priority: str = 'high'
) -> Dict:
    """
    Envoyer une push notification à plusieurs devices
    
    Args:
        fcm_tokens: Liste de tokens FCM
        notification: Dict contenant title, message, data
        priority: Priorité (high, normal)
    
    Returns:
        Dict: {success_count, failure_count, responses}
    """
    if not FIREBASE_AVAILABLE:
        logger.warning("Firebase not available")
        return {'success_count': 0, 'failure_count': len(fcm_tokens)}
    
    if not fcm_tokens:
        return {'success_count': 0, 'failure_count': 0}
    
    try:
        initialize_firebase()
        
        # Convertir toutes les valeurs de data en strings (requis par FCM)
        raw_data = notification.get('data', {})
        data = {k: str(v) if v is not None else '' for k, v in raw_data.items()}
        
        success_count = 0
        failure_count = 0
        
        # Envoyer à chaque token individuellement (plus fiable que multicast)
        for token in fcm_tokens:
            try:
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=notification.get('title', 'PRESSOW'),
                        body=notification.get('message', ''),
                    ),
                    data=data,
                    android=messaging.AndroidConfig(
                        priority=priority,
                        notification=messaging.AndroidNotification(
                            sound='default',
                            channel_id='presso_notifications',
                        ),
                    ),
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                sound='default',
                                badge=1,
                            ),
                        ),
                    ),
                    token=token,
                )
                
                response = messaging.send(message)
                logger.info(f"FCM sent to device: {response}")
                success_count += 1
            except Exception as token_error:
                logger.warning(f"FCM failed for token: {token_error}")
                failure_count += 1
        
        logger.info(f"FCM batch sent: {success_count} success, {failure_count} failures")
        
        return {
            'success_count': success_count,
            'failure_count': failure_count,
        }
    
    except Exception as e:
        logger.error(f"Failed to send FCM multicast: {str(e)}")
        return {
            'success_count': 0,
            'failure_count': len(fcm_tokens),
            'error': str(e)
        }


def subscribe_to_topic(fcm_token: str, topic: str) -> bool:
    """
    Souscrire un device à un topic FCM
    
    Args:
        fcm_token: Token FCM du device
        topic: Nom du topic (ex: 'all_users', 'providers', 'clients')
    
    Returns:
        bool: True si succès
    """
    if not FIREBASE_AVAILABLE:
        return False
    
    try:
        initialize_firebase()
        response = messaging.subscribe_to_topic([fcm_token], topic)
        logger.info(f"Subscribed to topic {topic}: {response.success_count} success")
        return response.success_count > 0
    except Exception as e:
        logger.error(f"Failed to subscribe to topic: {str(e)}")
        return False


def send_to_topic(topic: str, notification: Dict) -> bool:
    """
    Envoyer une notification à tous les devices d'un topic
    
    Args:
        topic: Nom du topic
        notification: Dict contenant title, message, data
    
    Returns:
        bool: True si succès
    """
    if not FIREBASE_AVAILABLE:
        return False
    
    try:
        initialize_firebase()
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=notification.get('title', 'PRESSO'),
                body=notification.get('message', ''),
            ),
            data=notification.get('data', {}),
            topic=topic,
        )
        
        response = messaging.send(message)
        logger.info(f"Sent to topic {topic}: {response}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send to topic: {str(e)}")
        return False

