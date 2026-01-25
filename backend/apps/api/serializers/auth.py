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
    """
    Serializer pour la demande de réinitialisation de mot de passe.
    L'utilisateur peut fournir soit son téléphone, soit son email.
    """
    identifier = serializers.CharField(
        max_length=150,
        help_text="Numéro de téléphone ou adresse email"
    )
    method = serializers.ChoiceField(
        choices=['sms', 'email'],
        required=False,
        help_text="Méthode de réinitialisation (sms ou email). Auto-détecté si non spécifié."
    )
    
    def validate(self, attrs):
        identifier = attrs.get('identifier', '').strip()
        method = attrs.get('method')
        
        # Auto-détection de la méthode si non spécifiée
        if not method:
            if '@' in identifier:
                method = 'email'
            else:
                method = 'sms'
        
        attrs['method'] = method
        
        if method == 'email':
            # Validation email basique
            if '@' not in identifier or '.' not in identifier.split('@')[-1]:
                raise serializers.ValidationError({
                    'identifier': "Veuillez entrer une adresse email valide."
                })
            attrs['email'] = identifier.lower()
        else:
            # Normalisation du téléphone
            attrs['phone'] = normalize_to_e164(identifier)
        
        return attrs


class PasswordResetVerifySerializer(serializers.Serializer):
    """
    Serializer pour vérifier le code de réinitialisation.
    """
    reset_token = serializers.CharField()
    code = serializers.CharField(max_length=6)


class PasswordResetResendSerializer(serializers.Serializer):
    """
    Serializer pour renvoyer le code de réinitialisation.
    """
    reset_token = serializers.CharField()


class PasswordResetFinalizeSerializer(serializers.Serializer):
    """
    Serializer pour finaliser la réinitialisation du mot de passe.
    """
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
    Gère les infos de base et l'upload de photo de profil
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    provider = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    phone_verified = serializers.SerializerMethodField()
    photo_profil_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'phone_verified', 'phone_verified_at',
            'first_name', 'last_name', 'photo_profil', 'photo_profil_url',
            'role', 'role_display', 'custom_role',
            'latitude', 'longitude', 'adresse', 'quartier',
            'date_inscription', 'is_active',
            'provider', 'permissions'
        ]
        read_only_fields = [
            'id', 'date_inscription', 'role_display', 'phone',
            'provider', 'permissions', 'phone_verified', 'phone_verified_at',
            'photo_profil_url'
        ]
    
    def get_phone_verified(self, obj):
        """Retourne si le téléphone est vérifié"""
        return obj.is_phone_verified()
    
    def get_photo_profil_url(self, obj):
        """Retourne l'URL complète de la photo de profil"""
        if obj.photo_profil:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo_profil.url)
            return obj.photo_profil.url
        return None
    
    def get_provider(self, obj):
        """Retourne les infos du prestataire si existant"""
        provider = obj.get_provider()
        if provider:
            photo_url = None
            if provider.photo_local:
                request = self.context.get('request')
                if request:
                    photo_url = request.build_absolute_uri(provider.photo_local.url)
                else:
                    photo_url = provider.photo_local.url
            return {
                'id': str(provider.id),
                'nom_commercial': provider.nom_commercial,
                'type': provider.type,
                'type_display': provider.get_type_display(),
                'adresse': provider.adresse,
                'ville': provider.ville,
                'quartier': provider.quartier,
                'photo_local': photo_url,
                'rayon_km': str(provider.rayon_km),
                'zone_couverture': provider.zone_couverture,
                'latitude': str(provider.latitude) if provider.latitude else None,
                'longitude': str(provider.longitude) if provider.longitude else None,
                'is_active': provider.is_active,
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


class UserPhotoUploadSerializer(serializers.ModelSerializer):
    """
    Serializer pour l'upload de photo de profil
    """
    class Meta:
        model = User
        fields = ['photo_profil']
    
    def validate_photo_profil(self, value):
        if value:
            # Vérifier la taille (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("La photo ne doit pas dépasser 5MB.")
            # Vérifier le type MIME
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(value, 'content_type') and value.content_type not in allowed_types:
                raise serializers.ValidationError("Format non supporté. Utilisez JPEG, PNG, GIF ou WebP.")
        return value


class AccountDeactivateSerializer(serializers.Serializer):
    """
    Serializer pour désactiver (soft delete) un compte
    """
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Mot de passe actuel pour confirmer la désactivation"
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Raison de la désactivation (optionnel)"
    )
    
    def validate_password(self, value):
        """Vérifier que le mot de passe est correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mot de passe incorrect.")
        return value


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


# ═══════════════════════════════════════════════════════════════════════════════
# CHANGEMENT DE NUMÉRO DE TÉLÉPHONE
# ═══════════════════════════════════════════════════════════════════════════════

class PhoneChangeRequestSerializer(serializers.Serializer):
    """
    Serializer pour demander un changement de numéro de téléphone.
    Étape 1: L'utilisateur fournit son mot de passe et le nouveau numéro.
    """
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        help_text="Mot de passe actuel pour confirmer l'identité"
    )
    new_phone = serializers.CharField(
        required=True,
        max_length=32,
        help_text="Nouveau numéro de téléphone (ex: 0712345678)"
    )
    
    def validate_password(self, value):
        """Vérifier le mot de passe actuel"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mot de passe incorrect.")
        return value
    
    def validate_new_phone(self, value):
        """Vérifier que le nouveau numéro est valide et disponible"""
        phone_e164 = normalize_to_e164(value)
        user = self.context['request'].user
        
        # Vérifier que ce n'est pas le même numéro
        if user.phone == phone_e164:
            raise serializers.ValidationError("Ce numéro est déjà votre numéro actuel.")
        
        # Vérifier que le numéro n'est pas déjà utilisé
        if User.objects.filter(phone=phone_e164).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Ce numéro de téléphone est déjà utilisé par un autre compte.")
        
        return phone_e164


class PhoneChangeConfirmSerializer(serializers.Serializer):
    """
    Serializer pour confirmer le changement de numéro de téléphone.
    Étape 2: L'utilisateur fournit le code OTP reçu sur le nouveau numéro.
    """
    change_token = serializers.CharField(
        required=True,
        help_text="Token de changement reçu après la demande"
    )
    otp_code = serializers.CharField(
        required=True,
        max_length=6,
        help_text="Code OTP reçu sur le nouveau numéro"
    )


