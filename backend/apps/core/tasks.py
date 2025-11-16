"""
Tâches Celery pour PRESSO Core
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='apps.core.tasks.clean_expired_tokens')
def clean_expired_tokens():
    """
    Nettoyer les tokens JWT blacklistés expirés
    Exécuté 1x par jour à 3h du matin
    """
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        
        # Supprimer les tokens expirés depuis plus de 7 jours
        cutoff = timezone.now() - timedelta(days=7)
        deleted_count = OutstandingToken.objects.filter(
            expires_at__lt=cutoff
        ).delete()[0]
        
        logger.info(f"Cleaned {deleted_count} expired JWT tokens")
        return {
            'cleaned': deleted_count,
            'timestamp': timezone.now().isoformat()
        }
    except ImportError:
        logger.warning("JWT token blacklist not installed")
        return {'cleaned': 0, 'error': 'Module not installed'}


@shared_task(name='apps.core.tasks.generate_daily_reports')
def generate_daily_reports():
    """
    Générer les rapports quotidiens
    Exécuté 1x par jour à 6h du matin
    """
    from apps.orders.models import Order
    from apps.providers.models import Provider
    from apps.users.models import User
    
    yesterday = timezone.now() - timedelta(days=1)
    
    stats = {
        'date': yesterday.date().isoformat(),
        'new_users': User.objects.filter(date_inscription__date=yesterday.date()).count(),
        'new_providers': Provider.objects.filter(date_creation__date=yesterday.date()).count(),
        'new_orders': Order.objects.filter(date_creation__date=yesterday.date()).count(),
        'completed_orders': Order.objects.filter(
            date_creation__date=yesterday.date(),
            statut='livre'
        ).count(),
    }
    
    logger.info(f"Daily report generated: {stats}")
    
    # TODO: Envoyer le rapport par email aux admins
    
    return stats


@shared_task(
    name='apps.core.tasks.send_sms_task',
    bind=True,
    max_retries=3,
    default_retry_delay=60  # Retry après 60 secondes
)
def send_sms_task(self, phone_number, message, tag='general'):
    """
    Envoyer un SMS de manière asynchrone via Orange SMS API
    
    Args:
        phone_number: Numéro de téléphone (format international)
        message: Message à envoyer
        tag: Tag pour identifier le type de SMS (otp, notification, etc.)
    
    Returns:
        Dict avec le résultat de l'envoi
    """
    from apps.core.utils.sms import send_sms, increment_sms_stats
    
    try:
        result = send_sms(phone_number, message, tag)
        
        # Incrémenter les stats
        increment_sms_stats(success=True)
        
        logger.info(f"✅ SMS sent successfully to {phone_number}, message_id={result.get('message_id')}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to send SMS to {phone_number}: {str(e)}")
        
        # Incrémenter les stats d'échec
        increment_sms_stats(success=False)
        
        # Retry automatique (3 fois max)
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for SMS to {phone_number}")
            raise


@shared_task(name='apps.core.tasks.send_email_async')
def send_email_async(subject, message, recipient_list, html_message=None):
    """
    Envoyer un email de manière asynchrone
    
    Args:
        subject: Sujet de l'email
        message: Corps du message (texte)
        recipient_list: Liste des destinataires
        html_message: Corps du message (HTML, optionnel)
    """
    from django.core.mail import send_mail
    from django.conf import settings
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Email sent to {recipient_list}: {subject}")
        return {'sent': True, 'recipients': len(recipient_list)}
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise

