"""
Webhooks pour :
- Orange SMS API (Delivery Receipts & MO)
- Moneroo (Paiements et Payouts)
- Endpoints de simulation pour le développement
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

from apps.core.services import MonerooService

logger = logging.getLogger(__name__)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def orange_delivery_receipt(request):
    """
    Webhook pour recevoir les delivery receipts d'Orange SMS API
    
    Orange POSTera ici les statuts de livraison :
    - DeliveredToTerminal : SMS délivré avec succès
    - DeliveryImpossible : Échec de livraison
    - etc.
    """
    try:
        data = request.data
        
        # Logger tout ce qu'on reçoit
        logger.info(f"📬 Orange Delivery Receipt received: {data}")
        
        # Format attendu (GSMA OneAPI) :
        # {
        #   "deliveryInfoNotification": {
        #     "deliveryInfo": {
        #       "address": "tel:+225XXXXXXXXXX",
        #       "deliveryStatus": "DeliveredToTerminal" | "DeliveryImpossible" | ...,
        #     },
        #     "callbackData": "otp" | "tag",
        #     "link": [{
        #       "rel": "OutboundSMSMessageRequest",
        #       "href": "..."
        #     }]
        #   }
        # }
        
        notification = data.get('deliveryInfoNotification', {})
        delivery_info = notification.get('deliveryInfo', {})
        
        address = delivery_info.get('address', 'unknown')
        delivery_status = delivery_info.get('deliveryStatus', 'unknown')
        callback_data = notification.get('callbackData', '')
        
        # Logger le statut
        if delivery_status == 'DeliveredToTerminal':
            logger.info(f"✅ SMS delivered successfully to {address} (tag: {callback_data})")
        elif delivery_status == 'DeliveryImpossible':
            logger.error(f"❌ SMS delivery failed to {address} (tag: {callback_data})")
        else:
            logger.warning(f"⚠️  SMS status '{delivery_status}' for {address} (tag: {callback_data})")
        
        # TODO: Mettre à jour une table de tracking des SMS si nécessaire
        # SMSLog.objects.filter(phone=address, tag=callback_data).update(status=delivery_status)
        
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error processing Orange DR: {e}", exc_info=True)
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def orange_mobile_originated(request):
    """
    Webhook pour recevoir les SMS entrants (MO - Mobile Originated)
    
    Utile si vous utilisez un numéro bi-directionnel et que les utilisateurs
    peuvent répondre par SMS.
    """
    try:
        data = request.data
        logger.info(f"📱 Orange MO (incoming SMS) received: {data}")
        
        # TODO: Traiter les SMS entrants si nécessaire
        # Par exemple : répondre automatiquement, valider des codes, etc.
        
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error processing Orange MO: {e}", exc_info=True)
        return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def webhook_health(request):
    """
    Endpoint de santé pour vérifier que les webhooks sont accessibles
    """
    return Response({
        'status': 'ok',
        'service': 'Webhooks Service',
        'simulation_mode': MonerooService.is_simulation_mode(),
        'endpoints': {
            'orange': {
                'delivery_receipt': '/api/webhooks/orange/dr/',
                'mobile_originated': '/api/webhooks/orange/mo/',
            },
            'moneroo': {
                'webhook': '/api/webhooks/moneroo/',
            },
            'simulation': {
                'confirm_payment': '/api/simulation/payment/<tx_id>/confirm/',
                'fail_payment': '/api/simulation/payment/<tx_id>/fail/',
                'transactions': '/api/simulation/transactions/',
            }
        }
    })


# ═══════════════════════════════════════════════════════════════════════════════
# MONEROO WEBHOOKS
# ═══════════════════════════════════════════════════════════════════════════════

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def moneroo_webhook(request):
    """
    Webhook principal pour recevoir les événements Moneroo.
    
    Types d'événements:
    - payment.success : Paiement réussi
    - payment.failed : Paiement échoué
    - payout.success : Virement réussi
    - payout.failed : Virement échoué
    """
    try:
        # Vérifier la signature (si configurée)
        signature = request.headers.get('X-Moneroo-Signature', '')
        if signature:
            is_valid = MonerooService.verify_webhook_signature(
                request.body,
                signature
            )
            if not is_valid:
                logger.warning("Signature de webhook Moneroo invalide")
                return Response(
                    {'error': 'Invalid signature'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        data = request.data
        event_type = data.get('event', data.get('type', ''))
        event_data = data.get('data', data)
        
        logger.info(f"📥 Webhook Moneroo reçu: {event_type}")
        logger.debug(f"Données: {data}")
        
        # Traiter l'événement
        result = MonerooService.process_webhook(event_type, event_data)
        
        return Response({
            'status': 'ok',
            'handled': result.get('handled', False),
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Erreur traitement webhook Moneroo: {e}", exc_info=True)
        return Response(
            {'status': 'error', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SIMULATION ENDPOINTS (pour le développement)
# ═══════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])  # AllowAny car utilisé uniquement en dev
def simulation_confirm_payment(request, transaction_id):
    """
    [SIMULATION] Confirme un paiement comme si le client avait payé.
    
    Utile pour tester le flux complet sans interface de paiement.
    Uniquement disponible en mode simulation.
    """
    if not MonerooService.is_simulation_mode():
        return Response(
            {'error': 'Simulation non disponible en mode production'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    result = MonerooService.simulate_payment_success(transaction_id)
    
    if result.get('success'):
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def simulation_fail_payment(request, transaction_id):
    """
    [SIMULATION] Simule l'échec d'un paiement.
    """
    if not MonerooService.is_simulation_mode():
        return Response(
            {'error': 'Simulation non disponible en mode production'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    reason = request.data.get('reason', 'Solde insuffisant')
    result = MonerooService.simulate_payment_failure(transaction_id, reason)
    
    if result.get('success'):
        return Response(result, status=status.HTTP_200_OK)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def simulation_get_transaction(request, transaction_id):
    """
    [SIMULATION] Récupère les détails d'une transaction simulée.
    """
    if not MonerooService.is_simulation_mode():
        return Response(
            {'error': 'Simulation non disponible en mode production'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    tx = MonerooService.get_mock_transaction(transaction_id)
    
    if tx:
        return Response(tx, status=status.HTTP_200_OK)
    else:
        return Response(
            {'error': 'Transaction non trouvée'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET', 'DELETE'])
@permission_classes([AllowAny])
def simulation_transactions(request):
    """
    [SIMULATION] Liste ou efface les transactions simulées.
    
    GET: Liste toutes les transactions simulées
    DELETE: Efface toutes les transactions simulées
    """
    if not MonerooService.is_simulation_mode():
        return Response(
            {'error': 'Simulation non disponible en mode production'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    if request.method == 'DELETE':
        count = MonerooService.clear_mock_transactions()
        return Response({
            'success': True,
            'cleared': count,
            'message': f'{count} transaction(s) effacée(s)',
        })
    
    # GET
    tx_type = request.query_params.get('type')  # 'payment' ou 'payout'
    transactions = MonerooService.list_mock_transactions(tx_type)
    
    return Response({
        'simulation_mode': True,
        'count': len(transactions),
        'transactions': transactions,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def simulation_status(request):
    """
    [SIMULATION] Vérifie le statut du mode simulation.
    """
    is_simulation = MonerooService.is_simulation_mode()
    config = MonerooService.get_api_config()
    
    return Response({
        'simulation_mode': is_simulation,
        'sandbox_mode': config.get('sandbox_mode', True),
        'api_configured': bool(config.get('api_key')),
        'message': (
            'Mode simulation actif - Les paiements sont simulés localement'
            if is_simulation else
            'Mode production - Connecté à Moneroo'
        ),
        'endpoints': {
            'confirm_payment': '/api/simulation/payment/{transaction_id}/confirm/',
            'fail_payment': '/api/simulation/payment/{transaction_id}/fail/',
            'get_transaction': '/api/simulation/payment/{transaction_id}/',
            'list_transactions': '/api/simulation/transactions/',
        } if is_simulation else None,
    })

