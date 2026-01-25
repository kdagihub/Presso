"""
Viewsets pour la gestion des portefeuilles prestataires.
"""
from decimal import Decimal
from rest_framework import status, permissions  # type: ignore
from rest_framework.views import APIView  # type: ignore
from rest_framework.response import Response  # type: ignore

from apps.api.viewsets.providers import require_provider_member, IsProviderMember
from apps.core.services import WalletService, PayoutService


class WalletSummaryView(APIView):
    """
    GET /api/provider/wallet/
    
    Retourne le résumé du portefeuille du prestataire.
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def get(self, request):
        provider, _ = require_provider_member(request)
        
        summary = WalletService.get_wallet_summary(provider)
        
        # Ajouter les infos du compte de payout principal
        from apps.core.models import ProviderPayoutAccount
        payout_account = ProviderPayoutAccount.objects.filter(
            provider=provider,
            is_primary=True
        ).first()
        
        if payout_account:
            summary['payout_account'] = {
                'id': str(payout_account.id),
                'operator': payout_account.operator,
                'operator_display': payout_account.get_operator_display(),
                'phone_number': payout_account.phone_number,
                'account_name': payout_account.account_name,
                'status': payout_account.status,
            }
        else:
            summary['payout_account'] = None
        
        return Response(summary, status=status.HTTP_200_OK)


class WalletTransactionsView(APIView):
    """
    GET /api/provider/wallet/transactions/
    
    Retourne l'historique des transactions du portefeuille.
    
    Query params:
    - limit: Nombre max (défaut: 50)
    - offset: Décalage (défaut: 0)
    - type: Filtrer par type (order_payment, commission, payout, refund, etc.)
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def get(self, request):
        provider, _ = require_provider_member(request)
        
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        transaction_type = request.query_params.get('type')
        
        # Limites de sécurité
        limit = min(limit, 100)
        
        history = WalletService.get_transaction_history(
            provider=provider,
            limit=limit,
            offset=offset,
            transaction_type=transaction_type
        )
        
        return Response(history, status=status.HTTP_200_OK)


class PayoutRequestView(APIView):
    """
    POST /api/provider/wallet/payout/
    
    Demande un retrait manuel vers Mobile Money.
    
    Body:
    - amount: Montant à retirer (optionnel, si absent = tout le solde)
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def post(self, request):
        provider, _ = require_provider_member(request)
        
        # Récupérer le montant (optionnel)
        amount = request.data.get('amount')
        if amount:
            try:
                amount = Decimal(str(amount))
            except (ValueError, TypeError):
                return Response(
                    {'detail': 'Montant invalide.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            payout_request, message = PayoutService.create_manual_payout_request(
                provider=provider,
                amount=amount
            )
            
            return Response({
                'success': True,
                'message': message,
                'payout_request': {
                    'id': str(payout_request.id),
                    'reference': payout_request.reference,
                    'amount': payout_request.amount,
                    'fee': payout_request.fee,
                    'net_amount': payout_request.net_amount,
                    'status': payout_request.status,
                    'scheduled_at': payout_request.scheduled_at,
                }
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'detail': f'Erreur lors de la demande de retrait: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PayoutHistoryView(APIView):
    """
    GET /api/provider/wallet/payouts/
    
    Retourne l'historique des retraits.
    
    Query params:
    - limit: Nombre max (défaut: 50)
    - offset: Décalage (défaut: 0)
    - status: Filtrer par statut (pending, completed, failed, etc.)
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def get(self, request):
        provider, _ = require_provider_member(request)
        
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        payout_status = request.query_params.get('status')
        
        limit = min(limit, 100)
        
        history = PayoutService.get_payout_history(
            provider=provider,
            limit=limit,
            offset=offset,
            status=payout_status
        )
        
        return Response(history, status=status.HTTP_200_OK)


class PayoutCancelView(APIView):
    """
    POST /api/provider/wallet/payouts/<payout_id>/cancel/
    
    Annule une demande de retrait (si pas encore traitée).
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def post(self, request, payout_id):
        provider, _ = require_provider_member(request)
        
        from apps.core.models import PayoutRequest
        
        try:
            payout_request = PayoutRequest.objects.get(
                id=payout_id,
                wallet__provider=provider
            )
        except PayoutRequest.DoesNotExist:
            return Response(
                {'detail': 'Demande de retrait introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        reason = request.data.get('reason', '')
        
        success = PayoutService.cancel_payout_request(payout_request, reason)
        
        if success:
            return Response({
                'success': True,
                'message': 'Demande de retrait annulée.'
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'detail': 'Impossible d\'annuler cette demande (déjà traitée).'},
                status=status.HTTP_400_BAD_REQUEST
            )
