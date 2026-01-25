"""
Services métier pour l'application core.

ARCHITECTURE:
=============
- PaymentGatewayService : Service unifié pour les paiements (CinetPay, simulation)
- WalletService : Gestion des portefeuilles prestataires
- DeliveryOTPService : Génération/validation des codes OTP de livraison
- PayoutService : Gestion des virements automatiques
- MonerooService : [Legacy] Service Moneroo original
"""
from apps.core.services.wallet import WalletService
from apps.core.services.delivery_otp import DeliveryOTPService
from apps.core.services.payout import PayoutService
from apps.core.services.moneroo import MonerooService
from apps.core.services.payment_gateway import PaymentGatewayService

__all__ = [
    'PaymentGatewayService',
    'WalletService',
    'DeliveryOTPService',
    'PayoutService',
    'MonerooService',
]
