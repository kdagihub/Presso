# ViewSets Presso API
# Tous les viewsets sont organisés par module

from .auth import (
    RegisterClientView,
    RegisterProviderView,
    OTPRequestView,
    OTPVerifyView,
    LoginView,
    RefreshView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    PasswordResetFinalizeView,
    ProfileView,
    ChangePasswordView,
)
from .providers import (
    ProviderAgencyListCreateView,
    ProviderAgencyDetailView,
    ProviderStaffListView,
    ProviderStaffInviteView,
    ProviderStaffDetailView,
    ProviderStaffActivateView,
)

__all__ = [
    'RegisterClientView',
    'RegisterProviderView',
    'OTPRequestView',
    'OTPVerifyView',
    'LoginView',
    'RefreshView',
    'LogoutView',
    'PasswordResetRequestView',
    'PasswordResetVerifyView',
    'PasswordResetFinalizeView',
    'ProfileView',
    'ChangePasswordView',
    'ProviderAgencyListCreateView',
    'ProviderAgencyDetailView',
    'ProviderStaffListView',
    'ProviderStaffInviteView',
    'ProviderStaffDetailView',
    'ProviderStaffActivateView',
]

