"""Endpoints Provider (agences, staff, rôles)."""
from __future__ import annotations

from typing import Optional

from django.db import transaction  # type: ignore
from rest_framework import permissions, status  # type: ignore
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied  # type: ignore
from rest_framework.response import Response  # type: ignore
from rest_framework.views import APIView  # type: ignore

from apps.api.permissions import (
    IsProviderMember,
    CanManageStaff,
    require_provider_member,
    require_can_manage_staff,
)
from apps.api.serializers.providers import (
    ProviderAgencySerializer,
    ProviderAgencyWriteSerializer,
    ProviderStaffSerializer,
    ProviderStaffInviteSerializer,
    ProviderStaffUpdateSerializer,
    ProviderStaffActivateSerializer,
)
from apps.providers.models import Provider, ProviderAgency, ProviderStaff
from apps.providers.services.staff import invite_staff, activate_staff, assign_role


def _get_agency_or_404(provider: Provider, agency_id) -> ProviderAgency:
    try:
        return provider.agencies.get(id=agency_id)
    except ProviderAgency.DoesNotExist as exc:
        raise NotFound('Agence introuvable') from exc


def _get_staff_or_404(provider: Provider, staff_id) -> ProviderStaff:
    try:
        return provider.staff_members.select_related('user', 'agency', 'role').get(id=staff_id)
    except ProviderStaff.DoesNotExist as exc:
        raise NotFound('Membre du staff introuvable') from exc


def _ensure_single_default(
    provider: Provider,
    agency: ProviderAgency,
    desired_state: Optional[bool] = None,
) -> None:
    if desired_state is not None:
        agency.is_default = desired_state

    if agency.is_default:
        provider.agencies.exclude(id=agency.id).filter(is_default=True).update(is_default=False)
        agency.save(update_fields=['is_default'])
    elif not provider.agencies.filter(is_default=True).exists():
        agency.is_default = True
        agency.save(update_fields=['is_default'])


def _ensure_default_after_delete(provider: Provider) -> None:
    if not provider.agencies.filter(is_default=True).exists():
        next_agency = provider.agencies.order_by('created').first()
        if next_agency:
            next_agency.is_default = True
            next_agency.save(update_fields=['is_default'])


def _assert_can_modify_owner(actor: Optional[ProviderStaff], target: ProviderStaff) -> None:
    if target.system_role != 'owner':
        return
    if actor and actor.system_role == 'owner':
        return
    raise PermissionDenied("Seul le propriétaire peut modifier un propriétaire")


class ProviderAgencyListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]

    def get(self, request):
        provider, _ = require_provider_member(request)
        agencies = provider.agencies.order_by('-is_default', 'name')
        serializer = ProviderAgencySerializer(agencies, many=True)
        return Response(serializer.data)

    def post(self, request):
        provider, _ = require_can_manage_staff(request)
        serializer = ProviderAgencyWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        make_default = serializer.validated_data.pop('is_default', None)
        with transaction.atomic():
            agency = serializer.save(provider=provider)
            _ensure_single_default(provider, agency, desired_state=make_default)
        return Response(ProviderAgencySerializer(agency).data, status=status.HTTP_201_CREATED)


class ProviderAgencyDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]

    def get(self, request, agency_id):
        provider, _ = require_provider_member(request)
        agency = _get_agency_or_404(provider, agency_id)
        return Response(ProviderAgencySerializer(agency).data)

    def patch(self, request, agency_id):
        provider, _ = require_can_manage_staff(request)
        agency = _get_agency_or_404(provider, agency_id)
        serializer = ProviderAgencyWriteSerializer(agency, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        make_default = serializer.validated_data.pop('is_default', None)
        with transaction.atomic():
            agency = serializer.save()
            _ensure_single_default(provider, agency, desired_state=make_default)
        return Response(ProviderAgencySerializer(agency).data)

    def delete(self, request, agency_id):
        provider, _ = require_can_manage_staff(request)
        agency = _get_agency_or_404(provider, agency_id)
        if agency.is_default and not provider.agencies.exclude(id=agency.id).exists():
            raise ValidationError('Impossible de supprimer l\'unique agence du prestataire.')
        agency.delete()
        _ensure_default_after_delete(provider)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProviderStaffListView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageStaff]

    def get(self, request):
        provider, _ = require_can_manage_staff(request)
        staff_qs = provider.staff_members.select_related('user', 'agency', 'role').order_by('-system_role', 'user__first_name')
        return Response(ProviderStaffSerializer(staff_qs, many=True).data)


class ProviderStaffInviteView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageStaff]

    def post(self, request):
        provider, _ = require_can_manage_staff(request)
        serializer = ProviderStaffInviteSerializer(data=request.data, context={'provider': provider})
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        staff = invite_staff(
            provider=provider,
            email=payload.get('email'),
            phone=payload.get('phone'),
            system_role=payload.get('system_role', 'operator'),
            role=payload.get('role'),
            agency=payload.get('agency'),
        )
        if payload.get('notes'):
            staff.notes = payload['notes']
            staff.save(update_fields=['notes'])
        return Response(ProviderStaffSerializer(staff).data, status=status.HTTP_201_CREATED)


class ProviderStaffDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageStaff]

    def get(self, request, staff_id):
        provider, _ = require_can_manage_staff(request)
        staff = _get_staff_or_404(provider, staff_id)
        return Response(ProviderStaffSerializer(staff).data)

    def patch(self, request, staff_id):
        provider, actor = require_can_manage_staff(request)
        staff = _get_staff_or_404(provider, staff_id)
        _assert_can_modify_owner(actor, staff)
        serializer = ProviderStaffUpdateSerializer(data=request.data, context={'provider': provider})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        updates = []
        if 'system_role' in data:
            staff.system_role = data['system_role']
            updates.append('system_role')
        if 'status' in data:
            staff.status = data['status']
            updates.append('status')
        if 'notes' in data:
            staff.notes = data['notes']
            updates.append('notes')
        assign_kwargs = {}
        if data.get('role_provided'):
            assign_kwargs['role'] = data.get('role')
        if data.get('agency_provided'):
            assign_kwargs['agency'] = data.get('agency')
        if assign_kwargs:
            assign_role(staff, **assign_kwargs)

        if updates:
            staff.save(update_fields=list(set(updates)))
        staff.refresh_from_db()
        return Response(ProviderStaffSerializer(staff).data)

    def delete(self, request, staff_id):
        provider, actor = require_can_manage_staff(request)
        staff = _get_staff_or_404(provider, staff_id)
        _assert_can_modify_owner(actor, staff)
        staff.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProviderStaffActivateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ProviderStaffActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            staff = activate_staff(serializer.validated_data['invite_token'], request.user)
        except ProviderStaff.DoesNotExist as exc:
            raise NotFound('Invitation introuvable ou expirée') from exc
        return Response(ProviderStaffSerializer(staff).data)
