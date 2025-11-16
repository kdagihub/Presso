"""
Utilitaires d'audit des événements d'authentification.
"""
from __future__ import annotations

import hashlib
from typing import Optional, Any, Dict

from django.http import HttpRequest

from apps.core.models import AuthEventLog


def _hash_phone(phone: Optional[str]) -> str:
    if not phone:
        return ''
    return hashlib.sha256(phone.encode('utf-8')).hexdigest()


def write_auth_event(
    event: str,
    request: Optional[HttpRequest] = None,
    *,
    user=None,
    phone_e164: Optional[str] = None,
    success: bool = True,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Enregistre un événement d'auth (login, otp, reset...).
    """
    ip_address = None
    user_agent = ''
    if request is not None:
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] or request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

    AuthEventLog.objects.create(
        event=event,
        user=user if getattr(user, 'is_authenticated', False) else None,
        phone_hash=_hash_phone(phone_e164),
        ip_address=ip_address,
        user_agent=user_agent[:512],
        success=success,
        metadata=metadata or {},
    )

