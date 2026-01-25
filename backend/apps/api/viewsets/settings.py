"""
Viewsets pour les paramètres (Provider et Client)

Endpoints:
- GET/PATCH /api/providers/settings/full/ - Paramètres complets du prestataire
- GET/PATCH /api/clients/notification-preferences/ - Préférences notification client
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.core.models import ProviderSettings
from apps.users.models import UserNotificationPreferences
from apps.api.serializers.settings import (
    ProviderSettingsSerializer,
    ProviderSettingsUpdateSerializer,
    ClientNotificationPreferencesSerializer,
)

logger = logging.getLogger(__name__)


class ProviderFullSettingsView(APIView):
    """
    Gère les paramètres complets du prestataire.
    
    Inclut :
    - Notifications (canaux + types)
    - Disponibilité (horaires, jours, pause, max commandes)
    - Financier (montant minimum)
    - Sécurité (2FA, alertes)
    """
    permission_classes = [IsAuthenticated]
    
    def _get_provider_settings(self, request):
        """Récupère les settings du prestataire de l'utilisateur connecté"""
        user = request.user
        
        # Vérifier si l'utilisateur est un prestataire
        if not hasattr(user, 'provider_profile'):
            return None, "Vous n'êtes pas un prestataire"
        
        provider = user.provider_profile
        
        # Récupérer ou créer les settings
        settings, created = ProviderSettings.objects.get_or_create(
            provider=provider,
            defaults={
                'business_name': provider.nom_commercial,
                'working_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
                'opening_hours': {
                    'weekdays': {'start': '08:00', 'end': '18:00'},
                    'weekends': {'start': '09:00', 'end': '16:00'}
                }
            }
        )
        
        return settings, None
    
    @extend_schema(
        tags=['Paramètres'],
        summary="Récupérer les paramètres du prestataire",
        description="""
        Retourne tous les paramètres configurables du prestataire :
        - Notifications (canaux et types)
        - Disponibilité (horaires, jours de travail, pause)
        - Paramètres financiers
        - Sécurité
        """,
        responses={
            200: ProviderSettingsSerializer,
            403: OpenApiResponse(description="Vous n'êtes pas un prestataire"),
        }
    )
    def get(self, request):
        settings, error = self._get_provider_settings(request)
        
        if error:
            return Response({
                'success': False,
                'message': error
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProviderSettingsSerializer(settings)
        
        return Response({
            'success': True,
            'settings': serializer.data
        })
    
    @extend_schema(
        tags=['Paramètres'],
        summary="Mettre à jour les paramètres du prestataire",
        description="""
        Met à jour les paramètres du prestataire.
        Tous les champs sont optionnels (PATCH).
        """,
        request=ProviderSettingsUpdateSerializer,
        responses={
            200: ProviderSettingsSerializer,
            400: OpenApiResponse(description="Données invalides"),
            403: OpenApiResponse(description="Vous n'êtes pas un prestataire"),
        }
    )
    def patch(self, request):
        settings, error = self._get_provider_settings(request)
        
        if error:
            return Response({
                'success': False,
                'message': error
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProviderSettingsUpdateSerializer(
            settings,
            data=request.data,
            partial=True
        )
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        logger.info(f"Provider {settings.provider.id} updated settings: {list(request.data.keys())}")
        
        # Retourner les settings mis à jour
        return Response({
            'success': True,
            'message': 'Paramètres mis à jour avec succès',
            'settings': ProviderSettingsSerializer(settings).data
        })


class ClientNotificationPreferencesView(APIView):
    """
    Gère les préférences de notification des clients.
    """
    permission_classes = [IsAuthenticated]
    
    def _get_preferences(self, request):
        """Récupère ou crée les préférences de l'utilisateur"""
        return UserNotificationPreferences.get_or_create_for_user(request.user)
    
    @extend_schema(
        tags=['Paramètres'],
        summary="Récupérer les préférences de notification",
        description="Retourne les préférences de notification de l'utilisateur connecté.",
        responses={
            200: ClientNotificationPreferencesSerializer,
        }
    )
    def get(self, request):
        prefs = self._get_preferences(request)
        serializer = ClientNotificationPreferencesSerializer(prefs)
        
        return Response({
            'success': True,
            'preferences': serializer.data
        })
    
    @extend_schema(
        tags=['Paramètres'],
        summary="Mettre à jour les préférences de notification",
        description="Met à jour les préférences de notification. Tous les champs sont optionnels.",
        request=ClientNotificationPreferencesSerializer,
        responses={
            200: ClientNotificationPreferencesSerializer,
            400: OpenApiResponse(description="Données invalides"),
        }
    )
    def patch(self, request):
        prefs = self._get_preferences(request)
        
        serializer = ClientNotificationPreferencesSerializer(
            prefs,
            data=request.data,
            partial=True
        )
        
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        logger.info(f"User {request.user.id} updated notification preferences")
        
        return Response({
            'success': True,
            'message': 'Préférences mises à jour',
            'preferences': ClientNotificationPreferencesSerializer(prefs).data
        })


class ProviderPauseToggleView(APIView):
    """
    Active/désactive rapidement le mode pause du prestataire.
    
    Endpoint simplifié pour un toggle rapide depuis le dashboard.
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['Paramètres'],
        summary="Basculer le mode pause",
        description="""
        Active ou désactive le mode pause du prestataire.
        Quand activé, le pressing n'accepte plus de nouvelles commandes.
        """,
        responses={
            200: OpenApiResponse(description="Mode pause basculé"),
            403: OpenApiResponse(description="Vous n'êtes pas un prestataire"),
        }
    )
    def post(self, request):
        user = request.user
        
        if not hasattr(user, 'provider_profile'):
            return Response({
                'success': False,
                'message': "Vous n'êtes pas un prestataire"
            }, status=status.HTTP_403_FORBIDDEN)
        
        provider = user.provider_profile
        settings = getattr(provider, 'settings', None)
        
        if not settings:
            return Response({
                'success': False,
                'message': "Paramètres non trouvés"
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Récupérer la raison si fournie
        reason = request.data.get('reason', '')
        
        # Toggle le mode pause
        settings.pause_mode = not settings.pause_mode
        if settings.pause_mode:
            settings.pause_reason = reason
        else:
            settings.pause_reason = ''
        
        settings.save(update_fields=['pause_mode', 'pause_reason', 'updated'])
        
        status_text = 'activé' if settings.pause_mode else 'désactivé'
        logger.info(f"Provider {provider.id} pause mode {status_text}")
        
        return Response({
            'success': True,
            'message': f'Mode pause {status_text}',
            'pause_mode': settings.pause_mode,
            'pause_reason': settings.pause_reason
        })
