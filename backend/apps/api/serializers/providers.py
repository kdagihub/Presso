"""Serializers pour les endpoints Provider (agences & staff)."""
from __future__ import annotations

from typing import Any, Optional
from decimal import Decimal, InvalidOperation

from rest_framework import serializers  # type: ignore

from apps.providers.models import Provider, ProviderAgency, ProviderStaff
from apps.core.models import Role, ProviderSettings
from apps.services.models import Service, ServiceTemplate, ArticleType, Matiere
from apps.tariffs.models import ProviderService as ProviderServiceLink, Tariff


def _validate_hex_color(value: str) -> str:
    if not value:
        return value
    value = value.strip()
    if not value.startswith('#'):
        raise serializers.ValidationError("La couleur doit commencer par '#'.")
    if len(value) not in {4, 7}:
        raise serializers.ValidationError("La couleur doit être au format #RGB ou #RRGGBB.")
    hex_part = value[1:]
    if not all(c in '0123456789abcdefABCDEF' for c in hex_part):
        raise serializers.ValidationError("Couleur hexadécimale invalide.")
    return value


# ═══════════════════════════════════════════════════════════════════════════════
# PROVIDER PROFILE (Modifier les infos du Provider lui-même)
# ═══════════════════════════════════════════════════════════════════════════════

class ProviderProfileSerializer(serializers.ModelSerializer):
    """
    Serializer en lecture seule pour le profil complet du Provider
    """
    location = serializers.SerializerMethodField()
    photo_local_url = serializers.SerializerMethodField()
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    owner = serializers.SerializerMethodField()
    
    class Meta:
        model = Provider
        fields = [
            'id', 'type', 'type_display', 'nom_commercial',
            'photo_local', 'photo_local_url',
            'zone_couverture', 'rayon_km',
            'latitude', 'longitude', 'location',
            'adresse', 'ville', 'quartier',
            'statut_kyc', 'is_active',
            'owner', 'created', 'updated'
        ]
        read_only_fields = fields
    
    def get_location(self, obj: Provider) -> Optional[dict[str, float]]:
        if obj.location:
            return {'lat': obj.location.y, 'lng': obj.location.x}
        return None
    
    def get_photo_local_url(self, obj: Provider) -> Optional[str]:
        if obj.photo_local:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo_local.url)
            return obj.photo_local.url
        return None
    
    def get_owner(self, obj: Provider) -> Optional[dict[str, Any]]:
        return {
            'id': str(obj.user.id),
            'username': obj.user.username,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'phone': obj.user.phone,
            'email': obj.user.email,
        }


class ProviderProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer pour modifier les infos du Provider
    """
    class Meta:
        model = Provider
        fields = [
            'nom_commercial', 'photo_local',
            'zone_couverture', 'rayon_km',
            'adresse', 'quartier',
            # Note: latitude/longitude/ville ne sont PAS modifiables après onboarding
        ]
        extra_kwargs = {field: {'required': False} for field in fields}
    
    def validate_photo_local(self, value):
        if value:
            # Vérifier la taille (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("La photo ne doit pas dépasser 5MB.")
            # Vérifier le type MIME
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(value, 'content_type') and value.content_type not in allowed_types:
                raise serializers.ValidationError("Format non supporté. Utilisez JPEG, PNG, GIF ou WebP.")
        return value
    
    def validate_rayon_km(self, value):
        if value is not None:
            if value < Decimal('0.5'):
                raise serializers.ValidationError("Le rayon minimum est de 0.5 km.")
            if value > Decimal('100'):
                raise serializers.ValidationError("Le rayon maximum est de 100 km.")
        return value
    
    def validate_nom_commercial(self, value):
        if value:
            value = value.strip()
            if len(value) < 2:
                raise serializers.ValidationError("Le nom commercial doit avoir au moins 2 caractères.")
            if len(value) > 200:
                raise serializers.ValidationError("Le nom commercial ne doit pas dépasser 200 caractères.")
        return value


class ProviderAgencySerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()

    class Meta:
        model = ProviderAgency
        fields = [
            'id', 'name', 'code', 'description',
            'adresse', 'ville', 'quartier',
            'latitude', 'longitude',
            'contact_name', 'contact_phone', 'contact_email',
            'opening_hours', 'metadata',
            'is_default', 'is_active',
            'location', 'created', 'updated',
        ]
        read_only_fields = ['id', 'location', 'created', 'updated']

    def get_location(self, obj: ProviderAgency) -> Optional[dict[str, float]]:
        if obj.location:
            return {'lat': obj.location.y, 'lng': obj.location.x}
        return None


class ProviderAgencyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderAgency
        fields = [
            'name', 'code', 'description',
            'adresse', 'ville', 'quartier',
            'latitude', 'longitude',
            'contact_name', 'contact_phone', 'contact_email',
            'opening_hours', 'metadata',
            'is_default', 'is_active',
        ]

    def validate_code(self, value: str) -> str:
        if value is None:
            return ''
        return value.strip().upper()


class ProviderStaffSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    agency = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = ProviderStaff
        fields = [
            'id', 'system_role', 'status', 'notes',
            'invited_email', 'invited_phone', 'invited_at',
            'activated_at', 'last_seen_at',
            'user', 'agency', 'role',
            'created', 'updated',
        ]
        read_only_fields = fields

    def get_user(self, obj: ProviderStaff) -> Optional[dict[str, Any]]:
        if not obj.user:
            return None
        return {
            'id': str(obj.user.id),
            'username': obj.user.username,
            'email': obj.user.email,
            'phone': obj.user.phone,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
        }

    def get_agency(self, obj: ProviderStaff) -> Optional[dict[str, Any]]:
        if not obj.agency:
            return None
        return {'id': str(obj.agency.id), 'name': obj.agency.name, 'is_default': obj.agency.is_default}

    def get_role(self, obj: ProviderStaff) -> Optional[dict[str, Any]]:
        if not obj.role:
            return None
        return {'id': str(obj.role.id), 'name': obj.role.name}


class ProviderStaffInviteSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=32)
    system_role = serializers.ChoiceField(choices=[c for c in ProviderStaff.ROLE_CHOICES if c[0] != 'owner'], default='operator')
    role_id = serializers.UUIDField(required=False, allow_null=True)
    agency_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        provider = self.context['provider']
        email = attrs.get('email', '').strip()
        phone = attrs.get('phone', '').strip()
        if not email and not phone:
            raise serializers.ValidationError('Email ou téléphone requis pour l\'invitation.')
        attrs['email'] = email
        attrs['phone'] = phone

        role_id = attrs.pop('role_id', serializers.empty)
        if role_id is not serializers.empty:
            if role_id is None:
                attrs['role'] = None
            else:
                try:
                    attrs['role'] = provider.custom_roles.get(id=role_id)
                except Role.DoesNotExist as exc:
                    raise serializers.ValidationError({'role_id': 'Rôle introuvable pour ce prestataire.'}) from exc
        else:
            attrs['role'] = None

        agency_id = attrs.pop('agency_id', serializers.empty)
        if agency_id is not serializers.empty:
            if agency_id is None:
                attrs['agency'] = None
            else:
                try:
                    attrs['agency'] = provider.agencies.get(id=agency_id)
                except ProviderAgency.DoesNotExist as exc:
                    raise serializers.ValidationError({'agency_id': 'Agence introuvable.'}) from exc
        else:
            attrs['agency'] = None
        return attrs


class ProviderStaffUpdateSerializer(serializers.Serializer):
    system_role = serializers.ChoiceField(choices=ProviderStaff.ROLE_CHOICES, required=False)
    role_id = serializers.UUIDField(required=False, allow_null=True)
    agency_id = serializers.UUIDField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=ProviderStaff.STATUS_CHOICES, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        provider = self.context['provider']

        role_id = attrs.pop('role_id', serializers.empty)
        if role_id is not serializers.empty:
            attrs['role_provided'] = True
            if role_id is None:
                attrs['role'] = None
            else:
                try:
                    attrs['role'] = provider.custom_roles.get(id=role_id)
                except Role.DoesNotExist as exc:
                    raise serializers.ValidationError({'role_id': 'Rôle introuvable pour ce prestataire.'}) from exc
        else:
            attrs['role_provided'] = False

        agency_id = attrs.pop('agency_id', serializers.empty)
        if agency_id is not serializers.empty:
            attrs['agency_provided'] = True
            if agency_id is None:
                attrs['agency'] = None
            else:
                try:
                    attrs['agency'] = provider.agencies.get(id=agency_id)
                except ProviderAgency.DoesNotExist as exc:
                    raise serializers.ValidationError({'agency_id': 'Agence introuvable.'}) from exc
        else:
            attrs['agency_provided'] = False
        return attrs


class ProviderStaffActivateSerializer(serializers.Serializer):
    invite_token = serializers.CharField(max_length=128)


class ProviderSettingsSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    storefront_photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProviderSettings
        fields = [
            'id',
            'business_name',
            'logo',
            'logo_url',
            'storefront_photo',
            'storefront_photo_url',
            'primary_color',
            'auto_accept_orders',
            'require_payment_before',
            'min_order_amount',
            'delivery_fee',
            'email_notifications',
            'sms_notifications',
            'notification_email',
            'notification_phone',
            'opening_hours',
            'metadata',
            'created',
            'updated',
        ]
        read_only_fields = ['id', 'created', 'updated', 'logo_url', 'storefront_photo_url']
    
    def get_logo_url(self, obj) -> Optional[str]:
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def get_storefront_photo_url(self, obj) -> Optional[str]:
        if obj.storefront_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.storefront_photo.url)
            return obj.storefront_photo.url
        return None


class ProviderSettingsUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderSettings
        fields = [
            'business_name',
            'logo',
            'storefront_photo',
            'primary_color',
            'auto_accept_orders',
            'require_payment_before',
            'min_order_amount',
            'delivery_fee',
            'email_notifications',
            'sms_notifications',
            'notification_email',
            'notification_phone',
            'opening_hours',
            'metadata',
        ]
        extra_kwargs = {field: {'required': False} for field in fields}
    
    def validate_logo(self, value):
        if value:
            if value.size > 2 * 1024 * 1024:
                raise serializers.ValidationError("Le logo ne doit pas dépasser 2MB.")
        return value
    
    def validate_storefront_photo(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("La photo ne doit pas dépasser 5MB.")
        return value

    def validate_primary_color(self, value: str) -> str:
        return _validate_hex_color(value)

    def validate_opening_hours(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Les horaires doivent être un objet JSON.")
        for day, slots in value.items():
            if not isinstance(slots, list):
                raise serializers.ValidationError(f"Horaires invalides pour {day}.")
            for slot in slots:
                if (
                    not isinstance(slot, (list, tuple))
                    or len(slot) != 2
                    or not all(isinstance(part, str) for part in slot)
                ):
                    raise serializers.ValidationError(f"Créneau invalide pour {day}.")
        return value

    def validate(self, attrs):
        for field in ('min_order_amount', 'delivery_fee'):
            if field in attrs and attrs[field] is not None:
                if attrs[field] < 0:
                    raise serializers.ValidationError({field: "La valeur doit être positive."})
        return attrs
#
# Provider Catalog (ProviderService + Tariffs)
#


class ProviderServiceSerializer(serializers.ModelSerializer):
    service = serializers.SerializerMethodField()

    class Meta:
        model = ProviderServiceLink
        fields = [
            'id',
            'service',
            'prix_base',
            'delai',
            'is_available',
            'created',
            'updated',
        ]
        read_only_fields = ['id', 'created', 'updated']

    def get_service(self, obj: ProviderServiceLink):
        return {
            'id': str(obj.service.id),
            'label': obj.service.label,
            'mode_tarif': obj.service.mode_tarif,
            'description': obj.service.description,
            'icone': obj.service.icone,
        }


class ProviderServiceWriteSerializer(serializers.Serializer):
    service_id = serializers.UUIDField(required=False)
    label = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    mode_tarif = serializers.ChoiceField(choices=Service.MODE_TARIF_CHOICES, required=False)
    duree_estimee = serializers.IntegerField(required=False)
    icone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    template_id = serializers.UUIDField(required=False)
    prix_base = serializers.DecimalField(max_digits=10, decimal_places=2)
    delai = serializers.IntegerField(min_value=1)
    is_available = serializers.BooleanField(default=True)

    def validate(self, attrs):
        provider = self.context['provider']
        if self.instance:
            if any(field in attrs for field in ('service_id', 'template_id', 'label', 'mode_tarif', 'duree_estimee')):
                raise serializers.ValidationError("La modification du service lié n'est pas autorisée.")
            return attrs

        if attrs.get('service_id'):
            service = self._validate_existing_service(provider, attrs['service_id'])
        else:
            template = None
            if attrs.get('template_id'):
                template = self._validate_template(attrs['template_id'])
                attrs.setdefault('mode_tarif', template.mode_tarif)
                attrs.setdefault('duree_estimee', template.duree_estimee)
                if template.description and 'description' not in attrs:
                    attrs['description'] = template.description
                if template.icone and 'icone' not in attrs:
                    attrs['icone'] = template.icone

            required_fields = ['label', 'mode_tarif', 'duree_estimee']
            missing = [field for field in required_fields if not attrs.get(field)]
            if missing:
                raise serializers.ValidationError(
                    f"Champs requis pour créer un service personnalisé: {', '.join(missing)}."
                )
            service = Service.objects.create(
                provider=provider,
                label=attrs['label'],
                description=attrs.get('description', ''),
                mode_tarif=attrs['mode_tarif'],
                duree_estimee=attrs['duree_estimee'],
                icone=attrs.get('icone', ''),
                template=template,
            )

        attrs['service'] = service
        return attrs

    def _validate_existing_service(self, provider, service_id):
        try:
            service = Service.objects.get(id=service_id)
        except Service.DoesNotExist as exc:
            raise serializers.ValidationError({'service_id': 'Service introuvable.'}) from exc
        if service.provider and service.provider != provider:
            raise serializers.ValidationError({'service_id': 'Service non autorisé pour ce prestataire.'})
        return service

    def _validate_template(self, template_id):
        try:
            return ServiceTemplate.objects.get(id=template_id, is_active=True)
        except ServiceTemplate.DoesNotExist as exc:
            raise serializers.ValidationError({'template_id': 'Template introuvable.'}) from exc

    def create(self, validated_data):
        provider = self.context['provider']
        service = validated_data['service']
        return ProviderServiceLink.objects.create(
            provider=provider,
            service=service,
            prix_base=validated_data['prix_base'],
            delai=validated_data['delai'],
            is_available=validated_data.get('is_available', True),
        )

    def update(self, instance: ProviderServiceLink, validated_data):
        # service change n'est pas supporté via PATCH
        for field in ['prix_base', 'delai', 'is_available']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save(update_fields=['prix_base', 'delai', 'is_available', 'updated'])
        return instance


class ArticleTypeSerializer(serializers.ModelSerializer):
    template = serializers.SerializerMethodField()

    class Meta:
        model = ArticleType
        fields = ['id', 'nom', 'description', 'template', 'created']
        read_only_fields = ['id', 'created', 'template']

    def get_template(self, obj):
        if obj.template:
            return {'id': str(obj.template.id), 'nom': obj.template.nom}
        return None


class ArticleTypeWriteSerializer(serializers.ModelSerializer):
    template_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = ArticleType
        fields = ['nom', 'description', 'template_id']

    def validate_template_id(self, value):
        if not value:
            return None
        from apps.services.models import ArticleTypeTemplate

        try:
            return ArticleTypeTemplate.objects.get(id=value)
        except ArticleTypeTemplate.DoesNotExist as exc:
            raise serializers.ValidationError("Template introuvable.") from exc

    def create(self, validated_data):
        provider = self.context['provider']
        template = validated_data.pop('template_id', None)
        return ArticleType.objects.create(provider=provider, template=template, **validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('template_id', None)
        return super().update(instance, validated_data)


class MatiereSerializer(serializers.ModelSerializer):
    template = serializers.SerializerMethodField()

    class Meta:
        model = Matiere
        fields = ['id', 'nom', 'description', 'template', 'created']
        read_only_fields = ['id', 'created', 'template']

    def get_template(self, obj):
        if obj.template:
            return {'id': str(obj.template.id), 'nom': obj.template.nom}
        return None


class MatiereWriteSerializer(serializers.ModelSerializer):
    template_id = serializers.UUIDField(required=False, allow_null=True, write_only=True)

    class Meta:
        model = Matiere
        fields = ['nom', 'description', 'template_id']

    def validate_template_id(self, value):
        if not value:
            return None
        from apps.services.models import MatiereTemplate

        try:
            return MatiereTemplate.objects.get(id=value)
        except MatiereTemplate.DoesNotExist as exc:
            raise serializers.ValidationError("Template introuvable.") from exc

    def create(self, validated_data):
        provider = self.context['provider']
        template = validated_data.pop('template_id', None)
        return Matiere.objects.create(provider=provider, template=template, **validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('template_id', None)
        return super().update(instance, validated_data)


class TariffSerializer(serializers.ModelSerializer):
    article_type = serializers.SerializerMethodField()
    matiere = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()

    class Meta:
        model = Tariff
        fields = ['id', 'article_type', 'matiere', 'service', 'prix', 'created', 'updated']

    def get_article_type(self, obj):
        return {'id': str(obj.article_type.id), 'nom': obj.article_type.nom}

    def get_matiere(self, obj):
        if obj.matiere:
            return {'id': str(obj.matiere.id), 'nom': obj.matiere.nom}
        return None

    def get_service(self, obj):
        return {'id': str(obj.service.id), 'label': obj.service.label}


class TariffWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = ['article_type', 'matiere', 'service', 'prix']

    def validate(self, attrs):
        provider = self.context['provider']
        article_type = attrs['article_type']
        if article_type.provider != provider:
            raise serializers.ValidationError({'article_type': "Type d'article invalide."})
        matiere = attrs.get('matiere')
        if matiere and matiere.provider != provider:
            raise serializers.ValidationError({'matiere': "Matière invalide."})
        service = attrs['service']
        if service.provider and service.provider != provider:
            raise serializers.ValidationError({'service': "Service invalide pour ce prestataire."})
        attrs['provider'] = provider
        return attrs

