"""Serializers pour les endpoints Provider (agences & staff)."""
from __future__ import annotations

from typing import Any, Optional

from rest_framework import serializers  # type: ignore

from apps.providers.models import ProviderAgency, ProviderStaff
from apps.core.models import Role


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
