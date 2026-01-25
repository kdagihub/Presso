"""
Service de dispatch des notifications - Pressow

Ce service gère l'envoi intelligent des notifications en fonction des :
- Préférences utilisateur (canaux activés, types de notifications)
- Type d'événement (commande, paiement, livraison, etc.)
- Deep linking (URL cible quand on clique sur la notification)

Usage:
    from apps.core.services.notification_dispatcher import NotificationDispatcher
    
    dispatcher = NotificationDispatcher()
    dispatcher.notify_new_order(order)
    dispatcher.notify_payment_received(payment)
"""
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationDispatcher:
    """
    Service centralisé pour envoyer des notifications intelligentes.
    
    Vérifie les préférences utilisateur avant d'envoyer et gère
    le deep linking pour rediriger vers le bon module.
    """
    
    # ═══════════════════════════════════════════════════════════════════
    # CONFIGURATION DES ÉVÉNEMENTS
    # ═══════════════════════════════════════════════════════════════════
    
    # Mapping des événements vers les types de notification
    EVENT_TYPES = {
        # Événements commandes
        'order_created': 'order_confirmation',
        'order_accepted': 'order_update',
        'order_ready': 'order_update',
        'order_in_delivery': 'delivery',
        'order_delivered': 'order_update',
        'order_cancelled': 'order_update',
        
        # Événements paiements
        'payment_received': 'payment',
        'payment_failed': 'payment',
        
        # Événements promotions
        'promotion': 'promotion',
    }
    
    # Templates de notification par événement
    NOTIFICATION_TEMPLATES = {
        # ═══════════════════════════════════════════════════════════════
        # PRESTATAIRE - Notifications
        # ═══════════════════════════════════════════════════════════════
        'provider_new_order': {
            'title': '🆕 Nouvelle commande !',
            'body': 'Commande #{order_number} de {client_name} - {amount} FCFA',
            'url': '/commandes/{order_id}',
            'priority': 'high',
        },
        'provider_payment_received': {
            'title': '💰 Paiement reçu',
            'body': 'Paiement de {amount} FCFA reçu pour la commande #{order_number}',
            'url': '/portefeuille',
            'priority': 'normal',
        },
        'provider_order_cancelled': {
            'title': '❌ Commande annulée',
            'body': 'La commande #{order_number} a été annulée par le client',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        'provider_reminder': {
            'title': '⏰ Rappel commande en attente',
            'body': 'La commande #{order_number} attend depuis {hours}h',
            'url': '/commandes/{order_id}',
            'priority': 'low',
        },
        
        # Confirmations d'action pour le prestataire
        'provider_order_confirmed': {
            'title': '✅ Commande confirmée',
            'body': 'Commande #{order_number} confirmée avec succès',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        'provider_order_accepted': {
            'title': '✅ Commande acceptée',
            'body': 'Commande #{order_number} acceptée avec succès',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        'provider_order_processing': {
            'title': '🔄 En traitement',
            'body': 'Commande #{order_number} en cours de traitement',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        'provider_order_ready': {
            'title': '📦 Commande prête',
            'body': 'Commande #{order_number} marquée prête pour livraison',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        'provider_order_in_delivery': {
            'title': '🚚 En livraison',
            'body': 'Commande #{order_number} partie en livraison',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        'provider_order_delivered': {
            'title': '🎉 Livraison confirmée',
            'body': 'Commande #{order_number} livrée avec succès !',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        
        # ═══════════════════════════════════════════════════════════════
        # CLIENT - Notifications
        # ═══════════════════════════════════════════════════════════════
        'client_order_confirmed': {
            'title': '✅ Commande confirmée',
            'body': 'Votre commande #{order_number} a été reçue par {provider_name}',
            'url': '/commandes/{order_id}',
            'priority': 'high',
        },
        'client_order_accepted': {
            'title': '👍 Commande acceptée',
            'body': '{provider_name} a accepté votre commande #{order_number}',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        'client_order_ready': {
            'title': '📦 Commande prête',
            'body': 'Votre commande #{order_number} est prête pour la livraison',
            'url': '/commandes/{order_id}',
            'priority': 'high',
        },
        'client_order_in_delivery': {
            'title': '🚚 Livraison en cours',
            'body': 'Votre commande #{order_number} est en route ! Code OTP: {otp_code}',
            'url': '/commandes/{order_id}',
            'priority': 'high',
        },
        'client_order_delivered': {
            'title': '🎉 Commande livrée',
            'body': 'Votre commande #{order_number} a été livrée avec succès',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        'client_order_cancelled': {
            'title': '❌ Commande annulée',
            'body': 'Votre commande #{order_number} a été annulée',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        'client_order_confirmed': {
            'title': '✅ Commande confirmée',
            'body': '{provider_name} a confirmé votre commande #{order_number}',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        'client_order_collected': {
            'title': '📥 Linge collecté',
            'body': 'Votre linge a été collecté pour la commande #{order_number}',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        'client_order_in_progress': {
            'title': '🧺 En cours de traitement',
            'body': 'Votre commande #{order_number} est en cours de traitement',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
        'client_payment_confirmed': {
            'title': '💳 Paiement confirmé',
            'body': 'Votre paiement de {amount} FCFA a été confirmé',
            'url': '/commandes/{order_id}',
            'priority': 'normal',
        },
    }
    
    # Mapping des statuts Order vers les clés de template
    STATUS_TO_TEMPLATE = {
        'confirmed': 'confirmed',
        'collected': 'collected',
        'in_progress': 'in_progress',
        'ready': 'ready',
        'delivered': 'delivered',
        'cancelled': 'cancelled',
    }
    
    def __init__(self):
        self.push_enabled = settings.NOTIFICATION_CHANNELS.get('push', True)
        self.email_enabled = settings.NOTIFICATION_CHANNELS.get('email', True)
        self.sms_enabled = settings.NOTIFICATION_CHANNELS.get('sms', False)
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTHODES PRINCIPALES - PRESTATAIRE
    # ═══════════════════════════════════════════════════════════════════
    
    def notify_provider_new_order(self, order) -> Dict[str, bool]:
        """
        Notifie le prestataire d'une nouvelle commande.
        
        Canaux: Push ✅ | Email ✅ | SMS ⚙️ (si activé)
        """
        provider = order.provider
        provider_settings = getattr(provider, 'settings', None)
        
        if not provider_settings:
            logger.warning(f"No settings found for provider {provider.id}")
            return {'push': False, 'email': False, 'sms': False}
        
        # Vérifier si le prestataire veut recevoir ce type de notification
        if not provider_settings.notify_new_orders:
            logger.info(f"Provider {provider.id} has disabled new order notifications")
            return {'push': False, 'email': False, 'sms': False}
        
        # Préparer les données
        template = self.NOTIFICATION_TEMPLATES['provider_new_order']
        data = {
            'order_number': order.numero,
            'order_id': str(order.id),
            'client_name': order.client.get_full_name() or order.client.username,
            'amount': str(order.total_estime or 0),
        }
        
        notification = self._build_notification(template, data)
        
        # Récupérer l'utilisateur du prestataire
        provider_user = provider.user if hasattr(provider, 'user') else None
        if not provider_user:
            logger.warning(f"No user associated with provider {provider.id}")
            return {'push': False, 'email': False, 'sms': False}
        
        logger.info(f"[NOTIF] Provider user: {provider_user.email}, settings: push={provider_settings.push_notifications}, email={provider_settings.email_notifications}")
        
        results = {}
        
        # Push notification
        if provider_settings.push_notifications and self.push_enabled:
            logger.info(f"[NOTIF] Sending push to {provider_user.id}")
            results['push'] = self._send_push(provider_user, notification)
        else:
            results['push'] = False
        
        # Email
        if provider_settings.email_notifications and self.email_enabled:
            email = provider_settings.notification_email or provider_user.email
            logger.info(f"[NOTIF] Sending email to {email}")
            results['email'] = self._send_email(
                email=email,
                subject=notification['title'],
                body=notification['body'],
                template_name='new_order',
                context={'order': order, 'provider': provider}
            )
            logger.info(f"[NOTIF] Email result: {results['email']}")
        else:
            logger.info(f"[NOTIF] Email disabled: settings={provider_settings.email_notifications}, enabled={self.email_enabled}")
            results['email'] = False
        
        # SMS (seulement si explicitement activé - coûteux)
        if provider_settings.sms_notifications and self.sms_enabled:
            phone = provider_settings.notification_phone or provider_user.phone
            results['sms'] = self._send_sms(phone, notification['body'])
        else:
            results['sms'] = False
        
        logger.info(f"Notified provider {provider.id} of new order {order.id}: {results}")
        return results
    
    def notify_provider_payment_received(self, order) -> Dict[str, bool]:
        """
        Notifie le prestataire d'un paiement reçu.
        
        Canaux: Push ✅ | Email ✅ | SMS ❌
        """
        provider = order.provider
        provider_settings = getattr(provider, 'settings', None)
        
        if not provider_settings or not provider_settings.notify_payments:
            return {'push': False, 'email': False, 'sms': False}
        
        template = self.NOTIFICATION_TEMPLATES['provider_payment_received']
        data = {
            'order_number': order.numero,
            'order_id': str(order.id),
            'amount': str(order.total_estime or 0),
        }
        
        notification = self._build_notification(template, data)
        provider_user = provider.user if hasattr(provider, 'user') else None
        
        if not provider_user:
            return {'push': False, 'email': False, 'sms': False}
        
        results = {}
        
        # Push
        if provider_settings.push_notifications and self.push_enabled:
            results['push'] = self._send_push(provider_user, notification)
        else:
            results['push'] = False
        
        # Email
        if provider_settings.email_notifications and self.email_enabled:
            email = provider_settings.notification_email or provider_user.email
            results['email'] = self._send_email(
                email=email,
                subject=notification['title'],
                body=notification['body'],
                template_name='payment_received',
                context={'order': order}
            )
        else:
            results['email'] = False
        
        results['sms'] = False  # Pas de SMS pour les paiements
        
        logger.info(f"Notified provider {provider.id} of payment for order {order.id}")
        return results
    
    def notify_provider_status_confirmation(self, order, new_status: str) -> Dict[str, bool]:
        """
        Notifie le prestataire de la confirmation de son changement de statut.
        
        C'est une notification légère (push uniquement) pour confirmer l'action.
        
        Canaux: Push ✅ | Email ❌ | SMS ❌
        """
        provider = order.provider
        provider_settings = getattr(provider, 'settings', None)
        
        if not provider_settings:
            return {'push': False, 'email': False, 'sms': False}
        
        # Mapping statut -> template
        status_templates = {
            'confirmed': 'provider_order_confirmed',
            'accepted': 'provider_order_accepted',
            'collected': 'provider_order_processing',
            'in_progress': 'provider_order_processing',
            'ready': 'provider_order_ready',
            'in_delivery': 'provider_order_in_delivery',
            'delivered': 'provider_order_delivered',
        }
        
        template_key = status_templates.get(new_status)
        if not template_key:
            logger.debug(f"No confirmation template for status: {new_status}")
            return {'push': False, 'email': False, 'sms': False}
        
        template = self.NOTIFICATION_TEMPLATES.get(template_key)
        if not template:
            return {'push': False, 'email': False, 'sms': False}
        
        data = {
            'order_number': order.numero,
            'order_id': str(order.id),
        }
        
        notification = self._build_notification(template, data)
        provider_user = provider.user if hasattr(provider, 'user') else None
        
        if not provider_user:
            return {'push': False, 'email': False, 'sms': False}
        
        results = {'email': False, 'sms': False}
        
        # Push uniquement pour les confirmations (pas besoin d'email)
        if provider_settings.push_notifications and self.push_enabled:
            results['push'] = self._send_push(provider_user, notification)
            logger.info(f"[NOTIF] Confirmation push sent to provider for status '{new_status}': {results['push']}")
        else:
            results['push'] = False
        
        return results
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTHODES PRINCIPALES - CLIENT
    # ═══════════════════════════════════════════════════════════════════
    
    def notify_client_order_confirmed(self, order) -> Dict[str, bool]:
        """
        Notifie le client que sa commande est confirmée.
        
        Canaux: Push ✅ | Email ✅ | SMS ⚙️
        """
        client = order.client
        prefs = self._get_client_preferences(client)
        
        if not prefs.notify_order_confirmations:
            return {'push': False, 'email': False, 'sms': False}
        
        template = self.NOTIFICATION_TEMPLATES['client_order_confirmed']
        data = {
            'order_number': order.numero,
            'order_id': str(order.id),
            'provider_name': order.provider.nom_commercial,
        }
        
        notification = self._build_notification(template, data)
        
        results = {}
        
        # Push
        if prefs.push_enabled and self.push_enabled:
            results['push'] = self._send_push(client, notification)
        else:
            results['push'] = False
        
        # Email
        if prefs.email_enabled and self.email_enabled:
            results['email'] = self._send_email(
                email=client.email,
                subject=notification['title'],
                body=notification['body'],
                template_name='order_confirmed',
                context={'order': order, 'client': client}
            )
        else:
            results['email'] = False
        
        # SMS (optionnel)
        if prefs.sms_enabled and self.sms_enabled:
            results['sms'] = self._send_sms(client.phone, notification['body'])
        else:
            results['sms'] = False
        
        logger.info(f"Notified client {client.id} of order confirmation {order.id}")
        return results
    
    def notify_client_order_status_changed(
        self, 
        order, 
        new_status: str, 
        otp_code: str = None
    ) -> Dict[str, bool]:
        """
        Notifie le client d'un changement de statut de commande.
        
        Args:
            order: Instance de Order
            new_status: 'confirmed', 'collected', 'in_progress', 'ready', 'delivered', 'cancelled'
            otp_code: Code OTP pour la livraison (optionnel)
        """
        client = order.client
        prefs = self._get_client_preferences(client)
        
        if not prefs.notify_order_updates:
            return {'push': False, 'email': False, 'sms': False}
        
        # Sélectionner le bon template
        template_status = self.STATUS_TO_TEMPLATE.get(new_status, new_status)
        template_key = f'client_order_{template_status}'
        template = self.NOTIFICATION_TEMPLATES.get(template_key)
        
        if not template:
            logger.warning(f"No template found for status: {new_status}")
            return {'push': False, 'email': False, 'sms': False}
        
        data = {
            'order_number': order.numero,
            'order_id': str(order.id),
            'provider_name': order.provider.nom_commercial,
            'otp_code': otp_code or '',
        }
        
        notification = self._build_notification(template, data)
        
        results = {}
        
        # Push
        if prefs.push_enabled and self.push_enabled:
            results['push'] = self._send_push(client, notification)
        else:
            results['push'] = False
        
        # Email (pour certains statuts)
        send_email_statuses = ['accepted', 'ready', 'delivered']
        if prefs.email_enabled and self.email_enabled and new_status in send_email_statuses:
            results['email'] = self._send_email(
                email=client.email,
                subject=notification['title'],
                body=notification['body'],
                template_name=f'order_{new_status}',
                context={'order': order, 'client': client}
            )
        else:
            results['email'] = False
        
        # SMS (uniquement pour livraison avec OTP)
        if new_status == 'in_delivery' and otp_code:
            if prefs.sms_enabled and self.sms_enabled:
                results['sms'] = self._send_sms(client.phone, notification['body'])
            else:
                # SMS obligatoire pour l'OTP de livraison
                results['sms'] = self._send_sms(client.phone, notification['body'])
        else:
            results['sms'] = False
        
        logger.info(f"Notified client {client.id} of order status change: {new_status}")
        return results
    
    # ═══════════════════════════════════════════════════════════════════
    # NOTIFICATIONS VÉRIFICATION À LA COLLECTE
    # ═══════════════════════════════════════════════════════════════════
    
    def notify_client_adjustment_required(
        self,
        order,
        adjustment_amount,
        deadline
    ) -> Dict[str, bool]:
        """
        Notifie le client qu'un écart a été détecté à la collecte.
        Le client doit compléter le paiement ou accepter de réduire le linge.
        """
        results = {'push': False, 'sms': False, 'email': False}
        client = order.client
        
        # Build notification
        notification = {
            'title': "⚠️ Vérification de votre commande",
            'body': (
                f"Le livreur a vérifié votre linge pour la commande {order.numero}. "
                f"Un complément de {adjustment_amount} FCFA est requis. "
                f"Vous avez jusqu'à {deadline.strftime('%H:%M')} pour compléter ou réduire le linge."
            ),
            'url': f'/orders/{order.id}/adjustment',
            'priority': 'high',
            'data': {
                'type': 'adjustment_required',
                'order_id': str(order.id),
                'order_numero': order.numero,
                'adjustment_amount': str(adjustment_amount),
                'deadline': deadline.isoformat(),
            }
        }
        
        prefs = self._get_client_preferences(client)
        
        # Push (toujours pour ce type critique)
        if self.push_enabled:
            results['push'] = self._send_push(client, notification)
        
        # SMS (critique, toujours envoyé)
        if self.sms_enabled:
            sms_body = (
                f"Pressow: Écart détecté sur commande {order.numero}. "
                f"Complément requis: {adjustment_amount} FCFA. "
                f"Délai: {deadline.strftime('%H:%M')}. Ouvrez l'app pour agir."
            )
            results['sms'] = self._send_sms(client.phone, sms_body)
        
        logger.info(f"Notified client {client.id} of adjustment required: {adjustment_amount} FCFA")
        return results
    
    def notify_client_credit_issued(
        self,
        order,
        credit_amount
    ) -> Dict[str, bool]:
        """
        Notifie le client qu'un crédit a été ajouté à son portefeuille
        (car il avait trop estimé/payé).
        """
        results = {'push': False, 'sms': False, 'email': False}
        client = order.client
        
        notification = {
            'title': "💰 Crédit ajouté à votre portefeuille",
            'body': (
                f"Suite à la vérification de votre commande {order.numero}, "
                f"un crédit de {credit_amount} FCFA a été ajouté à votre portefeuille. "
                f"Ce montant sera déduit de votre prochaine commande."
            ),
            'url': '/wallet',
            'priority': 'normal',
            'data': {
                'type': 'credit_issued',
                'order_id': str(order.id),
                'order_numero': order.numero,
                'credit_amount': str(credit_amount),
            }
        }
        
        prefs = self._get_client_preferences(client)
        
        if prefs.push_enabled and self.push_enabled:
            results['push'] = self._send_push(client, notification)
        
        logger.info(f"Notified client {client.id} of credit issued: {credit_amount} FCFA")
        return results
    
    def notify_provider_client_accepted_reduction(
        self,
        order,
        accepted_quantity
    ) -> Dict[str, bool]:
        """
        Notifie le prestataire que le client a accepté de réduire le linge.
        Le livreur peut maintenant prendre uniquement ce qui correspond au montant payé.
        """
        results = {'push': False, 'email': False}
        provider = order.provider
        
        # Récupérer l'owner du prestataire
        owner = provider.owner
        if not owner:
            logger.warning(f"Provider {provider.id} has no owner for notification")
            return results
        
        notification = {
            'title': "📦 Client a accepté la réduction",
            'body': (
                f"Le client de la commande {order.numero} a accepté de réduire son linge. "
                f"Le livreur peut maintenant collecter uniquement {accepted_quantity} "
                f"{'kg' if order.verified_weight else 'pièces'}."
            ),
            'url': f'/provider/orders/{order.id}',
            'priority': 'high',
            'data': {
                'type': 'client_accepted_reduction',
                'order_id': str(order.id),
                'order_numero': order.numero,
                'accepted_quantity': str(accepted_quantity),
            }
        }
        
        if self.push_enabled:
            results['push'] = self._send_push(owner, notification)
        
        # Notifier aussi le staff assigné s'il existe
        if order.assigned_staff and order.assigned_staff.user:
            if self.push_enabled:
                self._send_push(order.assigned_staff.user, notification)
        
        logger.info(f"Notified provider {provider.id} of client reduction acceptance")
        return results
    
    # ═══════════════════════════════════════════════════════════════════
    # MÉTHODES PRIVÉES
    # ═══════════════════════════════════════════════════════════════════
    
    def _get_client_preferences(self, user) -> 'UserNotificationPreferences':
        """Récupère ou crée les préférences de notification d'un client"""
        from apps.users.models import UserNotificationPreferences
        return UserNotificationPreferences.get_or_create_for_user(user)
    
    def _build_notification(self, template: Dict, data: Dict) -> Dict:
        """Construit la notification à partir d'un template et des données"""
        return {
            'title': template['title'].format(**data),
            'body': template['body'].format(**data),
            'url': template['url'].format(**data),
            'priority': template.get('priority', 'normal'),
            'data': {
                'type': template.get('type', 'notification'),
                'url': template['url'].format(**data),
                **data
            }
        }
    
    def _send_push(self, user, notification: Dict) -> bool:
        """Envoie une notification push via FCM"""
        try:
            from apps.core.utils.fcm import send_fcm_multicast, FIREBASE_AVAILABLE, initialize_firebase
            from apps.users.models import UserFCMToken
            
            if not FIREBASE_AVAILABLE:
                logger.warning("Firebase not available for push notifications")
                return False
            
            # S'assurer que Firebase est initialisé
            initialize_firebase()
            
            tokens = UserFCMToken.get_active_tokens_for_user(str(user.id))
            
            if not tokens:
                logger.debug(f"No FCM tokens for user {user.id}")
                return False
            
            result = send_fcm_multicast(tokens, {
                'title': notification['title'],
                'message': notification['body'],
                'data': notification.get('data', {})
            }, priority=notification.get('priority', 'normal'))
            
            return result.get('success_count', 0) > 0
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
    
    def _send_email(
        self, 
        email: str, 
        subject: str, 
        body: str,
        template_name: str = None,
        context: Dict = None
    ) -> bool:
        """Envoie un email de notification"""
        try:
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            
            # Pour l'instant, email simple. 
            # TODO: Ajouter des templates HTML
            html_message = None
            
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Email sent to {email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Error sending email to {email}: {e}")
            return False
    
    def _send_sms(self, phone: str, message: str) -> bool:
        """Envoie un SMS de notification"""
        try:
            from apps.core.tasks import send_sms_async
            
            # Envoyer via Celery (async)
            send_sms_async.delay(phone, message, tag='notification')
            
            logger.info(f"SMS queued for {phone}")
            return True
        except Exception as e:
            logger.error(f"Error sending SMS to {phone}: {e}")
            return False


# Instance globale pour faciliter l'utilisation
notification_dispatcher = NotificationDispatcher()
