"""
Viewsets pour la gestion des livraisons et OTP.
"""
from rest_framework import status, permissions  # type: ignore
from rest_framework.views import APIView  # type: ignore
from rest_framework.response import Response  # type: ignore

from apps.api.viewsets.providers import require_provider_member, IsProviderMember
from apps.core.services import DeliveryOTPService
from apps.orders.models import Order


class GenerateDeliveryOTPView(APIView):
    """
    POST /api/provider/orders/<order_id>/generate-otp/
    
    Génère un nouveau code OTP de livraison pour une commande.
    L'OTP est envoyé au client par SMS/WhatsApp.
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def post(self, request, order_id):
        provider, _ = require_provider_member(request)
        
        try:
            order = Order.objects.get(
                id=order_id,
                provider=provider
            )
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Commande introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier que la commande est dans un état approprié
        if order.statut not in ['collected', 'in_progress', 'ready']:
            return Response(
                {'detail': f'Impossible de générer un OTP pour une commande {order.get_statut_display()}.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier si déjà livrée
        if order.delivery_otp_validated_at:
            return Response(
                {'detail': 'Cette commande a déjà été livrée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Générer l'OTP
        otp_code = DeliveryOTPService.generate_otp(order, send_notification=True)
        
        return Response({
            'success': True,
            'message': 'Code OTP généré et envoyé au client.',
            'otp_status': DeliveryOTPService.get_otp_status(order),
            # Note: On ne renvoie PAS le code OTP au prestataire
            # C'est le client qui doit le donner au livreur
        }, status=status.HTTP_200_OK)


class ValidateDeliveryOTPView(APIView):
    """
    POST /api/provider/orders/<order_id>/validate-otp/
    
    Valide le code OTP de livraison.
    Déclenche le workflow de paiement automatique.
    
    Body:
    - code: Le code OTP à 6 chiffres
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def post(self, request, order_id):
        provider, _ = require_provider_member(request)
        
        try:
            order = Order.objects.get(
                id=order_id,
                provider=provider
            )
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Commande introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Récupérer le code
        code = request.data.get('code', '').strip()
        
        if not code:
            return Response(
                {'detail': 'Le code OTP est requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(code) != 6 or not code.isdigit():
            return Response(
                {'detail': 'Le code OTP doit être composé de 6 chiffres.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Valider l'OTP
        success, message = DeliveryOTPService.validate_otp(
            order=order,
            code=code,
            validated_by=request.user
        )
        
        if success:
            # Recharger la commande pour avoir les données à jour
            order.refresh_from_db()
            
            return Response({
                'success': True,
                'message': message,
                'order': {
                    'id': str(order.id),
                    'numero': order.numero,
                    'statut': order.statut,
                    'statut_display': order.get_statut_display(),
                    'date_livraison': order.date_livraison,
                    'provider_net_amount': order.provider_net_amount,
                    'payout_status': order.payout_status,
                    'payout_scheduled_at': order.payout_scheduled_at,
                },
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'detail': message},
                status=status.HTTP_400_BAD_REQUEST
            )


class RegenerateDeliveryOTPView(APIView):
    """
    POST /api/provider/orders/<order_id>/regenerate-otp/
    
    Régénère un nouveau code OTP (si expiré ou perdu).
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def post(self, request, order_id):
        provider, _ = require_provider_member(request)
        
        try:
            order = Order.objects.get(
                id=order_id,
                provider=provider
            )
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Commande introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        otp_code, message = DeliveryOTPService.regenerate_otp(order)
        
        if otp_code:
            return Response({
                'success': True,
                'message': message,
                'otp_status': DeliveryOTPService.get_otp_status(order),
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'detail': message},
                status=status.HTTP_400_BAD_REQUEST
            )


class DeliveryOTPStatusView(APIView):
    """
    GET /api/provider/orders/<order_id>/otp-status/
    
    Retourne le statut de l'OTP de livraison.
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def get(self, request, order_id):
        provider, _ = require_provider_member(request)
        
        try:
            order = Order.objects.get(
                id=order_id,
                provider=provider
            )
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Commande introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'order_id': str(order.id),
            'order_numero': order.numero,
            'order_statut': order.statut,
            'otp_status': DeliveryOTPService.get_otp_status(order),
        }, status=status.HTTP_200_OK)


class ClientDeliveryOTPView(APIView):
    """
    GET /api/orders/<order_id>/delivery-code/
    
    Endpoint pour le CLIENT pour voir son code OTP de livraison.
    Le client doit être authentifié et propriétaire de la commande.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, order_id):
        try:
            order = Order.objects.get(
                id=order_id,
                client=request.user
            )
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Commande introuvable.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier que l'OTP a été généré
        if not order.delivery_otp:
            return Response(
                {'detail': 'Aucun code de livraison n\'a été généré pour cette commande.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Vérifier si déjà validé
        if order.delivery_otp_validated_at:
            return Response({
                'message': 'Cette commande a déjà été livrée.',
                'is_validated': True,
                'validated_at': order.delivery_otp_validated_at,
            }, status=status.HTTP_200_OK)
        
        # Vérifier si expiré
        otp_status = DeliveryOTPService.get_otp_status(order)
        
        if otp_status['is_expired']:
            return Response({
                'message': 'Le code de livraison a expiré. Demandez au livreur de régénérer un nouveau code.',
                'is_expired': True,
            }, status=status.HTTP_200_OK)
        
        # Retourner le code au client
        return Response({
            'delivery_code': order.delivery_otp,
            'generated_at': order.delivery_otp_generated_at,
            'validity_minutes': otp_status['validity_minutes'],
            'is_expired': False,
            'message': 'Donnez ce code au livreur pour confirmer la réception de votre linge.',
        }, status=status.HTTP_200_OK)
