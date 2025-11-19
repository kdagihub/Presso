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
    PasswordResetFinalizeView,
    ProfileView,
    ChangePasswordView,
)
from apps.api.viewsets.providers import (
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
    path('providers/orders/', ProviderOrderListView.as_view(), name='provider-order-list'),
    path('providers/orders/<uuid:order_id>/', ProviderOrderDetailView.as_view(), name='provider-order-detail'),
    path('providers/orders/<uuid:order_id>/status/', ProviderOrderStatusUpdateView.as_view(), name='provider-order-status'),
    path('providers/orders/<uuid:order_id>/assign/', ProviderOrderAssignView.as_view(), name='provider-order-assign'),

    # =====================================================================
    # COMMANDES CLIENT
    # =====================================================================
    path('orders/', OrderListCreateView.as_view(), name='client-orders'),
    path('orders/<uuid:order_id>/', OrderDetailView.as_view(), name='client-order-detail'),
    
    # =====================================================================
    # WEBHOOKS ORANGE SMS
    # =====================================================================
    path('webhooks/orange/dr/', orange_delivery_receipt, name='orange_delivery_receipt'),
    path('webhooks/orange/mo/', orange_mobile_originated, name='orange_mobile_originated'),
    path('webhooks/health/', webhook_health, name='webhook_health'),
]