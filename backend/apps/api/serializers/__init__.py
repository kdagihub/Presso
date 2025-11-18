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
from .providers import (
    ProviderAgencySerializer,
    ProviderAgencyWriteSerializer,
    ProviderStaffSerializer,
    ProviderStaffInviteSerializer,
    ProviderStaffUpdateSerializer,
    ProviderStaffActivateSerializer,
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
    'ProviderAgencySerializer',
    'ProviderAgencyWriteSerializer',
    'ProviderStaffSerializer',
    'ProviderStaffInviteSerializer',
    'ProviderStaffUpdateSerializer',
    'ProviderStaffActivateSerializer',
]

