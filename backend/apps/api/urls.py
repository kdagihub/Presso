"""
URLs de l'API REST Presso
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenVerifyView

from apps.api.viewsets.auth import (
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
from apps.api.viewsets.webhooks import (
    orange_delivery_receipt,
    orange_mobile_originated,
    webhook_health,
)

urlpatterns = [
    # =====================================================================
    # AUTHENTIFICATION & OTP
    # =====================================================================
    path('auth/register/client/', RegisterClientView.as_view(), name='auth-register-client'),
    path('auth/register/provider/', RegisterProviderView.as_view(), name='auth-register-provider'),
    path('auth/otp/request/', OTPRequestView.as_view(), name='auth-otp-request'),
    path('auth/otp/verify/', OTPVerifyView.as_view(), name='auth-otp-verify'),
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/profile/', ProfileView.as_view(), name='auth-profile'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('auth/password/reset/', PasswordResetRequestView.as_view(), name='auth-password-reset'),
    path('auth/password/reset/verify/', PasswordResetVerifyView.as_view(), name='auth-password-reset-verify'),
    path('auth/password/reset/finalize/', PasswordResetFinalizeView.as_view(), name='auth-password-reset-finalize'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # =====================================================================
    # WEBHOOKS ORANGE SMS
    # =====================================================================
    path('webhooks/orange/dr/', orange_delivery_receipt, name='orange_delivery_receipt'),
    path('webhooks/orange/mo/', orange_mobile_originated, name='orange_mobile_originated'),
    path('webhooks/health/', webhook_health, name='webhook_health'),
]