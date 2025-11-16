"""
Webhooks pour Orange SMS API (Delivery Receipts & MO)
"""
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

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
        'service': 'Orange SMS Webhooks',
        'endpoints': {
            'delivery_receipt': '/api/webhooks/orange/dr/',
            'mobile_originated': '/api/webhooks/orange/mo/',
        }
    })

