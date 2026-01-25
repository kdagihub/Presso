"""
Endpoints pour l'onboarding des prestataires.

Ces endpoints gèrent le parcours de configuration initiale obligatoire
avant qu'un pressing ne soit visible sur la marketplace.
"""
from __future__ import annotations

from django.db import transaction  # type: ignore
from django.utils import timezone  # type: ignore
from rest_framework import permissions, status  # type: ignore
from rest_framework.exceptions import ValidationError, PermissionDenied  # type: ignore
from rest_framework.response import Response  # type: ignore
from rest_framework.views import APIView  # type: ignore

from apps.api.permissions import IsProviderMember, require_provider_member
from apps.api.serializers.onboarding import (
    OnboardingStatusSerializer,
    OnboardingIdentitySerializer,
    OnboardingServicesSerializer,
    OnboardingPayoutAccountSerializer,
    ProviderPayoutAccountReadSerializer,
    OnboardingCompleteResponseSerializer,
    ProviderOpenStatusSerializer,
)
from apps.providers.models import Provider
from apps.core.models import ProviderSettings, ProviderPayoutAccount
from apps.services.models import Service, ServiceTemplate
from apps.tariffs.models import ProviderService as ProviderServiceLink


def _get_or_create_settings(provider: Provider) -> ProviderSettings:
    """Récupère ou crée les settings d'un provider."""
    settings = getattr(provider, 'settings', None)
    if settings:
        return settings
    settings, _ = ProviderSettings.objects.get_or_create(
        provider=provider,
        defaults={'business_name': provider.nom_commercial},
    )
    return settings


class OnboardingStatusView(APIView):
    """
    GET /api/provider/onboarding/status/
    
    Retourne l'état d'onboarding du prestataire connecté.
    Utilisé par le frontend pour déterminer quelle vue afficher.
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def get(self, request):
        provider, _ = require_provider_member(request)
        settings = _get_or_create_settings(provider)
        
        # Construire le statut détaillé
        onboarding_status = settings.get_onboarding_status()
        
        # Ajouter les infos du provider
        data = {
            **onboarding_status,
            'provider_id': str(provider.id),
            'business_name': settings.business_name,
            'is_open': settings.is_open,
        }
        
        return Response(data)


class OnboardingIdentityView(APIView):
    """
    POST /api/provider/onboarding/identity/
    
    Étape 1 : Identité du pressing
    - Nom de la boutique
    - Localisation GPS
    - Logo / Photo de la devanture
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def post(self, request):
        provider, _ = require_provider_member(request)
        settings = _get_or_create_settings(provider)
        
        serializer = OnboardingIdentitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        with transaction.atomic():
            # Mettre à jour le Provider
            provider.adresse = data['adresse']
            provider.ville = data['ville']
            provider.quartier = data.get('quartier', '')
            provider.zone_couverture = data.get('zone_couverture', '')
            provider.rayon_km = data.get('rayon_km', 5.00)
            
            if data.get('latitude') is not None:
                provider.latitude = data['latitude']
                provider.longitude = data['longitude']
            
            provider.save()
            
            # Mettre à jour les ProviderSettings
            settings.business_name = data['business_name']
            
            if data.get('logo'):
                settings.logo = data['logo']
            
            if data.get('storefront_photo'):
                settings.storefront_photo = data['storefront_photo']
            
            settings.save()
            
            # Avancer l'onboarding à l'étape 1
            settings.advance_onboarding(1)
        
        return Response({
            'success': True,
            'message': 'Identité du pressing enregistrée',
            'current_step': settings.onboarding_step,
        }, status=status.HTTP_200_OK)


class OnboardingServicesView(APIView):
    """
    POST /api/provider/onboarding/services/
    
    Étape 2 : Services et tarifs
    Crée les services avec leurs tarifs de base.
    Au moins un service doit être configuré.
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def post(self, request):
        provider, _ = require_provider_member(request)
        settings = _get_or_create_settings(provider)
        
        # Vérifier que l'étape 1 est complète
        if settings.onboarding_step < 1:
            raise ValidationError({
                'detail': "L'étape 1 (Identité) doit être complétée d'abord."
            })
        
        serializer = OnboardingServicesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services_data = serializer.validated_data['services']
        
        created_services = []
        
        with transaction.atomic():
            for svc_data in services_data:
                # Chercher ou créer le service
                template = None
                if svc_data.get('template_id'):
                    try:
                        template = ServiceTemplate.objects.get(
                            id=svc_data['template_id'],
                            is_active=True
                        )
                    except ServiceTemplate.DoesNotExist:
                        pass
                
                # Créer le service personnalisé
                service, created = Service.objects.get_or_create(
                    provider=provider,
                    label=svc_data['label'].strip(),
                    defaults={
                        'mode_tarif': svc_data.get('mode_tarif', 'piece'),
                        'duree_estimee': svc_data.get('delai', 24) * 60,  # Convertir heures en minutes
                        'template': template,
                        'is_active': True,
                    }
                )
                
                # Créer ou mettre à jour le lien ProviderService
                provider_service, _ = ProviderServiceLink.objects.update_or_create(
                    provider=provider,
                    service=service,
                    defaults={
                        'prix_base': svc_data['prix_base'],
                        'delai': svc_data.get('delai', 24),
                        'is_available': True,
                    }
                )
                
                created_services.append({
                    'id': str(service.id),
                    'label': service.label,
                    'prix_base': str(provider_service.prix_base),
                    'delai': provider_service.delai,
                })
            
            # Avancer l'onboarding à l'étape 2
            settings.advance_onboarding(2)
        
        return Response({
            'success': True,
            'message': f'{len(created_services)} service(s) configuré(s)',
            'current_step': settings.onboarding_step,
            'services': created_services,
        }, status=status.HTTP_200_OK)


class OnboardingPayoutView(APIView):
    """
    POST /api/provider/onboarding/payout/
    
    Étape 3 : Informations de paiement
    Configure le compte Mobile Money pour les retraits.
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def post(self, request):
        provider, _ = require_provider_member(request)
        settings = _get_or_create_settings(provider)
        
        # Vérifier que l'étape 2 est complète
        if settings.onboarding_step < 2:
            raise ValidationError({
                'detail': "L'étape 2 (Services) doit être complétée d'abord."
            })
        
        serializer = OnboardingPayoutAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        with transaction.atomic():
            # Créer ou mettre à jour le compte de paiement
            payout_account, created = ProviderPayoutAccount.objects.update_or_create(
                provider=provider,
                operator=data['operator'],
                phone_number=data['phone_number'],
                defaults={
                    'account_name': data['account_name'],
                    'is_primary': True,
                    'status': 'pending',  # En attente de vérification
                }
            )
            
            # Avancer l'onboarding à l'étape 3 (terminé)
            settings.advance_onboarding(3)
            
            # Ouvrir automatiquement le pressing
            settings.is_open = True
            settings.save(update_fields=['is_open', 'updated'])
        
        return Response({
            'success': True,
            'message': 'Compte de paiement configuré. Votre pressing est maintenant actif !',
            'current_step': settings.onboarding_step,
            'onboarding_completed': settings.onboarding_completed,
            'payout_account': ProviderPayoutAccountReadSerializer(payout_account).data,
        }, status=status.HTTP_200_OK)


class OnboardingCompleteView(APIView):
    """
    GET /api/provider/onboarding/complete/
    
    Vérifie que l'onboarding est complet et retourne un résumé.
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def get(self, request):
        provider, _ = require_provider_member(request)
        settings = _get_or_create_settings(provider)
        
        if not settings.onboarding_completed:
            return Response({
                'success': False,
                'message': "L'onboarding n'est pas terminé.",
                'current_step': settings.onboarding_step,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Compter les services et comptes
        services_count = ProviderServiceLink.objects.filter(
            provider=provider,
            is_available=True
        ).count()
        
        payout_accounts_count = ProviderPayoutAccount.objects.filter(
            provider=provider
        ).count()
        
        return Response({
            'success': True,
            'message': 'Onboarding terminé avec succès !',
            'provider_id': str(provider.id),
            'business_name': settings.business_name,
            'is_open': settings.is_open,
            'services_count': services_count,
            'payout_accounts_count': payout_accounts_count,
        })


class ProviderOpenStatusView(APIView):
    """
    GET /api/provider/status/
    POST /api/provider/status/
    
    Toggle l'état ouvert/fermé du pressing.
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def get(self, request):
        provider, _ = require_provider_member(request)
        settings = _get_or_create_settings(provider)
        
        return Response({
            'is_open': settings.is_open,
            'closed_reason': settings.closed_reason,
            'onboarding_completed': settings.onboarding_completed,
        })
    
    def post(self, request):
        provider, _ = require_provider_member(request)
        settings = _get_or_create_settings(provider)
        
        # Vérifier que l'onboarding est terminé
        if not settings.onboarding_completed:
            raise ValidationError({
                'detail': "L'onboarding doit être terminé avant de pouvoir ouvrir le pressing."
            })
        
        serializer = ProviderOpenStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        settings.is_open = data['is_open']
        settings.closed_reason = data.get('closed_reason', '')
        settings.save(update_fields=['is_open', 'closed_reason', 'updated'])
        
        status_text = "ouvert" if settings.is_open else "fermé"
        
        return Response({
            'success': True,
            'message': f'Le pressing est maintenant {status_text}.',
            'is_open': settings.is_open,
            'closed_reason': settings.closed_reason,
        })


class ProviderPayoutAccountListCreateView(APIView):
    """
    GET /api/provider/payout-accounts/
    POST /api/provider/payout-accounts/
    
    Gestion des comptes de paiement du prestataire.
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def get(self, request):
        provider, _ = require_provider_member(request)
        accounts = ProviderPayoutAccount.objects.filter(provider=provider)
        serializer = ProviderPayoutAccountReadSerializer(accounts, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        provider, _ = require_provider_member(request)
        
        serializer = OnboardingPayoutAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Vérifier si le compte existe déjà
        existing = ProviderPayoutAccount.objects.filter(
            provider=provider,
            operator=data['operator'],
            phone_number=data['phone_number']
        ).first()
        
        if existing:
            raise ValidationError({
                'detail': 'Ce compte de paiement existe déjà.'
            })
        
        account = ProviderPayoutAccount.objects.create(
            provider=provider,
            operator=data['operator'],
            phone_number=data['phone_number'],
            account_name=data['account_name'],
            status='pending',
        )
        
        return Response(
            ProviderPayoutAccountReadSerializer(account).data,
            status=status.HTTP_201_CREATED
        )


class ProviderPayoutAccountDetailView(APIView):
    """
    GET /api/provider/payout-accounts/<uuid:account_id>/
    PATCH /api/provider/payout-accounts/<uuid:account_id>/
    DELETE /api/provider/payout-accounts/<uuid:account_id>/
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def _get_account(self, provider, account_id):
        try:
            return ProviderPayoutAccount.objects.get(
                provider=provider,
                id=account_id
            )
        except ProviderPayoutAccount.DoesNotExist:
            raise ValidationError({'detail': 'Compte de paiement introuvable.'})
    
    def get(self, request, account_id):
        provider, _ = require_provider_member(request)
        account = self._get_account(provider, account_id)
        return Response(ProviderPayoutAccountReadSerializer(account).data)
    
    def patch(self, request, account_id):
        provider, _ = require_provider_member(request)
        account = self._get_account(provider, account_id)
        
        # Seul le nom et is_primary peuvent être modifiés
        if 'account_name' in request.data:
            account.account_name = request.data['account_name']
        
        if 'is_primary' in request.data and request.data['is_primary']:
            account.is_primary = True
        
        account.save()
        
        return Response(ProviderPayoutAccountReadSerializer(account).data)
    
    def delete(self, request, account_id):
        provider, _ = require_provider_member(request)
        account = self._get_account(provider, account_id)
        
        # Ne pas supprimer le dernier compte
        if ProviderPayoutAccount.objects.filter(provider=provider).count() <= 1:
            raise ValidationError({
                'detail': 'Impossible de supprimer le dernier compte de paiement.'
            })
        
        account.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
