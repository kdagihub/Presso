"""
Client D7 Verify pour l'envoi et la vérification des OTP.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import requests
from django.conf import settings  # type: ignore

logger = logging.getLogger(__name__)


class D7VerifyError(Exception):
    """Erreur d'appel au service D7 Verify."""


class D7VerifyClient:
    def __init__(self) -> None:
        self.base_url = getattr(settings, 'D7_API_BASE_URL', 'https://api.d7networks.com').rstrip('/')
        self.api_token = getattr(settings, 'D7_API_TOKEN', '')
        self.originator = getattr(settings, 'D7_ORIGINATOR', 'Pressow-OTP')
        self.timeout = getattr(settings, 'D7_TIMEOUT_SECONDS', 20)

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def send_otp(
        self,
        recipient_e164: str,
        *,
        content: Optional[str] = None,
        template_id: Optional[int] = None,
        expiry: int = 600,
        otp_code_length: int = 6,
        otp_type: str = 'numeric',
    ) -> dict:
        url = f"{self.base_url}/verify/v1/otp/send-otp"
        payload: dict = {
            'originator': self.originator,
            'recipient': recipient_e164,
            'expiry': expiry,
            'otp_code_length': otp_code_length,
            'otp_type': otp_type,
        }
        if template_id:
            payload['template_id'] = template_id
        else:
            payload['content'] = content or 'Votre code de vérification Pressow est: {}'
        return self._post(url, payload, 'send_otp')

    def resend_otp(self, otp_id: str) -> dict:
        url = f"{self.base_url}/verify/v1/otp/resend-otp"
        return self._post(url, {'otp_id': otp_id}, 'resend_otp')

    def verify_otp(self, otp_id: str, otp_code: str) -> dict:
        url = f"{self.base_url}/verify/v1/otp/verify-otp"
        return self._post(url, {'otp_id': otp_id, 'otp_code': otp_code}, 'verify_otp')

    def get_status(self, otp_id: str) -> dict:
        url = f"{self.base_url}/verify/v1/report/{otp_id}"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=self.timeout)
            if not resp.ok:
                logger.error('D7 get_status failed: status=%s', resp.status_code)
                raise D7VerifyError(f"D7 get_status error: {resp.status_code}")
            return resp.json()
        except requests.RequestException as exc:
            logger.exception('D7 get_status request exception')
            raise D7VerifyError('D7 get_status exception') from exc

    def _post(self, url: str, body: dict, label: str) -> dict:
        try:
            resp = requests.post(url, headers=self._headers(), data=json.dumps(body), timeout=self.timeout)
            if not resp.ok:
                logger.error('D7 %s failed: status=%s', label, resp.status_code)
                try:
                    _ = resp.json()
                except Exception:
                    pass
                raise D7VerifyError(f"D7 {label} error: {resp.status_code}")
            return resp.json()
        except requests.RequestException as exc:
            logger.exception('D7 %s request exception', label)
            raise D7VerifyError(f'D7 {label} exception') from exc

