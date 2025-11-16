"""
Utilitaires SMS (mode placeholder - aucun provider externe actif)
"""
import logging
import time
from typing import Dict

from django.conf import settings  # type: ignore
from django.core.cache import cache  # type: ignore

logger = logging.getLogger(__name__)


def send_sms(msisdn: str, message: str, tag: str = 'general') -> Dict:
    """
    Placeholder d'envoi SMS.
    On log l'information et on retourne un identifiant factice sans contacter de provider.
    """
    message_id = f"dev-{int(time.time() * 1000)}"
    logger.info("📱 [SMS placeholder] to=%s tag=%s message=%s", msisdn, tag, message)
    if not settings.NOTIFICATION_CHANNELS.get('sms', False):
        logger.info("SMS channel disabled via settings.NOTIFICATION_CHANNELS")
    return {
        'success': True,
        'message_id': message_id,
        'to': msisdn,
        'tag': tag,
        'provider': 'placeholder',
    }


def send_otp_sms(phone: str, code: str, purpose: str = 'verification') -> Dict:
    """
    Génère un message OTP standard et délègue à send_sms (placeholder).
    """
    messages = {
        'signup': f"Presso: Votre code de vérification est {code}. Valide 10 minutes. Ne le partagez jamais.",
        'reset_password': f"Presso: Code de réinitialisation: {code}. Valide 10 minutes. Ne le partagez jamais.",
        'phone_verification': f"Presso: Votre code de vérification est {code}. Valide 10 minutes.",
        'login_2fa': f"Presso: Code de connexion: {code}. Valide 10 minutes.",
    }
    message = messages.get(purpose, f"Presso: Votre code est {code}. Valide 10 minutes.")
    return send_sms(phone, message, tag=f'otp_{purpose}')


def get_sms_stats() -> Dict:
    """
    Statistiques d'envoi SMS (via cache ou DB si implémenté)
    
    Returns:
        Dict avec les stats
    """
    # Pour l'instant, on retourne des stats basiques depuis le cache
    stats = {
        'total_sent': cache.get('sms_stats_total_sent', 0),
        'last_24h': cache.get('sms_stats_last_24h', 0),
        'failed': cache.get('sms_stats_failed', 0)
    }
    
    return stats


def increment_sms_stats(success: bool = True):
    """
    Incrémenter les statistiques SMS
    
    Args:
        success: True si envoi réussi
    """
    cache.incr('sms_stats_total_sent', 1)
    
    if success:
        # Compteur sur 24h (expire automatiquement)
        key = 'sms_stats_last_24h'
        count = cache.get(key, 0)
        cache.set(key, count + 1, timeout=86400)  # 24h
    else:
        cache.incr('sms_stats_failed', 1)

