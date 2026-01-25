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
from .orders import (
    OrderListCreateView,
    OrderDetailView,
    ProviderOrderListView,
    ProviderOrderDetailView,
    ProviderOrderStatusUpdateView,
    ProviderOrderAssignView,
    # Vérification à la collecte
    CollectorVerifyQuantityView,
    CollectorConfirmCollectionView,
    # Réponse client à l'ajustement
    ClientAdjustmentStatusView,
    ClientCompleteAdjustmentView,
    ClientAcceptReductionView,
    # Réclamation client
    ClientClaimStatusView,
    ClientSubmitClaimView,
    # Portefeuille client
    ClientWalletView,
)
from .onboarding import (
    OnboardingStatusView,
    OnboardingIdentityView,
    OnboardingServicesView,
    OnboardingPayoutView,
    OnboardingCompleteView,
    ProviderOpenStatusView,
    ProviderPayoutAccountListCreateView,
    ProviderPayoutAccountDetailView,
)
from .wallet import (
    WalletSummaryView,
    WalletTransactionsView,
    PayoutRequestView,
    PayoutHistoryView,
    PayoutCancelView,
)
from .dashboard import (
    DashboardSummaryView,
    DashboardStatsView,
    ShareLinkView,
)
from .delivery import (
    GenerateDeliveryOTPView,
    ValidateDeliveryOTPView,
    RegenerateDeliveryOTPView,
    DeliveryOTPStatusView,
    ClientDeliveryOTPView,
)
from .notifications import (
    FCMTokenRegisterView,
    FCMTokenUnregisterView,
    FCMDeviceListView,
    FCMDeviceDeleteView,
    FCMTestNotificationView,
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
    'ProviderSettingsView',
    'ProviderServiceListCreateView',
    'ProviderServiceDetailView',
    'ProviderArticleTypeListCreateView',
    'ProviderArticleTypeDetailView',
    'ProviderMatiereListCreateView',
    'ProviderMatiereDetailView',
    'ProviderTariffListCreateView',
    'ProviderTariffDetailView',
    'CatalogProviderServicesPublicView',
    'CatalogProviderServiceDetailView',
    'OrderListCreateView',
    'OrderDetailView',
    'ProviderOrderListView',
    'ProviderOrderDetailView',
    'ProviderOrderStatusUpdateView',
    'ProviderOrderAssignView',
    # Vérification à la collecte
    'CollectorVerifyQuantityView',
    'CollectorConfirmCollectionView',
    # Réponse client à l'ajustement
    'ClientAdjustmentStatusView',
    'ClientCompleteAdjustmentView',
    'ClientAcceptReductionView',
    # Réclamation client
    'ClientClaimStatusView',
    'ClientSubmitClaimView',
    # Portefeuille client
    'ClientWalletView',
    # Onboarding
    'OnboardingStatusView',
    'OnboardingIdentityView',
    'OnboardingServicesView',
    'OnboardingPayoutView',
    'OnboardingCompleteView',
    'ProviderOpenStatusView',
    'ProviderPayoutAccountListCreateView',
    'ProviderPayoutAccountDetailView',
    # Wallet
    'WalletSummaryView',
    'WalletTransactionsView',
    'PayoutRequestView',
    'PayoutHistoryView',
    'PayoutCancelView',
    # Dashboard
    'DashboardSummaryView',
    'DashboardStatsView',
    'ShareLinkView',
    # Delivery OTP
    'GenerateDeliveryOTPView',
    'ValidateDeliveryOTPView',
    'RegenerateDeliveryOTPView',
    'DeliveryOTPStatusView',
    'ClientDeliveryOTPView',
    # Notifications FCM
    'FCMTokenRegisterView',
    'FCMTokenUnregisterView',
    'FCMDeviceListView',
    'FCMDeviceDeleteView',
    'FCMTestNotificationView',
]

