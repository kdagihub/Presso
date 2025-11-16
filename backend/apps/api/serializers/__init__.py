# Serializers Presso API
# Tous les serializers sont organisés par module

from .auth import (
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

__all__ = [
    'ClientRegisterSerializer',
    'ProviderRegisterSerializer',
    'LoginSerializer',
    'OTPRequestSerializer',
    'OTPVerifySerializer',
    'PasswordResetRequestSerializer',
    'PasswordResetVerifySerializer',
    'PasswordResetFinalizeSerializer',
    'UserProfileSerializer',
    'PasswordChangeSerializer',
]

