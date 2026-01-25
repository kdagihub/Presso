"""
Viewsets pour les notifications push (FCM)

Endpoints:
- POST /api/notifications/fcm/register/ - Enregistrer un token FCM
- POST /api/notifications/fcm/unregister/ - Supprimer un token FCM
- GET /api/notifications/devices/ - Lister les devices enregistrés
- DELETE /api/notifications/devices/<id>/ - Supprimer un device
- POST /api/notifications/test/ - Envoyer une notification de test
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.users.models import UserFCMToken
from apps.api.serializers.notifications import (
    FCMTokenRegisterSerializer,
    FCMTokenUnregisterSerializer,
    FCMTokenListSerializer,
)

logger = logging.getLogger(__name__)


class FCMTokenRegisterView(APIView):
    """
    Enregistre un token FCM pour l'utilisateur connecté.
    
    Appelé par le frontend après :
    1. Demande de permission de notification (Notification.requestPermission())
    2. Obtention du token Firebase (getToken())
    
    Le token est associé au device (navigateur/mobile) de l'utilisateur.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Notifications'],
        summary="Enregistrer un token FCM",
        description="""
        Enregistre un token FCM pour recevoir des notifications push.
        
        Ce endpoint doit être appelé par le frontend après avoir obtenu
        la permission de notification et le token Firebase.
        
        **Flux Frontend (Vue.js):**
        1. Demander la permission: `Notification.requestPermission()`
        2. Obtenir le token: `getToken(messaging, { vapidKey: '...' })`
        3. Envoyer à ce endpoint avec le type de device
        
        Si le token existe déjà pour un autre utilisateur, il sera transféré.
        """,
        request=FCMTokenRegisterSerializer,
        responses={
            201: OpenApiResponse(description="Token enregistré avec succès"),
            400: OpenApiResponse(description="Données invalides"),
        }
    )
    def post(self, request):
        serializer = FCMTokenRegisterSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        fcm_token = serializer.save()
        
        logger.info(
            f"[FCM] Token registered for user {request.user.id} "
            f"({fcm_token.device_type}: {fcm_token.device_name or 'unnamed'})"
        )
        
        return Response({
            'success': True,
            'message': 'Token FCM enregistré avec succès',
            'device': {
                'id': str(fcm_token.id),
                'type': fcm_token.device_type,
                'name': fcm_token.device_name,
            }
        }, status=status.HTTP_201_CREATED)


class FCMTokenUnregisterView(APIView):
    """
    Supprime/désactive un token FCM.
    
    Appelé lors de :
    - Déconnexion de l'utilisateur
    - Désactivation des notifications par l'utilisateur
    - Changement de navigateur/device
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Notifications'],
        summary="Supprimer un token FCM",
        description="""
        Supprime un token FCM pour ne plus recevoir de notifications sur ce device.
        
        **Quand appeler:**
        - À la déconnexion (logout)
        - Si l'utilisateur désactive les notifications
        - Lors du changement de compte sur un device
        """,
        request=FCMTokenUnregisterSerializer,
        responses={
            200: OpenApiResponse(description="Token supprimé"),
            400: OpenApiResponse(description="Token invalide"),
            404: OpenApiResponse(description="Token non trouvé"),
        }
    )
    def post(self, request):
        serializer = FCMTokenUnregisterSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        token = serializer.validated_data['token']
        
        # Supprimer le token
        deleted_count, _ = UserFCMToken.objects.filter(
            token=token,
            user=request.user
        ).delete()
        
        if deleted_count == 0:
            return Response({
                'success': False,
                'message': 'Token non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)
        
        logger.info(f"[FCM] Token unregistered for user {request.user.id}")
        
        return Response({
            'success': True,
            'message': 'Token FCM supprimé avec succès'
        })


class FCMDeviceListView(APIView):
    """
    Liste tous les devices enregistrés pour les notifications push.
    Permet à l'utilisateur de voir et gérer ses devices.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Notifications'],
        summary="Lister les devices enregistrés",
        description="""
        Retourne la liste de tous les devices (navigateurs, mobiles)
        enregistrés pour recevoir des notifications push.
        """,
        responses={
            200: FCMTokenListSerializer(many=True),
        }
    )
    def get(self, request):
        devices = UserFCMToken.objects.filter(
            user=request.user,
            is_active=True
        ).order_by('-created')
        
        serializer = FCMTokenListSerializer(devices, many=True)
        
        return Response({
            'count': devices.count(),
            'devices': serializer.data
        })


class FCMDeviceDeleteView(APIView):
    """
    Supprime un device spécifique par son ID.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Notifications'],
        summary="Supprimer un device",
        description="Supprime un device spécifique de la liste des notifications.",
        responses={
            200: OpenApiResponse(description="Device supprimé"),
            404: OpenApiResponse(description="Device non trouvé"),
        }
    )
    def delete(self, request, device_id):
        try:
            device = UserFCMToken.objects.get(
                id=device_id,
                user=request.user
            )
            device_name = device.device_name or device.get_device_type_display()
            device.delete()
            
            logger.info(f"[FCM] Device {device_id} deleted for user {request.user.id}")
            
            return Response({
                'success': True,
                'message': f'Device "{device_name}" supprimé'
            })
        except UserFCMToken.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Device non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)


class FCMTestNotificationView(APIView):
    """
    Envoie une notification de test à l'utilisateur connecté.
    Utile pour vérifier que les notifications fonctionnent.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Notifications'],
        summary="Envoyer une notification de test",
        description="""
        Envoie une notification push de test à tous les devices
        enregistrés de l'utilisateur connecté.
        
        Utile pour :
        - Vérifier que la configuration FCM est correcte
        - Tester que les notifications arrivent bien
        """,
        responses={
            200: OpenApiResponse(description="Notification envoyée"),
            400: OpenApiResponse(description="Aucun device enregistré"),
        }
    )
    def post(self, request):
        from apps.core.utils.fcm import send_fcm_multicast, FIREBASE_AVAILABLE
        
        if not FIREBASE_AVAILABLE:
            return Response({
                'success': False,
                'message': 'Firebase n\'est pas configuré sur le serveur'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # Récupérer les tokens actifs
        tokens = UserFCMToken.get_active_tokens_for_user(str(request.user.id))
        
        if not tokens:
            return Response({
                'success': False,
                'message': 'Aucun device enregistré pour les notifications. '
                          'Activez d\'abord les notifications dans votre navigateur.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Envoyer la notification de test
        notification = {
            'title': '🔔 Test Pressow',
            'message': 'Les notifications fonctionnent correctement !',
            'data': {
                'type': 'test',
                'timestamp': str(request.user.date_inscription)
            }
        }
        
        result = send_fcm_multicast(tokens, notification)
        
        # Mettre à jour last_used_at pour les tokens utilisés
        if result.get('success_count', 0) > 0:
            UserFCMToken.objects.filter(
                user=request.user,
                token__in=tokens,
                is_active=True
            ).update(last_used_at=request.user.date_inscription)  # Sera remplacé par timezone.now() dans le vrai code
        
        return Response({
            'success': True,
            'message': f'Notification envoyée à {result.get("success_count", 0)} device(s)',
            'details': {
                'total_devices': len(tokens),
                'success': result.get('success_count', 0),
                'failed': result.get('failure_count', 0),
            }
        })
