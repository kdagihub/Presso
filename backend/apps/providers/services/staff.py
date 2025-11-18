"""Services utilitaires pour la gestion du staff prestataire."""
from __future__ import annotations

import secrets
from typing import Optional

from django.utils import timezone  # type: ignore
from django.contrib.auth import get_user_model  # type: ignore

from apps.providers.models import Provider, ProviderAgency, ProviderStaff

User = get_user_model()
_SENTINEL = object()


def generate_invite_token() -> str:
    """Génère un token d'invitation aléatoire."""
    return secrets.token_urlsafe(32)


def invite_staff(
    *,
    provider: Provider,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    system_role: str = 'operator',
    role=None,
    agency: Optional[ProviderAgency] = None,
) -> ProviderStaff:
    """Crée une invitation pour un membre du staff (sans compte utilisateur)."""
    token = generate_invite_token()
    staff = ProviderStaff.objects.create(
        provider=provider,
        agency=agency,
        system_role=system_role,
        role=role,
        status='invited',
        invited_email=email or '',
        invited_phone=phone or '',
        invite_token=token,
        invited_at=timezone.now(),
    )
    return staff


def activate_staff(invite_token: str, user: User) -> ProviderStaff:
    """Active un membre du staff à partir de son token."""
    staff = ProviderStaff.objects.get(invite_token=invite_token, status='invited')
    staff.user = user
    staff.status = 'active'
    staff.activated_at = timezone.now()
    staff.invite_token = ''
    staff.save(update_fields=['user', 'status', 'activated_at', 'invite_token'])
    return staff


def assign_role(
    staff: ProviderStaff,
    *,
    system_role: Optional[str] = None,
    role=_SENTINEL,
    agency=_SENTINEL,
) -> ProviderStaff:
    """Met à jour les rôles/affectations d'un staff."""
    fields_to_update: list[str] = []
    if system_role and staff.system_role != system_role:
        staff.system_role = system_role
        fields_to_update.append('system_role')
    if role is not _SENTINEL and staff.role != role:
        staff.role = role
        fields_to_update.append('role')
    if agency is not _SENTINEL and staff.agency != agency:
        staff.agency = agency
        fields_to_update.append('agency')
    if fields_to_update:
        staff.save(update_fields=fields_to_update)
    return staff
