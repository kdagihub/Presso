"""
Serializers pour les flux d'authentification Presso (OTP stateless).
"""
from django.contrib.auth import get_user_model, password_validation  # type: ignore
from django.contrib.auth.password_validation import validate_password  # type: ignore
from django.core.exceptions import ValidationError as DjangoValidationError  # type: ignore
from rest_framework import serializers  # type: ignore


PROVIDER_SERVICE_CHOICES = [
    ('pressing-linge', 'Pressing linge'),
    ('pressing-chaussures', 'Pressing chaussures'),
    ('blanchisserie', 'Blanchisserie'),
    ('laverie', 'Laverie'),
    ('fanico', 'Service à domicile / pressing traditionnel'),
    ('nettoyage', 'Nettoyage'),
    ('autre', 'Autre'),
]

from apps.core.utils.phone import normalize_to_e164

User = get_user_model()


class ClientRegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, attrs):
        phone = normalize_to_e164(attrs['phone'])
        attrs['phone'] = phone

        password = attrs.get('password') or ''
        password_confirm = attrs.get('password_confirm') or ''

        if password or password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError({'password': 'Les mots de passe ne correspondent pas.'})
            try:
                password_validation.validate_password(password)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({'password': list(exc.messages)})
        else:
            attrs['password'] = ''
        return attrs


class ProviderRegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    company_name = serializers.CharField(max_length=200)
    service_type = serializers.ChoiceField(choices=PROVIDER_SERVICE_CHOICES)
    city = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=32)
    email = serializers.EmailField(required=False, allow_blank=True)
    login = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Les mots de passe ne correspondent pas.'})
        try:
            password_validation.validate_password(attrs['password'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})

        attrs['phone'] = normalize_to_e164(attrs['phone'])
        return attrs


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=150, help_text="Username, email ou téléphone")
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})


class OTPRequestSerializer(serializers.Serializer):
    pending_token = serializers.CharField()


class OTPVerifySerializer(serializers.Serializer):
    pending_token = serializers.CharField()
    code = serializers.CharField(max_length=6)
    otp_id = serializers.CharField(max_length=128, required=False, allow_blank=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=32)

    def validate_phone(self, value):
        return normalize_to_e164(value)


class PasswordResetVerifySerializer(serializers.Serializer):
    reset_token = serializers.CharField()
    code = serializers.CharField(max_length=6)


class PasswordResetFinalizeSerializer(serializers.Serializer):
    reset_session_token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'Les mots de passe ne correspondent pas.'})
        try:
            password_validation.validate_password(attrs['new_password'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'new_password': list(exc.messages)})
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer pour le profil utilisateur connecté
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    provider = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    phone_verified = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'phone_verified', 'phone_verified_at',
            'first_name', 'last_name', 'photo_profil',
            'role', 'role_display', 'custom_role',
            'latitude', 'longitude', 'adresse', 'quartier',
            'date_inscription', 'is_active',
            'provider', 'permissions'
        ]
        read_only_fields = [
            'id', 'date_inscription', 'role_display',
            'provider', 'permissions', 'phone_verified', 'phone_verified_at'
        ]
    
    def get_phone_verified(self, obj):
        """Retourne si le téléphone est vérifié"""
        return obj.is_phone_verified()
    
    def get_provider(self, obj):
        """Retourne les infos du prestataire si existant"""
        provider = obj.get_provider()
        if provider:
            return {
                'id': str(provider.id),
                'nom_commercial': provider.nom_commercial,
                'type': provider.type,
                'adresse': provider.adresse,
                'quartier': provider.quartier,
            }
        return None
    
    def get_permissions(self, obj):
        """Retourne les permissions de l'utilisateur"""
        if obj.is_superuser:
            return ['all']
        
        if obj.custom_role and obj.custom_role.is_active:
            return list(
                obj.custom_role.permissions.filter(is_active=True)
                .values_list('code', flat=True)
            )
        
        return []


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer pour changer le mot de passe
    """
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        """Vérifier que l'ancien mot de passe est correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Ancien mot de passe incorrect.")
        return value
    
    def validate(self, attrs):
        """Vérifier que les nouveaux mots de passe correspondent"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Les nouveaux mots de passe ne correspondent pas."
            })
        return attrs
    
    def save(self, **kwargs):
        """Changer le mot de passe"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


