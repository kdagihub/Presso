"""
Serializers pour les paramètres (Provider et Client)
"""
from rest_framework import serializers
from apps.core.models import ProviderSettings
from apps.users.models import UserNotificationPreferences


class ProviderSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer pour lire les paramètres du prestataire.
    Utilisé par GET /api/providers/settings/full/
    """
    
    class Meta:
        model = ProviderSettings
        fields = [
            # Notifications - Canaux
            'push_notifications',
            'email_notifications',
            'sms_notifications',
            'notification_email',
            'notification_phone',
            
            # Notifications - Types
            'notify_new_orders',
            'notify_order_updates',
            'notify_payments',
            'notify_reminders',
            
            # Disponibilité
            'auto_accept_orders',
            'pause_mode',
            'pause_reason',
            'max_orders_per_day',
            'working_days',
            'opening_hours',
            
            # Financier
            'min_order_amount',
            'delivery_fee',
            
            # Sécurité
            'two_factor_auth',
            'login_alerts',
            
            # État
            'is_open',
            'closed_reason',
            
            # Métadonnées
            'updated',
        ]
        read_only_fields = ['updated']


class ProviderSettingsUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour mettre à jour les paramètres du prestataire.
    Utilisé par PATCH /api/providers/settings/full/
    """
    
    class Meta:
        model = ProviderSettings
        fields = [
            # Notifications - Canaux
            'push_notifications',
            'email_notifications',
            'sms_notifications',
            'notification_email',
            'notification_phone',
            
            # Notifications - Types
            'notify_new_orders',
            'notify_order_updates',
            'notify_payments',
            'notify_reminders',
            
            # Disponibilité
            'auto_accept_orders',
            'pause_mode',
            'pause_reason',
            'max_orders_per_day',
            'working_days',
            'opening_hours',
            
            # Financier
            'min_order_amount',
            'delivery_fee',
            
            # Sécurité
            'two_factor_auth',
            'login_alerts',
        ]
    
    def validate_working_days(self, value):
        """Valide que working_days contient des jours valides"""
        valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        if not isinstance(value, list):
            raise serializers.ValidationError("working_days doit être une liste")
        
        for day in value:
            if day not in valid_days:
                raise serializers.ValidationError(f"Jour invalide: {day}")
        
        return value
    
    def validate_opening_hours(self, value):
        """Valide le format des horaires d'ouverture"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("opening_hours doit être un objet JSON")
        
        # Format attendu:
        # {
        #   "weekdays": {"start": "08:00", "end": "18:00"},
        #   "weekends": {"start": "09:00", "end": "16:00"}
        # }
        return value
    
    def validate_min_order_amount(self, value):
        """Valide que le montant minimum est positif"""
        if value < 0:
            raise serializers.ValidationError("Le montant minimum doit être positif")
        return value
    
    def validate_max_orders_per_day(self, value):
        """Valide que max_orders_per_day est positif"""
        if value < 0:
            raise serializers.ValidationError("Le nombre maximum de commandes doit être positif ou 0 (illimité)")
        return value


class ClientNotificationPreferencesSerializer(serializers.ModelSerializer):
    """
    Serializer pour les préférences de notification des clients.
    Utilisé par GET/PATCH /api/clients/notification-preferences/
    """
    
    class Meta:
        model = UserNotificationPreferences
        fields = [
            # Canaux
            'push_enabled',
            'email_enabled',
            'sms_enabled',
            
            # Types
            'notify_order_confirmations',
            'notify_order_updates',
            'notify_delivery',
            'notify_payments',
            'notify_promotions',
            
            # Métadonnées
            'updated',
        ]
        read_only_fields = ['updated']


class NotificationTestSerializer(serializers.Serializer):
    """Serializer pour tester l'envoi de notifications"""
    
    channel = serializers.ChoiceField(
        choices=['push', 'email', 'sms', 'all'],
        default='push',
        help_text="Canal de notification à tester"
    )
    
    message = serializers.CharField(
        max_length=500,
        required=False,
        default="Ceci est une notification de test depuis Pressow",
        help_text="Message personnalisé (optionnel)"
    )
