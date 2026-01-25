"""Endpoints Provider (agences, staff, rôles)."""
from __future__ import annotations

from typing import Optional

from django.db import transaction  # type: ignore
from rest_framework import permissions, status  # type: ignore
from rest_framework.exceptions import NotFound, ValidationError, PermissionDenied  # type: ignore
from rest_framework.response import Response  # type: ignore
from rest_framework.views import APIView  # type: ignore

from apps.api.permissions import (
    IsProviderMember,
    CanManageStaff,
    require_provider_member,
    require_can_manage_staff,
    CanManageSettings,
    require_can_manage_settings,
    CanManageServices,
    require_can_manage_services,
    CanManageTariffs,
    require_can_manage_tariffs,
)
from apps.api.serializers.providers import (
    ProviderProfileSerializer,
    ProviderProfileUpdateSerializer,
    ProviderAgencySerializer,
    ProviderAgencyWriteSerializer,
    ProviderStaffSerializer,
    ProviderStaffInviteSerializer,
    ProviderStaffUpdateSerializer,
    ProviderStaffActivateSerializer,
    ProviderSettingsSerializer,
    ProviderSettingsUpdateSerializer,
    ProviderServiceSerializer,
    ProviderServiceWriteSerializer,
    ArticleTypeSerializer,
    ArticleTypeWriteSerializer,
    MatiereSerializer,
    MatiereWriteSerializer,
    TariffSerializer,
    TariffWriteSerializer,
)
from apps.providers.models import Provider, ProviderAgency, ProviderStaff
from apps.core.models import ProviderSettings
from apps.providers.services.staff import invite_staff, activate_staff, assign_role
from apps.services.models import Service, ArticleType, Matiere
from apps.tariffs.models import ProviderService as ProviderServiceLink, Tariff


def _get_agency_or_404(provider: Provider, agency_id) -> ProviderAgency:
    try:
        return provider.agencies.get(id=agency_id)
    except ProviderAgency.DoesNotExist as exc:
        raise NotFound('Agence introuvable') from exc


def _get_staff_or_404(provider: Provider, staff_id) -> ProviderStaff:
    try:
        return provider.staff_members.select_related('user', 'agency', 'role').get(id=staff_id)
    except ProviderStaff.DoesNotExist as exc:
        raise NotFound('Membre du staff introuvable') from exc


def _get_service_or_404(provider: Provider, service_id) -> Service:
    try:
        return Service.objects.filter(provider=provider).get(id=service_id)
    except Service.DoesNotExist as exc:
        raise NotFound('Service introuvable') from exc


def _get_provider_service_or_404(provider: Provider, pk) -> ProviderServiceLink:
    try:
        return ProviderServiceLink.objects.select_related('service').get(provider=provider, id=pk)
    except ProviderServiceLink.DoesNotExist as exc:
        raise NotFound('Catalogue service introuvable') from exc


def _get_article_type_or_404(provider: Provider, pk) -> ArticleType:
    try:
        return ArticleType.objects.get(provider=provider, id=pk)
    except ArticleType.DoesNotExist as exc:
        raise NotFound("Type d'article introuvable") from exc


def _get_matiere_or_404(provider: Provider, pk) -> Matiere:
    try:
        return Matiere.objects.get(provider=provider, id=pk)
    except Matiere.DoesNotExist as exc:
        raise NotFound('Matière introuvable') from exc


def _get_tariff_or_404(provider: Provider, pk) -> Tariff:
    try:
        return Tariff.objects.get(provider=provider, id=pk)
    except Tariff.DoesNotExist as exc:
        raise NotFound('Tarif introuvable') from exc


def _ensure_single_default(
    provider: Provider,
    agency: ProviderAgency,
    desired_state: Optional[bool] = None,
) -> None:
    if desired_state is not None:
        agency.is_default = desired_state

    if agency.is_default:
        provider.agencies.exclude(id=agency.id).filter(is_default=True).update(is_default=False)
        agency.save(update_fields=['is_default'])
    elif not provider.agencies.filter(is_default=True).exists():
        agency.is_default = True
        agency.save(update_fields=['is_default'])


def _ensure_default_after_delete(provider: Provider) -> None:
    if not provider.agencies.filter(is_default=True).exists():
        next_agency = provider.agencies.order_by('created').first()
        if next_agency:
            next_agency.is_default = True
            next_agency.save(update_fields=['is_default'])


def _assert_can_modify_owner(actor: Optional[ProviderStaff], target: ProviderStaff) -> None:
    if target.system_role != 'owner':
        return
    if actor and actor.system_role == 'owner':
        return
    raise PermissionDenied("Seul le propriétaire peut modifier un propriétaire")


# ═══════════════════════════════════════════════════════════════════════════════
# PROVIDER PROFILE (Infos du Provider lui-même)
# ═══════════════════════════════════════════════════════════════════════════════

class ProviderProfileView(APIView):
    """
    Endpoint pour lire/modifier le profil du Provider connecté
    GET: Retourne les infos complètes du Provider
    PATCH: Modifie les infos du Provider (nom_commercial, photo_local, zone, etc.)
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def get(self, request):
        provider, _ = require_provider_member(request)
        serializer = ProviderProfileSerializer(provider, context={'request': request})
        return Response(serializer.data)
    
    def patch(self, request):
        provider, _ = require_provider_member(request)
        
        # Seul le owner peut modifier les infos du provider
        staff = provider.staff_members.filter(user=request.user).first()
        if staff and staff.system_role != 'owner':
            raise PermissionDenied("Seul le propriétaire peut modifier les informations de l'entreprise.")
        
        serializer = ProviderProfileUpdateSerializer(
            provider, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Gérer la suppression de l'ancienne photo si une nouvelle est uploadée
        if 'photo_local' in request.data and provider.photo_local:
            provider.photo_local.delete(save=False)
        
        serializer.save()
        
        return Response({
            'message': 'Profil entreprise mis à jour avec succès',
            'provider': ProviderProfileSerializer(provider, context={'request': request}).data
        })


class ProviderPhotoView(APIView):
    """
    Endpoint dédié pour upload/suppression de la photo du local
    POST: Upload une nouvelle photo
    DELETE: Supprime la photo actuelle
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def post(self, request):
        provider, _ = require_provider_member(request)
        
        # Vérifier les permissions
        staff = provider.staff_members.filter(user=request.user).first()
        if staff and staff.system_role != 'owner':
            raise PermissionDenied("Seul le propriétaire peut modifier la photo de l'entreprise.")
        
        if 'photo_local' not in request.FILES:
            raise ValidationError({'photo_local': 'Aucune photo fournie.'})
        
        photo = request.FILES['photo_local']
        
        # Vérifier la taille (max 5MB)
        if photo.size > 5 * 1024 * 1024:
            raise ValidationError({'photo_local': 'La photo ne doit pas dépasser 5MB.'})
        
        # Supprimer l'ancienne photo si elle existe
        if provider.photo_local:
            provider.photo_local.delete(save=False)
        
        provider.photo_local = photo
        provider.save(update_fields=['photo_local', 'updated'])
        
        return Response({
            'message': 'Photo mise à jour avec succès',
            'photo_url': request.build_absolute_uri(provider.photo_local.url) if provider.photo_local else None
        })
    
    def delete(self, request):
        provider, _ = require_provider_member(request)
        
        # Vérifier les permissions
        staff = provider.staff_members.filter(user=request.user).first()
        if staff and staff.system_role != 'owner':
            raise PermissionDenied("Seul le propriétaire peut supprimer la photo de l'entreprise.")
        
        if provider.photo_local:
            provider.photo_local.delete(save=True)
            return Response({'message': 'Photo supprimée avec succès'})
        return Response({'message': 'Aucune photo à supprimer'}, status=status.HTTP_400_BAD_REQUEST)


class ProviderAgencyListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]

    def get(self, request):
        provider, _ = require_provider_member(request)
        agencies = provider.agencies.order_by('-is_default', 'name')
        serializer = ProviderAgencySerializer(agencies, many=True)
        return Response(serializer.data)

    def post(self, request):
        provider, _ = require_can_manage_staff(request)
        serializer = ProviderAgencyWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        make_default = serializer.validated_data.pop('is_default', None)
        with transaction.atomic():
            agency = serializer.save(provider=provider)
            _ensure_single_default(provider, agency, desired_state=make_default)
        return Response(ProviderAgencySerializer(agency).data, status=status.HTTP_201_CREATED)


class ProviderAgencyDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]

    def get(self, request, agency_id):
        provider, _ = require_provider_member(request)
        agency = _get_agency_or_404(provider, agency_id)
        return Response(ProviderAgencySerializer(agency).data)

    def patch(self, request, agency_id):
        provider, _ = require_can_manage_staff(request)
        agency = _get_agency_or_404(provider, agency_id)
        serializer = ProviderAgencyWriteSerializer(agency, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        make_default = serializer.validated_data.pop('is_default', None)
        with transaction.atomic():
            agency = serializer.save()
            _ensure_single_default(provider, agency, desired_state=make_default)
        return Response(ProviderAgencySerializer(agency).data)

    def delete(self, request, agency_id):
        provider, _ = require_can_manage_staff(request)
        agency = _get_agency_or_404(provider, agency_id)
        if agency.is_default and not provider.agencies.exclude(id=agency.id).exists():
            raise ValidationError('Impossible de supprimer l\'unique agence du prestataire.')
        agency.delete()
        _ensure_default_after_delete(provider)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProviderStaffListView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageStaff]

    def get(self, request):
        provider, _ = require_can_manage_staff(request)
        staff_qs = provider.staff_members.select_related('user', 'agency', 'role').order_by('-system_role', 'user__first_name')
        return Response(ProviderStaffSerializer(staff_qs, many=True).data)


class ProviderStaffInviteView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageStaff]

    def post(self, request):
        provider, _ = require_can_manage_staff(request)
        serializer = ProviderStaffInviteSerializer(data=request.data, context={'provider': provider})
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        staff = invite_staff(
            provider=provider,
            email=payload.get('email'),
            phone=payload.get('phone'),
            system_role=payload.get('system_role', 'operator'),
            role=payload.get('role'),
            agency=payload.get('agency'),
        )
        if payload.get('notes'):
            staff.notes = payload['notes']
            staff.save(update_fields=['notes'])
        return Response(ProviderStaffSerializer(staff).data, status=status.HTTP_201_CREATED)


class ProviderStaffDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageStaff]

    def get(self, request, staff_id):
        provider, _ = require_can_manage_staff(request)
        staff = _get_staff_or_404(provider, staff_id)
        return Response(ProviderStaffSerializer(staff).data)

    def patch(self, request, staff_id):
        provider, actor = require_can_manage_staff(request)
        staff = _get_staff_or_404(provider, staff_id)
        _assert_can_modify_owner(actor, staff)
        serializer = ProviderStaffUpdateSerializer(data=request.data, context={'provider': provider})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        updates = []
        if 'system_role' in data:
            staff.system_role = data['system_role']
            updates.append('system_role')
        if 'status' in data:
            staff.status = data['status']
            updates.append('status')
        if 'notes' in data:
            staff.notes = data['notes']
            updates.append('notes')
        assign_kwargs = {}
        if data.get('role_provided'):
            assign_kwargs['role'] = data.get('role')
        if data.get('agency_provided'):
            assign_kwargs['agency'] = data.get('agency')
        if assign_kwargs:
            assign_role(staff, **assign_kwargs)

        if updates:
            staff.save(update_fields=list(set(updates)))
        staff.refresh_from_db()
        return Response(ProviderStaffSerializer(staff).data)

    def delete(self, request, staff_id):
        provider, actor = require_can_manage_staff(request)
        staff = _get_staff_or_404(provider, staff_id)
        _assert_can_modify_owner(actor, staff)
        staff.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProviderStaffActivateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ProviderStaffActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            staff = activate_staff(serializer.validated_data['invite_token'], request.user)
        except ProviderStaff.DoesNotExist as exc:
            raise NotFound('Invitation introuvable ou expirée') from exc
        return Response(ProviderStaffSerializer(staff).data)


def _get_or_create_settings(provider: Provider) -> ProviderSettings:
    settings = getattr(provider, 'settings', None)
    if settings:
        return settings
    settings, _ = ProviderSettings.objects.get_or_create(
        provider=provider,
        defaults={'business_name': provider.nom_commercial},
    )
    return settings


class ProviderSettingsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]

    def get(self, request):
        provider, _ = require_provider_member(request)
        settings = _get_or_create_settings(provider)
        # Passer le contexte request pour que les URLs soient absolues
        return Response(ProviderSettingsSerializer(settings, context={'request': request}).data)

    def patch(self, request):
        provider, _ = require_can_manage_settings(request)
        settings = _get_or_create_settings(provider)
        serializer = ProviderSettingsUpdateSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Recharger et passer le contexte request pour que les URLs soient absolues
        settings.refresh_from_db()
        return Response(ProviderSettingsSerializer(settings, context={'request': request}).data)


class ProviderServiceListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageServices]

    def get(self, request):
        provider, _ = require_can_manage_services(request)
        services = ProviderServiceLink.objects.filter(provider=provider).select_related('service').order_by('service__label')
        return Response(ProviderServiceSerializer(services, many=True).data)

    def post(self, request):
        provider, _ = require_can_manage_services(request)
        serializer = ProviderServiceWriteSerializer(data=request.data, context={'provider': provider})
        serializer.is_valid(raise_exception=True)
        offer = serializer.save()
        return Response(ProviderServiceSerializer(offer).data, status=status.HTTP_201_CREATED)


class ProviderServiceDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageServices]

    def get(self, request, service_id):
        provider, _ = require_can_manage_services(request)
        offer = _get_provider_service_or_404(provider, service_id)
        return Response(ProviderServiceSerializer(offer).data)

    def patch(self, request, service_id):
        provider, _ = require_can_manage_services(request)
        offer = _get_provider_service_or_404(provider, service_id)
        serializer = ProviderServiceWriteSerializer(
            offer,
            data=request.data,
            partial=True,
            context={'provider': provider},
        )
        serializer.is_valid(raise_exception=True)
        offer = serializer.save()
        return Response(ProviderServiceSerializer(offer).data)

    def delete(self, request, service_id):
        provider, _ = require_can_manage_services(request)
        offer = _get_provider_service_or_404(provider, service_id)
        offer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProviderArticleTypeListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageServices]

    def get(self, request):
        provider, _ = require_can_manage_services(request)
        items = ArticleType.objects.filter(provider=provider).order_by('nom')
        return Response(ArticleTypeSerializer(items, many=True).data)

    def post(self, request):
        provider, _ = require_can_manage_services(request)
        serializer = ArticleTypeWriteSerializer(data=request.data, context={'provider': provider})
        serializer.is_valid(raise_exception=True)
        article_type = serializer.save()
        return Response(ArticleTypeSerializer(article_type).data, status=status.HTTP_201_CREATED)


class ProviderArticleTypeDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageServices]

    def get(self, request, type_id):
        provider, _ = require_can_manage_services(request)
        article_type = _get_article_type_or_404(provider, type_id)
        return Response(ArticleTypeSerializer(article_type).data)

    def patch(self, request, type_id):
        provider, _ = require_can_manage_services(request)
        article_type = _get_article_type_or_404(provider, type_id)
        serializer = ArticleTypeWriteSerializer(article_type, data=request.data, partial=True, context={'provider': provider})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ArticleTypeSerializer(article_type).data)

    def delete(self, request, type_id):
        provider, _ = require_can_manage_services(request)
        article_type = _get_article_type_or_404(provider, type_id)
        article_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProviderMatiereListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageServices]

    def get(self, request):
        provider, _ = require_can_manage_services(request)
        items = Matiere.objects.filter(provider=provider).order_by('nom')
        return Response(MatiereSerializer(items, many=True).data)

    def post(self, request):
        provider, _ = require_can_manage_services(request)
        serializer = MatiereWriteSerializer(data=request.data, context={'provider': provider})
        serializer.is_valid(raise_exception=True)
        matiere = serializer.save()
        return Response(MatiereSerializer(matiere).data, status=status.HTTP_201_CREATED)


class ProviderMatiereDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageServices]

    def get(self, request, matiere_id):
        provider, _ = require_can_manage_services(request)
        matiere = _get_matiere_or_404(provider, matiere_id)
        return Response(MatiereSerializer(matiere).data)

    def patch(self, request, matiere_id):
        provider, _ = require_can_manage_services(request)
        matiere = _get_matiere_or_404(provider, matiere_id)
        serializer = MatiereWriteSerializer(matiere, data=request.data, partial=True, context={'provider': provider})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MatiereSerializer(matiere).data)

    def delete(self, request, matiere_id):
        provider, _ = require_can_manage_services(request)
        matiere = _get_matiere_or_404(provider, matiere_id)
        matiere.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProviderTariffListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageTariffs]

    def get(self, request):
        provider, _ = require_can_manage_tariffs(request)
        qs = Tariff.objects.filter(provider=provider).select_related('article_type', 'matiere', 'service')
        return Response(TariffSerializer(qs, many=True).data)

    def post(self, request):
        provider, _ = require_can_manage_tariffs(request)
        serializer = TariffWriteSerializer(data=request.data, context={'provider': provider})
        serializer.is_valid(raise_exception=True)
        tariff = serializer.save()
        return Response(TariffSerializer(tariff).data, status=status.HTTP_201_CREATED)


class ProviderTariffDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanManageTariffs]

    def get(self, request, tariff_id):
        provider, _ = require_can_manage_tariffs(request)
        tariff = _get_tariff_or_404(provider, tariff_id)
        return Response(TariffSerializer(tariff).data)

    def patch(self, request, tariff_id):
        provider, _ = require_can_manage_tariffs(request)
        tariff = _get_tariff_or_404(provider, tariff_id)
        serializer = TariffWriteSerializer(tariff, data=request.data, partial=True, context={'provider': provider})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(TariffSerializer(tariff).data)

    def delete(self, request, tariff_id):
        provider, _ = require_can_manage_tariffs(request)
        tariff = _get_tariff_or_404(provider, tariff_id)
        tariff.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CatalogProviderServicesPublicView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, provider_id):
        services = ProviderServiceLink.objects.filter(
            provider_id=provider_id,
            is_available=True,
        ).select_related('service')
        return Response(ProviderServiceSerializer(services, many=True).data)


class CatalogProviderServiceDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, provider_id, offer_id):
        try:
            provider = Provider.objects.get(id=provider_id, is_active=True)
        except Provider.DoesNotExist as exc:
            raise NotFound('Prestataire introuvable') from exc

        try:
            offer = ProviderServiceLink.objects.select_related('service').get(
                provider=provider,
                id=offer_id,
                is_available=True,
            )
        except ProviderServiceLink.DoesNotExist as exc:
            raise NotFound('Service non disponible') from exc

        tariffs = Tariff.objects.select_related('article_type', 'matiere').filter(
            provider=provider,
            service=offer.service,
        )
        article_type_ids = tariffs.values_list('article_type_id', flat=True)
        matiere_ids = [mid for mid in tariffs.values_list('matiere_id', flat=True) if mid]

        article_types = ArticleType.objects.filter(id__in=article_type_ids)
        matieres = Matiere.objects.filter(id__in=matiere_ids) if matiere_ids else Matiere.objects.none()

        data = {
            'service': {
                'id': str(offer.service.id),
                'label': offer.service.label,
                'description': offer.service.description,
                'mode_tarif': offer.service.mode_tarif,
                'duree_estimee': offer.service.duree_estimee,
                'icone': offer.service.icone,
            },
            'provider_service': ProviderServiceSerializer(offer).data,
            'article_types': ArticleTypeSerializer(article_types, many=True).data,
            'matieres': MatiereSerializer(matieres, many=True).data,
            'tariffs': TariffSerializer(tariffs, many=True).data,
        }
        return Response(data)


class NearbyProvidersView(APIView):
    """
    GET /api/catalog/providers/nearby/?lat=X&lng=Y&radius=10
    
    Liste les pressings disponibles proches d'une position géographique.
    Endpoint public (pas d'authentification requise).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = int(request.query_params.get('radius', 10))  # km par défaut

        if not lat or not lng:
            return Response(
                {'detail': 'Les paramètres lat et lng sont requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            lat = float(lat)
            lng = float(lng)
        except ValueError:
            return Response(
                {'detail': 'lat et lng doivent être des nombres valides'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Récupérer les providers actifs avec onboarding terminé
        # Les champs onboarding_completed et is_open sont dans ProviderSettings
        providers = Provider.objects.filter(
            settings__onboarding_completed=True,
            settings__is_open=True,
        ).select_related('settings').prefetch_related('provider_services')

        # TODO: Ajouter filtrage géographique avec PostGIS quand les données seront disponibles
        # from django.contrib.gis.geos import Point
        # from django.contrib.gis.measure import D
        # point = Point(lng, lat, srid=4326)
        # providers = providers.filter(location__distance_lte=(point, D(km=radius)))

        # Pour le MVP, on retourne tous les providers actifs (max 50)
        providers = providers[:50]

        result = []
        for provider in providers:
            # Compter les services disponibles
            services_count = provider.provider_services.filter(is_available=True).count()
            
            # Récupérer les settings (on sait qu'ils existent car on a filtré dessus)
            prov_settings = provider.settings
            
            result.append({
                'id': str(provider.id),
                'nom_commercial': provider.nom_commercial,
                'photo': provider.photo_local.url if provider.photo_local else None,
                'ville': provider.ville or '',
                'adresse': provider.adresse or '',
                'latitude': float(provider.latitude) if provider.latitude else None,
                'longitude': float(provider.longitude) if provider.longitude else None,
                'note_moyenne': 4.5,  # TODO: Calculer la vraie note moyenne
                'services_count': services_count,
                'is_open': prov_settings.is_open,
                'min_order_amount': float(prov_settings.min_order_amount) if prov_settings.min_order_amount else 500,
            })

        return Response(result)
