"""
URLs de l'API REST Presso
"""
from django.urls import path  # type: ignore
from rest_framework_simplejwt.views import TokenVerifyView  # type: ignore

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
    PasswordResetResendView,
    PasswordResetFinalizeView,
    ProfileView,
    ProfilePhotoView,
    AccountDeactivateView,
    ChangePasswordView,
    PhoneChangeRequestView,
    PhoneChangeConfirmView,
    PhoneChangeResendOTPView,
)
from apps.api.viewsets.providers import (
    ProviderProfileView,
    ProviderPhotoView,
    ProviderAgencyListCreateView,
    ProviderAgencyDetailView,
    ProviderStaffListView,
    ProviderStaffInviteView,
    ProviderStaffDetailView,
    ProviderStaffActivateView,
    ProviderSettingsView,
    ProviderServiceListCreateView,
    ProviderServiceDetailView,
    ProviderArticleTypeListCreateView,
    ProviderArticleTypeDetailView,
    ProviderMatiereListCreateView,
    ProviderMatiereDetailView,
    ProviderTariffListCreateView,
    ProviderTariffDetailView,
    CatalogProviderServicesPublicView,
    CatalogProviderServiceDetailView,
    NearbyProvidersView,
)
from apps.api.viewsets.orders import (
    OrderListCreateView,
    OrderDetailView,
    ProviderOrderListView,
    ProviderOrderDetailView,
    ProviderOrderStatusUpdateView,
    ProviderOrderAssignView,
)
from apps.api.viewsets.webhooks import (
    orange_delivery_receipt,
    orange_mobile_originated,
    webhook_health,
    moneroo_webhook,
    simulation_confirm_payment,
    simulation_fail_payment,
    simulation_get_transaction,
    simulation_transactions,
    simulation_status,
)
from apps.api.viewsets.onboarding import (
    OnboardingStatusView,
    OnboardingIdentityView,
    OnboardingServicesView,
    OnboardingPayoutView,
    OnboardingCompleteView,
    ProviderOpenStatusView,
    ProviderPayoutAccountListCreateView,
    ProviderPayoutAccountDetailView,
)
from apps.api.viewsets.wallet import (
    WalletSummaryView,
    WalletTransactionsView,
    PayoutRequestView,
    PayoutHistoryView,
    PayoutCancelView,
)
from apps.api.viewsets.dashboard import (
    DashboardSummaryView,
    DashboardStatsView,
    ShareLinkView,
)
from apps.api.viewsets.delivery import (
    GenerateDeliveryOTPView,
    ValidateDeliveryOTPView,
    RegenerateDeliveryOTPView,
    DeliveryOTPStatusView,
    ClientDeliveryOTPView,
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
    path('auth/profile/photo/', ProfilePhotoView.as_view(), name='auth-profile-photo'),
    path('auth/deactivate/', AccountDeactivateView.as_view(), name='auth-deactivate'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('auth/password/reset/', PasswordResetRequestView.as_view(), name='auth-password-reset'),
    path('auth/password/reset/verify/', PasswordResetVerifyView.as_view(), name='auth-password-reset-verify'),
    path('auth/password/reset/resend/', PasswordResetResendView.as_view(), name='auth-password-reset-resend'),
    path('auth/password/reset/finalize/', PasswordResetFinalizeView.as_view(), name='auth-password-reset-finalize'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Changement de numéro de téléphone
    path('auth/phone/change/request/', PhoneChangeRequestView.as_view(), name='auth-phone-change-request'),
    path('auth/phone/change/confirm/', PhoneChangeConfirmView.as_view(), name='auth-phone-change-confirm'),
    path('auth/phone/change/resend/', PhoneChangeResendOTPView.as_view(), name='auth-phone-change-resend'),

    # =====================================================================
    # ONBOARDING PRESTATAIRE
    # =====================================================================
    path('provider/onboarding/status/', OnboardingStatusView.as_view(), name='onboarding-status'),
    path('provider/onboarding/identity/', OnboardingIdentityView.as_view(), name='onboarding-identity'),
    path('provider/onboarding/services/', OnboardingServicesView.as_view(), name='onboarding-services'),
    path('provider/onboarding/payout/', OnboardingPayoutView.as_view(), name='onboarding-payout'),
    path('provider/onboarding/complete/', OnboardingCompleteView.as_view(), name='onboarding-complete'),
    path('provider/status/', ProviderOpenStatusView.as_view(), name='provider-open-status'),
    path('provider/payout-accounts/', ProviderPayoutAccountListCreateView.as_view(), name='provider-payout-accounts'),
    path('provider/payout-accounts/<uuid:account_id>/', ProviderPayoutAccountDetailView.as_view(), name='provider-payout-account-detail'),

    # =====================================================================
    # PROVIDER PROFILE (Infos du Provider lui-même)
    # =====================================================================
    path('provider/me/', ProviderProfileView.as_view(), name='provider-profile'),
    path('provider/me/photo/', ProviderPhotoView.as_view(), name='provider-photo'),
    
    # =====================================================================
    # PROVIDER MANAGEMENT
    # =====================================================================
    path('providers/agencies/', ProviderAgencyListCreateView.as_view(), name='provider-agency-list'),
    path('providers/agencies/<uuid:agency_id>/', ProviderAgencyDetailView.as_view(), name='provider-agency-detail'),
    path('providers/staff/', ProviderStaffListView.as_view(), name='provider-staff-list'),
    path('providers/staff/invite/', ProviderStaffInviteView.as_view(), name='provider-staff-invite'),
    path('providers/staff/<uuid:staff_id>/', ProviderStaffDetailView.as_view(), name='provider-staff-detail'),
    path('providers/staff/activate/', ProviderStaffActivateView.as_view(), name='provider-staff-activate'),
    path('providers/settings/', ProviderSettingsView.as_view(), name='provider-settings'),
    path('providers/services/', ProviderServiceListCreateView.as_view(), name='provider-services'),
    path('providers/services/<uuid:service_id>/', ProviderServiceDetailView.as_view(), name='provider-service-detail'),
    path('providers/catalog/article-types/', ProviderArticleTypeListCreateView.as_view(), name='provider-article-types'),
    path('providers/catalog/article-types/<uuid:type_id>/', ProviderArticleTypeDetailView.as_view(), name='provider-article-type-detail'),
    path('providers/catalog/materials/', ProviderMatiereListCreateView.as_view(), name='provider-materials'),
    path('providers/catalog/materials/<uuid:matiere_id>/', ProviderMatiereDetailView.as_view(), name='provider-material-detail'),
    path('providers/tariffs/', ProviderTariffListCreateView.as_view(), name='provider-tariffs'),
    path('providers/tariffs/<uuid:tariff_id>/', ProviderTariffDetailView.as_view(), name='provider-tariff-detail'),
    path('catalog/providers/<uuid:provider_id>/services/', CatalogProviderServicesPublicView.as_view(), name='public-provider-services'),
    path('catalog/providers/<uuid:provider_id>/services/<uuid:offer_id>/details/', CatalogProviderServiceDetailView.as_view(), name='public-provider-service-details'),
    path('catalog/providers/nearby/', NearbyProvidersView.as_view(), name='nearby-providers'),
    path('providers/orders/', ProviderOrderListView.as_view(), name='provider-order-list'),
    path('providers/orders/<uuid:order_id>/', ProviderOrderDetailView.as_view(), name='provider-order-detail'),
    path('providers/orders/<uuid:order_id>/status/', ProviderOrderStatusUpdateView.as_view(), name='provider-order-status'),
    path('providers/orders/<uuid:order_id>/assign/', ProviderOrderAssignView.as_view(), name='provider-order-assign'),

    # =====================================================================
    # DASHBOARD PRESTATAIRE
    # =====================================================================
    path('provider/dashboard/', DashboardSummaryView.as_view(), name='provider-dashboard'),
    path('provider/dashboard/stats/', DashboardStatsView.as_view(), name='provider-dashboard-stats'),
    path('provider/share-link/', ShareLinkView.as_view(), name='provider-share-link'),
    
    # =====================================================================
    # WALLET & PAYOUTS PRESTATAIRE
    # =====================================================================
    path('provider/wallet/', WalletSummaryView.as_view(), name='provider-wallet'),
    path('provider/wallet/transactions/', WalletTransactionsView.as_view(), name='provider-wallet-transactions'),
    path('provider/wallet/payout/', PayoutRequestView.as_view(), name='provider-wallet-payout'),
    path('provider/wallet/payouts/', PayoutHistoryView.as_view(), name='provider-payout-history'),
    path('provider/wallet/payouts/<uuid:payout_id>/cancel/', PayoutCancelView.as_view(), name='provider-payout-cancel'),
    
    # =====================================================================
    # LIVRAISON OTP (Prestataire)
    # =====================================================================
    path('provider/orders/<uuid:order_id>/generate-otp/', GenerateDeliveryOTPView.as_view(), name='provider-order-generate-otp'),
    path('provider/orders/<uuid:order_id>/validate-otp/', ValidateDeliveryOTPView.as_view(), name='provider-order-validate-otp'),
    path('provider/orders/<uuid:order_id>/regenerate-otp/', RegenerateDeliveryOTPView.as_view(), name='provider-order-regenerate-otp'),
    path('provider/orders/<uuid:order_id>/otp-status/', DeliveryOTPStatusView.as_view(), name='provider-order-otp-status'),
    
    # =====================================================================
    # COMMANDES CLIENT
    # =====================================================================
    path('orders/', OrderListCreateView.as_view(), name='client-orders'),
    path('orders/<uuid:order_id>/', OrderDetailView.as_view(), name='client-order-detail'),
    path('orders/<uuid:order_id>/delivery-code/', ClientDeliveryOTPView.as_view(), name='client-order-delivery-code'),
    
    # =====================================================================
    # WEBHOOKS
    # =====================================================================
    # Orange SMS
    path('webhooks/orange/dr/', orange_delivery_receipt, name='orange_delivery_receipt'),
    path('webhooks/orange/mo/', orange_mobile_originated, name='orange_mobile_originated'),
    # Moneroo
    path('webhooks/moneroo/', moneroo_webhook, name='moneroo_webhook'),
    # Health check
    path('webhooks/health/', webhook_health, name='webhook_health'),
    
    # =====================================================================
    # SIMULATION (Développement uniquement)
    # =====================================================================
    path('simulation/status/', simulation_status, name='simulation_status'),
    path('simulation/payment/<str:transaction_id>/', simulation_get_transaction, name='simulation_get_transaction'),
    path('simulation/payment/<str:transaction_id>/confirm/', simulation_confirm_payment, name='simulation_confirm_payment'),
    path('simulation/payment/<str:transaction_id>/fail/', simulation_fail_payment, name='simulation_fail_payment'),
    path('simulation/transactions/', simulation_transactions, name='simulation_transactions'),
]