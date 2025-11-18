"""
APIViews pour l'authentification avancée (OTP stateless + JWT).
"""
from __future__ import annotations

import random
import time
from datetime import timedelta

from decimal import Decimal, InvalidOperation

from django.conf import settings  # type: ignore
from django.contrib.auth import authenticate, get_user_model  # type: ignore
from django.contrib.auth.hashers import make_password  # type: ignore
from django.core import signing  # type: ignore
from django.core.cache import cache  # type: ignore
from django.utils import timezone  # type: ignore
from rest_framework import permissions, status  # type: ignore
from rest_framework.response import Response  # type: ignore
from rest_framework.views import APIView  # type: ignore
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken  # type: ignore
from rest_framework_simplejwt.tokens import RefreshToken  # type: ignore

from apps.api.serializers.auth import (
    ClientRegisterSerializer,
    ProviderRegisterSerializer,
    LoginSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    PasswordResetFinalizeSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
)
from apps.core.audit import write_auth_event
from apps.core.models import Permission, Role
from apps.core.services.d7_verify import D7VerifyClient, D7VerifyError
from apps.core.utils.phone import normalize_to_e164
from apps.providers.models import Provider, ProviderAgency, ProviderStaff

SERVICE_TYPE_MAP = {
    'pressing-linge': 'pressing',
    'pressing-chaussures': 'pressing_chaussures',
    'blanchisserie': 'blanchisserie',
    'laverie': 'laverie',
    'fanico': 'fanico',
    'nettoyage': 'nettoyage',
    'autre': 'autre',
}

User = get_user_model()

REFRESH_COOKIE_NAME = 'refresh_token'
REFRESH_COOKIE_PATH = '/api/auth/'


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age = int(settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME', timedelta(days=7)).total_seconds())
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=not settings.DEBUG,
        samesite=getattr(settings, 'AUTH_COOKIE_SAMESITE', 'Lax'),
        path=REFRESH_COOKIE_PATH,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


def _build_pending_token(payload: dict) -> str:
    return signing.dumps(payload, salt='presso-signup')


def _read_pending_token(token: str) -> dict:
    data = signing.loads(token, salt='presso-signup')
    exp_ts = data.get('exp_ts')
    if exp_ts and timezone.now().timestamp() > float(exp_ts):
        raise signing.BadSignature('pending token expired')
    return data


def _build_reset_token(payload: dict) -> str:
    return signing.dumps(payload, salt='presso-reset')


def _read_reset_token(token: str) -> dict:
    data = signing.loads(token, salt='presso-reset')
    exp_ts = data.get('exp_ts')
    if exp_ts and timezone.now().timestamp() > float(exp_ts):
        raise signing.BadSignature('reset token expired')
    return data


def _build_reset_session_token(payload: dict) -> str:
    return signing.dumps(payload, salt='presso-reset-session')


def _read_reset_session_token(token: str) -> dict:
    data = signing.loads(token, salt='presso-reset-session')
    exp_ts = data.get('exp_ts')
    if exp_ts and timezone.now().timestamp() > float(exp_ts):
        raise signing.BadSignature('reset session token expired')
    return data


def _is_same_site_request(request) -> bool:
    allowed = set(getattr(settings, 'CORS_ALLOWED_ORIGINS', []))
    if settings.DEBUG:
        allowed.update({
            'http://localhost:5173',
            'http://localhost:3000',
            'http://127.0.0.1:5173',
        })

    if not settings.DEBUG:
        if request.META.get('HTTP_X_REQUESTED_WITH', '').lower() != 'xmlhttprequest':
            return False

    header = request.META.get('HTTP_ORIGIN') or request.META.get('HTTP_REFERER')
    if not settings.DEBUG and not header:
        return False
    if not header:
        return True
    return any(str(header).startswith(origin) for origin in allowed)


_LOGIN_FAIL_MAX = 5
_LOGIN_FAIL_WINDOW_SEC = 15 * 60
_LOGIN_LOCKOUT_SEC = 15 * 60


def _cache_key_login_fail(identifier: str) -> str:
    return f"auth:login:fail:{identifier}"


def _cache_key_login_lock(identifier: str) -> str:
    return f"auth:login:lock:{identifier}"


def _login_is_locked(identifier: str) -> int:
    key = _cache_key_login_lock(identifier)
    ttl = cache.ttl(key)
    if ttl is None:
        return 1 if cache.get(key) else 0
    return max(ttl, 0)


def _register_login_failure(identifier: str) -> int:
    key = _cache_key_login_fail(identifier)
    try:
        count = cache.incr(key)
    except Exception:
        count = 1
        cache.set(key, count, timeout=_LOGIN_FAIL_WINDOW_SEC)
    if count == 1 and hasattr(cache, 'expire'):
        try:
            cache.expire(key, _LOGIN_FAIL_WINDOW_SEC)
        except Exception:
            pass
    if count >= _LOGIN_FAIL_MAX:
        cache.set(_cache_key_login_lock(identifier), True, timeout=_LOGIN_LOCKOUT_SEC)
    return count


def _reset_login_failures(identifier: str) -> None:
    cache.delete_many([_cache_key_login_fail(identifier), _cache_key_login_lock(identifier)])


def _jitter_sleep(base_ms: int = 100, spread_ms: int = 200) -> None:
    try:
        sleep_for = (base_ms + random.randint(0, spread_ms)) / 1000.0
        time.sleep(sleep_for)
    except Exception:
        pass


def _backoff_key(prefix: str, key: str) -> str:
    return f"auth:backoff:{prefix}:{key}"


def _register_backoff(prefix: str, key: str, window_sec: int = 300) -> int:
    cache_key = _backoff_key(prefix, key)
    try:
        count = cache.incr(cache_key)
    except Exception:
        count = 1
        cache.set(cache_key, count, timeout=window_sec)
    if count == 1 and hasattr(cache, 'expire'):
        try:
            cache.expire(cache_key, window_sec)
        except Exception:
            pass
    return count


DEFAULT_ROLE_DEFINITIONS = {
    'owner': {
        'name': 'Owner',
        'description': "Propriétaire du pressing",
        'permissions': '__all__',
    },
    'manager': {
        'name': 'Manager',
        'description': "Gestionnaire d'agence",
        'permissions': [
            'orders.view', 'orders.manage',
            'services.view', 'services.manage',
            'tariffs.manage', 'customers.view',
            'staff.manage', 'stats.view',
        ],
    },
    'operator': {
        'name': 'Opérateur',
        'description': "Employé chargé des commandes",
        'permissions': ['orders.view', 'orders.manage', 'services.view'],
    },
    'delivery': {
        'name': 'Livreur',
        'description': "Collecte et livraison",
        'permissions': ['orders.view'],
    },
}


def _split_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or '').strip().split()
    if not parts:
        return '', ''
    first = parts[0]
    last = ' '.join(parts[1:]) if len(parts) > 1 else ''
    return first, last


def _create_provider_profile(user: User, provider_data: dict) -> Provider:
    company_name = provider_data.get('company_name') or user.get_full_name() or user.username
    service_type = provider_data.get('service_type', 'autre')
    mapped_type = SERVICE_TYPE_MAP.get(service_type, 'autre')
    city = provider_data.get('city') or ''
    coverage_description = city or 'À définir'
    address = city or 'À définir'
    district = ''
    radius_value = Decimal('5')

    provider = Provider.objects.create(
        user=user,
        type=mapped_type,
        nom_commercial=company_name,
        zone_couverture=coverage_description,
        rayon_km=radius_value,
        adresse=address,
        quartier=district,
    )
    return provider


def _ensure_default_agency(provider: Provider, provider_data: dict) -> ProviderAgency:
    agency = provider.agencies.filter(is_default=True).first()
    if agency:
        return agency

    adresse = provider.adresse or provider_data.get('city') or 'Adresse principale'
    ville = provider_data.get('city') or 'Abidjan'
    quartier = provider.quartier or provider_data.get('quartier') or ''

    agency = ProviderAgency.objects.create(
        provider=provider,
        name="Agence principale",
        code='MAIN',
        description="Agence créée automatiquement",
        adresse=adresse,
        ville=ville,
        quartier=quartier,
        is_default=True,
        is_active=True,
    )
    return agency


def _ensure_default_roles(provider: Provider) -> dict[str, Role]:
    roles: dict[str, Role] = {}
    required_codes = {
        code
        for config in DEFAULT_ROLE_DEFINITIONS.values()
        if config['permissions'] != '__all__'
        for code in config['permissions']
    }
    permissions_map = {
        perm.code: perm
        for perm in Permission.objects.filter(code__in=required_codes)
    }
    all_permissions = None

    for system_key, config in DEFAULT_ROLE_DEFINITIONS.items():
        role, _ = Role.objects.get_or_create(
            provider=provider,
            name=config['name'],
            defaults={'description': config['description'], 'is_active': True},
        )
        role.description = config['description']
        role.is_active = True
        role.save(update_fields=['description', 'is_active'])

        if config['permissions'] == '__all__':
            if all_permissions is None:
                all_permissions = list(Permission.objects.filter(is_active=True))
            perms = all_permissions
        else:
            perms = [permissions_map[code] for code in config['permissions'] if code in permissions_map]
        role.permissions.set(perms)
        roles[system_key] = role
    return roles


def _ensure_owner_staff(
    provider: Provider,
    agency: ProviderAgency,
    user: User,
    owner_role: Role | None,
) -> ProviderStaff:
    defaults = {
        'agency': agency,
        'system_role': 'owner',
        'role': owner_role,
        'status': 'active',
        'activated_at': timezone.now(),
    }
    staff, created = ProviderStaff.objects.get_or_create(
        provider=provider,
        user=user,
        defaults=defaults,
    )
    if not created:
        changed = False
        for field, value in defaults.items():
            current = getattr(staff, field)
            if current != value:
                setattr(staff, field, value)
                changed = True
        if changed:
            staff.save(update_fields=list(defaults.keys()))
    return staff


def _bootstrap_provider_account(user: User, provider_payload: dict) -> Provider:
    provider = _create_provider_profile(user, provider_payload)
    agency = _ensure_default_agency(provider, provider_payload)
    role_map = _ensure_default_roles(provider)
    owner_role = role_map.get('owner')
    _ensure_owner_staff(provider, agency, user, owner_role)
    if owner_role and user.custom_role != owner_role:
        user.custom_role = owner_role
        user.save(update_fields=['custom_role'])
    return provider


class RegisterClientView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'otp_request'

    def post(self, request):
        serializer = ClientRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        phone_e164 = vd['phone']

        if (
            User.objects.filter(phone=phone_e164).exists()
            or (vd.get('email') and User.objects.filter(email__iexact=vd['email']).exists())
        ):
            _register_backoff('register', request.META.get('REMOTE_ADDR', ''))
            _jitter_sleep()
            return Response({'requires_otp': False, 'detail': 'Si éligible, un OTP a été envoyé'}, status=status.HTTP_200_OK)

        d7 = D7VerifyClient()
        try:
            otp_payload = d7.send_otp(
                phone_e164,
                expiry=settings.OTP_EXPIRY_MINUTES * 60,
                otp_code_length=settings.OTP_LENGTH,
            )
        except D7VerifyError:
            write_auth_event('OTP_PROVIDER_ERROR', request, phone_e164=phone_e164, success=False)
            return Response({'detail': 'Service OTP indisponible, réessayez plus tard'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        otp_id = otp_payload.get('otp_id') or otp_payload.get('request_id')
        expiry_seconds = int(otp_payload.get('expiry', settings.OTP_EXPIRY_MINUTES * 60))

        pending = {
            'register_type': 'client',
            'phone': phone_e164,
            'username': phone_e164,
            'email': vd.get('email') or '',
            'first_name': vd.get('first_name') or '',
            'last_name': vd.get('last_name') or '',
            'role': 'client',
            'password_hash': make_password(vd['password']) if vd.get('password') else None,
            'otp_id': otp_id,
            'exp_sec': expiry_seconds,
            'exp_ts': (timezone.now() + timedelta(seconds=expiry_seconds)).timestamp(),
        }
        token = _build_pending_token(pending)
        write_auth_event('OTP_SENT', request, phone_e164=phone_e164, success=True, metadata={'otp_id': otp_id})
        return Response({'requires_otp': True, 'pending_token': token}, status=status.HTTP_201_CREATED)


class RegisterProviderView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'otp_request'

    def post(self, request):
        serializer = ProviderRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data
        phone_e164 = vd['phone']
        username = vd['login']

        if (
            User.objects.filter(phone=phone_e164).exists()
            or User.objects.filter(username__iexact=username).exists()
            or (vd.get('email') and User.objects.filter(email__iexact=vd['email']).exists())
        ):
            _register_backoff('register', request.META.get('REMOTE_ADDR', ''))
            _jitter_sleep()
            return Response({'requires_otp': False, 'detail': 'Si éligible, un OTP a été envoyé'}, status=status.HTTP_200_OK)

        d7 = D7VerifyClient()
        try:
            otp_payload = d7.send_otp(
                phone_e164,
                expiry=settings.OTP_EXPIRY_MINUTES * 60,
                otp_code_length=settings.OTP_LENGTH,
            )
        except D7VerifyError:
            write_auth_event('OTP_PROVIDER_ERROR', request, phone_e164=phone_e164, success=False)
            return Response({'detail': 'Service OTP indisponible, réessayez plus tard'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        otp_id = otp_payload.get('otp_id') or otp_payload.get('request_id')
        expiry_seconds = int(otp_payload.get('expiry', settings.OTP_EXPIRY_MINUTES * 60))

        first_name, last_name = _split_name(vd['name'])
        provider_payload = {
            'company_name': vd['company_name'],
            'service_type': vd['service_type'],
            'city': vd['city'],
        }

        pending = {
            'register_type': 'provider',
            'phone': phone_e164,
            'username': username,
            'email': vd.get('email') or '',
            'first_name': first_name,
            'last_name': last_name,
            'role': 'provider_owner',
            'password_hash': make_password(vd['password']),
            'provider': provider_payload,
            'otp_id': otp_id,
            'exp_sec': expiry_seconds,
            'exp_ts': (timezone.now() + timedelta(seconds=expiry_seconds)).timestamp(),
        }

        token = _build_pending_token(pending)
        write_auth_event('OTP_SENT', request, phone_e164=phone_e164, success=True, metadata={'otp_id': otp_id})
        return Response({'requires_otp': True, 'pending_token': token}, status=status.HTTP_201_CREATED)


class OTPRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'otp_request'

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pending = _read_pending_token(serializer.validated_data['pending_token'])
        otp_id = pending.get('otp_id')

        d7 = D7VerifyClient()
        try:
            if otp_id:
                d7.resend_otp(otp_id)
            else:
                data = d7.send_otp(pending['phone'])
                pending['otp_id'] = data.get('otp_id') or data.get('request_id')
        except D7VerifyError:
            write_auth_event('OTP_PROVIDER_ERROR', request, phone_e164=pending.get('phone'), success=False)
            return Response({'detail': 'Service OTP indisponible, réessayez plus tard'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        write_auth_event('OTP_SENT', request, phone_e164=pending.get('phone'), success=True, metadata={'otp_id': pending.get('otp_id')})
        token = _build_pending_token(pending)
        return Response({'detail': 'OTP envoyé', 'pending_token': token}, status=status.HTTP_200_OK)


class OTPVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'otp_verify'

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pending = _read_pending_token(serializer.validated_data['pending_token'])
        otp_id = serializer.validated_data.get('otp_id') or pending.get('otp_id')
        if not otp_id:
            return Response({'detail': 'OTP non initialisé'}, status=status.HTTP_400_BAD_REQUEST)

        d7 = D7VerifyClient()
        try:
            result = d7.verify_otp(otp_id, serializer.validated_data['code'])
        except D7VerifyError:
            write_auth_event('OTP_PROVIDER_ERROR', request, phone_e164=pending.get('phone'), success=False)
            return Response({'detail': 'Service OTP indisponible, réessayez plus tard'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        status_str = str(result.get('status', '')).upper()
        if status_str not in {'APPROVED', 'ALREADY_VERIFIED'}:
            write_auth_event('OTP_VERIFY_FAIL', request, phone_e164=pending.get('phone'), success=False)
            return Response({'detail': f'OTP {status_str or "FAILED"}'}, status=status.HTTP_400_BAD_REQUEST)

        phone_e164 = pending.get('phone')
        if User.objects.filter(phone=phone_e164).exists():
            return Response({'detail': 'Compte déjà existant'}, status=status.HTTP_409_CONFLICT)

        register_type = pending.get('register_type', 'client')

        user = User(
            username=pending.get('username') or phone_e164,
            email=pending.get('email') or '',
            phone=phone_e164,
            first_name=pending.get('first_name') or '',
            last_name=pending.get('last_name') or '',
            role=pending.get('role') or '',
        )

        password_hash = pending.get('password_hash')
        if password_hash:
            user.password = password_hash
        else:
            user.set_unusable_password()

        user.save()
        user.mark_phone_verified()

        if register_type == 'provider':
            _bootstrap_provider_account(user, pending.get('provider') or {})

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        response = Response({'access': access, 'user': UserProfileSerializer(user).data}, status=status.HTTP_200_OK)
        set_refresh_cookie(response, str(refresh))
        write_auth_event('OTP_VERIFY_OK', request, user=user, phone_e164=phone_e164, success=True)
        return response


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'auth_login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data['identifier']
        password = serializer.validated_data['password']
        normalized = normalize_to_e164(identifier)
        lock_key = normalized or identifier.lower()

        if _login_is_locked(lock_key):
            return Response({'detail': 'Trop de tentatives. Réessayez plus tard.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        user = authenticate(request, username=identifier, password=password)
        if not user:
            _register_login_failure(lock_key)
            write_auth_event('LOGIN_FAIL', request, phone_e164=normalized if normalized else None, success=False)
            _jitter_sleep()
            return Response({'detail': 'Identifiants invalides'}, status=status.HTTP_401_UNAUTHORIZED)

        _reset_login_failures(lock_key)
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        response = Response({'access': access, 'user': UserProfileSerializer(user).data}, status=status.HTTP_200_OK)
        set_refresh_cookie(response, str(refresh))
        write_auth_event('LOGIN_SUCCESS', request, user=user, phone_e164=user.phone, success=True)
        return response


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'auth_refresh'

    def post(self, request):
        if not _is_same_site_request(request):
            return Response({'detail': 'Origine non autorisée'}, status=status.HTTP_403_FORBIDDEN)
        token = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not token:
            return Response({'detail': 'Refresh token manquant'}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            refresh = RefreshToken(token)
            user = User.objects.get(id=refresh.get('user_id'))
        except Exception:
            return Response({'detail': 'Refresh token invalide'}, status=status.HTTP_401_UNAUTHORIZED)

        access = str(refresh.access_token)
        if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False):
            try:
                if settings.SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION', False):
                    refresh.blacklist()  # type: ignore[attr-defined]
            except Exception:
                pass
            new_refresh = RefreshToken.for_user(user)
            response = Response({'access': access}, status=status.HTTP_200_OK)
            set_refresh_cookie(response, str(new_refresh))
        else:
            response = Response({'access': access}, status=status.HTTP_200_OK)
        write_auth_event('TOKEN_REFRESH', request, user=user, success=True)
        return response


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'auth_logout'

    def post(self, request):
        if not _is_same_site_request(request):
            return Response({'detail': 'Origine non autorisée'}, status=status.HTTP_403_FORBIDDEN)
        try:
            for token in OutstandingToken.objects.filter(user=request.user):
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            pass
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        write_auth_event('LOGOUT', request, user=request.user, success=True)
        return response


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'password_reset_request'

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            _register_backoff('reset', request.META.get('REMOTE_ADDR', ''))
            _jitter_sleep()
            return Response({'detail': 'OTP envoyé'}, status=status.HTTP_200_OK)

        d7 = D7VerifyClient()
        try:
            payload = d7.send_otp(phone)
        except D7VerifyError:
            write_auth_event('OTP_PROVIDER_ERROR', request, phone_e164=phone, success=False)
            return Response({'detail': 'Service OTP indisponible, réessayez plus tard'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        otp_id = payload.get('otp_id') or payload.get('request_id')
        expiry_seconds = int(payload.get('expiry', settings.OTP_EXPIRY_MINUTES * 60))
        reset_token = _build_reset_token({
            'phone': phone,
            'otp_id': otp_id,
            'exp_ts': (timezone.now() + timedelta(seconds=expiry_seconds)).timestamp(),
        })
        write_auth_event('RESET_REQUEST', request, user=user, phone_e164=phone, success=True, metadata={'otp_id': otp_id})
        return Response({'reset_token': reset_token, 'detail': 'OTP envoyé'}, status=status.HTTP_200_OK)


class PasswordResetVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'password_reset_verify'

    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            reset = _read_reset_token(serializer.validated_data['reset_token'])
        except signing.BadSignature:
            return Response({'detail': 'Jeton invalide ou expiré'}, status=status.HTTP_400_BAD_REQUEST)

        otp_id = reset.get('otp_id')
        if not otp_id:
            return Response({'detail': 'OTP non initialisé'}, status=status.HTTP_400_BAD_REQUEST)

        d7 = D7VerifyClient()
        try:
            result = d7.verify_otp(otp_id, serializer.validated_data['code'])
        except D7VerifyError:
            write_auth_event('OTP_PROVIDER_ERROR', request, phone_e164=reset.get('phone'), success=False)
            return Response({'detail': 'Service OTP indisponible, réessayez plus tard'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        status_str = str(result.get('status', '')).upper()
        if status_str not in {'APPROVED', 'ALREADY_VERIFIED'}:
            write_auth_event('RESET_VERIFY_FAIL', request, phone_e164=reset.get('phone'), success=False)
            return Response({'detail': f'OTP {status_str or "FAILED"}'}, status=status.HTTP_400_BAD_REQUEST)

        session_token = _build_reset_session_token({
            'phone': reset.get('phone'),
            'exp_ts': (timezone.now() + timedelta(minutes=10)).timestamp(),
        })
        write_auth_event('RESET_VERIFY_OK', request, phone_e164=reset.get('phone'), success=True)
        return Response({'reset_session_token': session_token}, status=status.HTTP_200_OK)


class PasswordResetFinalizeView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'password_reset_finalize'

    def post(self, request):
        serializer = PasswordResetFinalizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            session = _read_reset_session_token(serializer.validated_data['reset_session_token'])
        except signing.BadSignature:
            return Response({'detail': 'Session de réinitialisation invalide ou expirée'}, status=status.HTTP_400_BAD_REQUEST)

        phone = session.get('phone')
        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return Response({'detail': 'Utilisateur introuvable'}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        write_auth_event('RESET_FINALIZE_OK', request, user=user, phone_e164=phone, success=True)
        return Response({'detail': 'Mot de passe mis à jour'}, status=status.HTTP_200_OK)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Profil mis à jour avec succès', 'user': serializer.data})


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        write_auth_event('PASSWORD_CHANGE', request, user=request.user, phone_e164=request.user.phone, success=True)
        return Response({'message': 'Mot de passe changé avec succès'}, status=status.HTTP_200_OK)