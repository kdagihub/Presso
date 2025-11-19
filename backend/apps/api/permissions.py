"""Permissions et helpers pour l'espace prestataire."""
from __future__ import annotations

from typing import Optional, Tuple

from rest_framework.permissions import BasePermission  # type: ignore
from rest_framework.exceptions import PermissionDenied  # type: ignore

from apps.providers.models import Provider, ProviderStaff


def get_provider_context(user) -> Tuple[Optional[Provider], Optional[ProviderStaff]]:
    provider = getattr(user, 'provider_profile', None)
    staff = None
    if provider:
        staff = user.staff_assignments.filter(provider=provider).first()
        return provider, staff

    staff = user.staff_assignments.select_related('provider').first()
    if staff:
        return staff.provider, staff

    if user.custom_role_id:
        provider = user.custom_role.provider  # type: ignore[assignment]
        staff = user.staff_assignments.filter(provider=provider).first()
        return provider, staff
    return None, None


def _attach_context(request, provider: Optional[Provider], staff: Optional[ProviderStaff]) -> None:
    if provider:
        setattr(request, 'provider', provider)
    if staff or staff is None:
        setattr(request, 'provider_staff', staff)


def require_provider_member(request) -> Tuple[Provider, Optional[ProviderStaff]]:
    provider = getattr(request, 'provider', None)
    staff = getattr(request, 'provider_staff', None)
    if provider:
        return provider, staff
    provider, staff = get_provider_context(request.user)
    if not provider:
        raise PermissionDenied("Accès réservé aux prestataires")
    _attach_context(request, provider, staff)
    return provider, staff


def require_can_manage_staff(request) -> Tuple[Provider, Optional[ProviderStaff]]:
    provider, staff = require_provider_member(request)
    user = request.user
    if user.is_superuser:
        return provider, staff
    if getattr(provider, 'user_id', None) == user.id:
        return provider, staff
    if staff and staff.system_role in {'owner', 'manager'}:
        return provider, staff
    if user.has_custom_permission('staff.manage'):
        return provider, staff
    raise PermissionDenied("Permission insuffisante pour gérer le staff")


def require_can_manage_settings(request) -> Tuple[Provider, Optional[ProviderStaff]]:
    provider, staff = require_provider_member(request)
    user = request.user
    if user.is_superuser or getattr(provider, 'user_id', None) == user.id:
        return provider, staff
    if staff and staff.system_role in {'owner', 'manager'}:
        return provider, staff
    if user.has_custom_permission('settings.manage'):
        return provider, staff
    raise PermissionDenied("Permission insuffisante pour gérer les paramètres")


def require_can_manage_services(request) -> Tuple[Provider, Optional[ProviderStaff]]:
    provider, staff = require_provider_member(request)
    user = request.user
    if user.is_superuser or getattr(provider, 'user_id', None) == user.id:
        return provider, staff
    if staff and staff.system_role in {'owner', 'manager'}:
        return provider, staff
    if user.has_custom_permission('services.manage'):
        return provider, staff
    raise PermissionDenied("Permission insuffisante pour gérer les services")


def require_can_manage_tariffs(request) -> Tuple[Provider, Optional[ProviderStaff]]:
    provider, staff = require_provider_member(request)
    user = request.user
    if user.is_superuser or getattr(provider, 'user_id', None) == user.id:
        return provider, staff
    if staff and staff.system_role in {'owner', 'manager'}:
        return provider, staff
    if user.has_custom_permission('tariffs.manage'):
        return provider, staff
    raise PermissionDenied("Permission insuffisante pour gérer les tarifs")


def require_can_manage_orders(request) -> Tuple[Provider, Optional[ProviderStaff]]:
    provider, staff = require_provider_member(request)
    user = request.user
    if user.is_superuser or getattr(provider, 'user_id', None) == user.id:
        return provider, staff
    if staff and staff.system_role in {'owner', 'manager', 'operator'}:
        return provider, staff
    if user.has_custom_permission('orders.manage'):
        return provider, staff
    raise PermissionDenied("Permission insuffisante pour gérer les commandes")


class IsProviderMember(BasePermission):
    message = "Accès réservé aux prestataires"

    def has_permission(self, request, view) -> bool:
        provider, staff = get_provider_context(request.user)
        if provider:
            _attach_context(request, provider, staff)
            return True
        return False


class CanManageStaff(IsProviderMember):
    message = "Permission insuffisante pour gérer le staff"

    def has_permission(self, request, view) -> bool:
        if not super().has_permission(request, view):
            return False
        provider = getattr(request, 'provider', None)
        staff = getattr(request, 'provider_staff', None)
        user = request.user
        if user.is_superuser or getattr(provider, 'user_id', None) == user.id:
            return True
        if staff and staff.system_role in {'owner', 'manager'}:
            return True
        if user.has_custom_permission('staff.manage'):
            return True
        return False


class IsProviderOwner(IsProviderMember):
    message = "Action réservée au propriétaire"

    def has_permission(self, request, view) -> bool:
        if not super().has_permission(request, view):
            return False
        provider = getattr(request, 'provider', None)
        staff = getattr(request, 'provider_staff', None)
        if getattr(provider, 'user_id', None) == request.user.id:
            return True
        if staff and staff.system_role == 'owner':
            return True
        return False


class CanManageServices(IsProviderMember):
    message = "Permission insuffisante pour gérer les services"

    def has_permission(self, request, view) -> bool:
        if not super().has_permission(request, view):
            return False
        provider = getattr(request, 'provider', None)
        staff = getattr(request, 'provider_staff', None)
        user = request.user
        if user.is_superuser or getattr(provider, 'user_id', None) == user.id:
            return True
        if staff and staff.system_role in {'owner', 'manager'}:
            return True
        if user.has_custom_permission('services.manage'):
            return True
        return False


class CanManageTariffs(IsProviderMember):
    message = "Permission insuffisante pour gérer les tarifs"

    def has_permission(self, request, view) -> bool:
        if not super().has_permission(request, view):
            return False
        provider = getattr(request, 'provider', None)
        staff = getattr(request, 'provider_staff', None)
        user = request.user
        if user.is_superuser or getattr(provider, 'user_id', None) == user.id:
            return True
        if staff and staff.system_role in {'owner', 'manager'}:
            return True
        if user.has_custom_permission('tariffs.manage'):
            return True
        return False


class CanManageOrders(IsProviderMember):
    message = "Permission insuffisante pour gérer les commandes"

    def has_permission(self, request, view) -> bool:
        if not super().has_permission(request, view):
            return False
        provider = getattr(request, 'provider', None)
        staff = getattr(request, 'provider_staff', None)
        user = request.user
        if user.is_superuser or getattr(provider, 'user_id', None) == user.id:
            return True
        if staff and staff.system_role in {'owner', 'manager', 'operator'}:
            return True
        if user.has_custom_permission('orders.manage'):
            return True
        return False


class CanManageSettings(IsProviderMember):
    message = "Permission insuffisante pour gérer les paramètres"

    def has_permission(self, request, view) -> bool:
        if not super().has_permission(request, view):
            return False
        provider = getattr(request, 'provider', None)
        staff = getattr(request, 'provider_staff', None)
        user = request.user
        if user.is_superuser or getattr(provider, 'user_id', None) == user.id:
            return True
        if staff and staff.system_role in {'owner', 'manager'}:
            return True
        if user.has_custom_permission('settings.manage'):
            return True
        return False
