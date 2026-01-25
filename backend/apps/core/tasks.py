"""
Tâches Celery pour PRESSO Core

TÂCHES PLANIFIÉES (Beat Schedule):
==================================
- clean_expired_otp : Toutes les 30 minutes
- clean_expired_tokens : 1x/jour à 3h
- generate_daily_reports : 1x/jour à 6h
- process_pending_payouts : Toutes les 5 minutes
- retry_failed_payouts : Toutes les heures

TÂCHES À LA DEMANDE:
====================
- process_single_payout : Traiter un payout spécifique
- send_sms_task : Envoyer un SMS
- send_email_async : Envoyer un email
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal
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


# =============================================================================
# TÂCHES OTP
# =============================================================================

@shared_task(name='apps.core.tasks.clean_expired_otp')
def clean_expired_otp():
    """
    Nettoyer les OTP expirés.
    Exécuté toutes les 30 minutes.
    """
    from apps.users.models import OTPCode
    
    try:
        # Supprimer les OTP expirés
        now = timezone.now()
        deleted_count = OTPCode.objects.filter(
            expires_at__lt=now
        ).delete()[0]
        
        logger.info(f"Cleaned {deleted_count} expired OTP codes")
        return {
            'cleaned': deleted_count,
            'timestamp': now.isoformat()
        }
    except Exception as e:
        logger.error(f"Error cleaning expired OTP: {e}")
        return {'cleaned': 0, 'error': str(e)}


# =============================================================================
# TÂCHES PAYOUT (Virements automatiques)
# =============================================================================

@shared_task(name='apps.core.tasks.process_pending_payouts')
def process_pending_payouts():
    """
    Traite les payouts programmés dont l'heure est arrivée.
    
    Exécuté toutes les 5 minutes.
    
    Workflow:
    1. Trouve les commandes avec payout_status='scheduled' et payout_scheduled_at <= now
    2. Pour chaque commande, envoie le payout au prestataire
    3. Met à jour le statut du payout et du wallet
    """
    from apps.orders.models import Order
    from apps.core.models import PayoutRequest, PlatformSettings
    from apps.core.services import PayoutService
    
    now = timezone.now()
    settings = PlatformSettings.get_settings()
    
    # Trouver les commandes avec payout programmé et prêt à être exécuté
    # payment_status='escrow' signifie que l'argent est bloqué et prêt pour le payout
    orders_to_payout = Order.objects.filter(
        payout_status='scheduled',
        payout_scheduled_at__lte=now,
        payment_status='escrow',  # Argent bloqué en séquestre
        statut='delivered',
    ).select_related('provider')
    
    processed = 0
    failed = 0
    total_amount = Decimal('0')
    
    for order in orders_to_payout:
        try:
            # Exécuter le payout
            result = PayoutService.execute_order_payout(order)
            
            if result.get('success'):
                processed += 1
                total_amount += result.get('amount', Decimal('0'))
                logger.info(f"✅ Payout exécuté pour commande {order.numero}")
            else:
                failed += 1
                logger.warning(f"⚠️ Payout échoué pour commande {order.numero}: {result.get('error')}")
                
        except Exception as e:
            failed += 1
            logger.error(f"❌ Erreur payout commande {order.numero}: {e}")
            
            # Marquer comme échoué pour retry
            order.payout_status = 'failed'
            order.save(update_fields=['payout_status'])
    
    logger.info(f"Payouts traités: {processed} réussis, {failed} échoués, total: {total_amount} FCFA")
    
    return {
        'processed': processed,
        'failed': failed,
        'total_amount': str(total_amount),
        'timestamp': now.isoformat(),
    }


@shared_task(name='apps.core.tasks.retry_failed_payouts')
def retry_failed_payouts():
    """
    Réessaie les payouts qui ont échoué.
    
    Exécuté toutes les heures.
    Maximum 3 tentatives par payout.
    """
    from apps.core.models import PayoutRequest
    from apps.core.services import PayoutService
    
    now = timezone.now()
    
    # Trouver les payouts échoués à réessayer (max 3 tentatives)
    failed_payouts = PayoutRequest.objects.filter(
        status='failed',
        retry_count__lt=3,
        should_retry=True,
    ).select_related('provider', 'order')
    
    retried = 0
    succeeded = 0
    
    for payout in failed_payouts:
        try:
            result = PayoutService.retry_payout(payout)
            retried += 1
            
            if result.get('success'):
                succeeded += 1
                logger.info(f"✅ Payout {payout.reference} réussi après retry")
            else:
                logger.warning(f"⚠️ Payout {payout.reference} échoué encore: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Erreur retry payout {payout.reference}: {e}")
    
    logger.info(f"Retry payouts: {retried} tentés, {succeeded} réussis")
    
    return {
        'retried': retried,
        'succeeded': succeeded,
        'timestamp': now.isoformat(),
    }


@shared_task(
    name='apps.core.tasks.process_single_payout',
    bind=True,
    max_retries=3,
    default_retry_delay=300  # Retry après 5 minutes
)
def process_single_payout(self, order_id: str):
    """
    Traite le payout d'une commande spécifique.
    
    Appelé après la validation OTP de livraison, avec un délai de 2h.
    
    Args:
        order_id: ID de la commande
    """
    from apps.orders.models import Order
    from apps.core.services import PayoutService
    
    try:
        order = Order.objects.select_related(
            'provider'
        ).get(id=order_id)
        
        # Vérifier que le payout est toujours programmé
        if order.payout_status != 'scheduled':
            logger.info(f"Payout commande {order.numero} déjà traité: {order.payout_status}")
            return {'skipped': True, 'reason': f'status={order.payout_status}'}
        
        # Exécuter le payout
        result = PayoutService.execute_order_payout(order)
        
        if result.get('success'):
            logger.info(f"✅ Payout commande {order.numero} exécuté avec succès")
            return result
        else:
            raise Exception(result.get('error', 'Erreur inconnue'))
            
    except Order.DoesNotExist:
        logger.error(f"Commande {order_id} introuvable pour payout")
        return {'error': 'Order not found'}
        
    except Exception as e:
        logger.error(f"❌ Erreur payout commande {order_id}: {e}")
        
        # Retry automatique
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded pour payout commande {order_id}")
            
            # Marquer comme échoué définitivement
            try:
                order = Order.objects.get(id=order_id)
                order.payout_status = 'failed'
                order.save(update_fields=['payout_status'])
            except Exception:
                pass
            
            raise


@shared_task(name='apps.core.tasks.schedule_order_payout')
def schedule_order_payout(order_id: str, delay_hours: int = 2):
    """
    Programme le payout d'une commande avec un délai.
    
    Appelé immédiatement après la validation OTP.
    
    Args:
        order_id: ID de la commande
        delay_hours: Délai en heures avant le payout (défaut: 2h)
    """
    from apps.orders.models import Order
    
    try:
        order = Order.objects.get(id=order_id)
        
        # Programmer le payout
        scheduled_at = timezone.now() + timedelta(hours=delay_hours)
        order.payout_status = 'scheduled'
        order.payout_scheduled_at = scheduled_at
        order.save(update_fields=['payout_status', 'payout_scheduled_at'])
        
        # Programmer la tâche Celery avec le délai
        process_single_payout.apply_async(
            args=[str(order_id)],
            eta=scheduled_at,
        )
        
        logger.info(f"Payout programmé pour commande {order.numero} à {scheduled_at}")
        
        return {
            'order_id': str(order_id),
            'scheduled_at': scheduled_at.isoformat(),
            'delay_hours': delay_hours,
        }
        
    except Order.DoesNotExist:
        logger.error(f"Commande {order_id} introuvable pour programmer payout")
        return {'error': 'Order not found'}


@shared_task(name='apps.core.tasks.process_manual_payout_request')
def process_manual_payout_request(payout_request_id: str):
    """
    Traite une demande de retrait manuel d'un prestataire.
    
    Args:
        payout_request_id: ID de la demande de payout
    """
    from apps.core.models import PayoutRequest
    from apps.core.services import PayoutService
    
    try:
        payout = PayoutRequest.objects.select_related(
            'provider', 'provider__wallet'
        ).get(id=payout_request_id)
        
        if payout.status != 'pending':
            logger.info(f"Payout {payout.reference} déjà traité: {payout.status}")
            return {'skipped': True, 'reason': f'status={payout.status}'}
        
        # Exécuter le payout
        result = PayoutService.execute_payout_request(payout)
        
        if result.get('success'):
            logger.info(f"✅ Retrait {payout.reference} exécuté avec succès")
        else:
            logger.warning(f"⚠️ Retrait {payout.reference} échoué: {result.get('error')}")
        
        return result
        
    except PayoutRequest.DoesNotExist:
        logger.error(f"PayoutRequest {payout_request_id} introuvable")
        return {'error': 'PayoutRequest not found'}


# =============================================================================
# TÂCHES NOTIFICATIONS
# =============================================================================

@shared_task(name='apps.core.tasks.send_payout_notification')
def send_payout_notification(provider_id: str, amount: str, status: str):
    """
    Envoie une notification de payout au prestataire.
    
    Args:
        provider_id: ID du prestataire
        amount: Montant du payout
        status: Statut (success, failed)
    """
    from apps.providers.models import Provider
    
    try:
        provider = Provider.objects.select_related('user').get(id=provider_id)
        phone = provider.user.phone_number
        
        if status == 'success':
            message = f"Pressow: Votre virement de {amount} FCFA a été effectué avec succès sur votre compte Mobile Money."
        else:
            message = f"Pressow: Le virement de {amount} FCFA a échoué. Nous réessayerons automatiquement."
        
        # Envoyer le SMS
        send_sms_task.delay(phone, message, tag='payout')
        
        logger.info(f"Notification payout envoyée à {phone}")
        return {'sent': True, 'phone': phone}
        
    except Provider.DoesNotExist:
        logger.error(f"Provider {provider_id} introuvable pour notification")
        return {'error': 'Provider not found'}

