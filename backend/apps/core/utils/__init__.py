"""
Utilitaires PRESSO Core
"""

# SMS utilities
from .sms import (
    send_sms,
    send_otp_sms,
    get_sms_stats,
    increment_sms_stats
)

# FCM utilities
from .fcm import (
    send_fcm_notification,
    send_fcm_multicast,
    subscribe_to_topic,
    send_to_topic,
    FIREBASE_AVAILABLE
)

__all__ = [
    # SMS
    'send_sms',
    'send_otp_sms',
    'get_sms_stats',
    'increment_sms_stats',
    
    # FCM
    'send_fcm_notification',
    'send_fcm_multicast',
    'subscribe_to_topic',
    'send_to_topic',
    'FIREBASE_AVAILABLE',
]

