"""
Utilitaires de normalisation des numéros de téléphone (format E.164)
"""
from __future__ import annotations

import re
from typing import Final

from django.conf import settings

_E164_REGEX: Final[re.Pattern[str]] = re.compile(r"^\+[1-9]\d{5,14}$")


def is_e164(value: str) -> bool:
    """
    Vérifie si une chaîne est valide au format E.164 (+CC...).
    """
    if not value:
        return False
    return bool(_E164_REGEX.match(value))


def normalize_to_e164(raw_phone: str) -> str:
    """
    Normalise un numéro vers E.164 en utilisant un indicatif par défaut.

    Politique :
    - Si commence par '+', conserve '+' + chiffres.
    - Sinon, si commence par l'indicatif (ex: 225), on préfixe '+'.
    - Sinon, on conserve les zéros initiaux du numéro local et on préfixe l'indicatif par défaut.
    """
    default_cc = getattr(settings, 'DEFAULT_COUNTRY_CODE', '+225')
    default_cc_digits = default_cc.lstrip('+')

    s = (raw_phone or '').strip()
    if not s:
        return ''

    if s.startswith('+'):
        digits = ''.join(ch for ch in s if ch.isdigit())
        return f'+{digits}' if digits else ''

    digits_only = ''.join(ch for ch in s if ch.isdigit())
    if not digits_only:
        return ''

    if digits_only.startswith(default_cc_digits):
        return f'+{digits_only}'

    return f'+{default_cc_digits}{digits_only}'

