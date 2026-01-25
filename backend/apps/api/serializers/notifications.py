"""
Serializers pour les notifications push (FCM)
"""
from rest_framework import serializers
from apps.users.models import UserFCMToken


class FCMTokenRegisterSerializer(serializers.Serializer):
    """
    Serializer pour enregistrer un token FCM.
    Appelé par le frontend (Vue.js, Flutter) après avoir obtenu
    la permission de notification et le token Firebase.
    """
    token = serializers.CharField(
        max_length=500,
        help_text="Token FCM généré par Firebase Messaging"
    )
    device_type = serializers.ChoiceField(
        choices=['web', 'android', 'ios'],
        default='web',
        help_text="Type de device: web, android, ios"
    )
    device_name = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        default='',
        help_text="Nom du device (ex: Chrome sur Windows)"
    )
    device_info = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Informations supplémentaires sur le device"
    )
    
    def validate_token(self, value):
        """Valide le format du token FCM"""
        if not value or len(value) < 100:
            raise serializers.ValidationError(
                "Le token FCM semble invalide (trop court)"
            )
        return value
    
    def create(self, validated_data):
        """Enregistre le token FCM pour l'utilisateur connecté"""
        user = self.context['request'].user
        
        return UserFCMToken.register_token(
            user=user,
            token=validated_data['token'],
            device_type=validated_data.get('device_type', 'web'),
            device_name=validated_data.get('device_name', ''),
            device_info=validated_data.get('device_info', {})
        )


class FCMTokenUnregisterSerializer(serializers.Serializer):
    """
    Serializer pour supprimer/désactiver un token FCM.
    Appelé lors de la déconnexion ou si l'utilisateur refuse les notifications.
    """
    token = serializers.CharField(
        max_length=500,
        help_text="Token FCM à supprimer"
    )
    
    def validate_token(self, value):
        """Vérifie que le token existe"""
        user = self.context['request'].user
        
        if not UserFCMToken.objects.filter(token=value, user=user).exists():
            raise serializers.ValidationError(
                "Ce token n'est pas enregistré pour votre compte"
            )
        return value


class FCMTokenListSerializer(serializers.ModelSerializer):
    """
    Serializer pour lister les tokens FCM d'un utilisateur.
    Permet de voir tous ses devices enregistrés.
    """
    device_type_display = serializers.CharField(
        source='get_device_type_display',
        read_only=True
    )
    
    class Meta:
        model = UserFCMToken
        fields = [
            'id',
            'device_type',
            'device_type_display',
            'device_name',
            'is_active',
            'last_used_at',
            'created',
        ]
        read_only_fields = fields


class NotificationPreferencesSerializer(serializers.Serializer):
    """
    Serializer pour les préférences de notification de l'utilisateur.
    Permet de configurer quels types de notifications recevoir.
    """
    # Canaux de notification
    push_enabled = serializers.BooleanField(
        default=True,
        help_text="Activer les notifications push"
    )
    sms_enabled = serializers.BooleanField(
        default=False,
        help_text="Activer les notifications SMS"
    )
    email_enabled = serializers.BooleanField(
        default=True,
        help_text="Activer les notifications email"
    )
    
    # Types de notifications
    order_updates = serializers.BooleanField(
        default=True,
        help_text="Notifications sur les mises à jour de commandes"
    )
    payment_updates = serializers.BooleanField(
        default=True,
        help_text="Notifications sur les paiements"
    )
    promotions = serializers.BooleanField(
        default=False,
        help_text="Notifications promotionnelles"
    )
    
    def to_internal_value(self, data):
        """Convertit les données entrantes"""
        return super().to_internal_value(data)
