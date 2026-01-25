"""
Viewsets pour le tableau de bord prestataire.
"""
from datetime import timedelta
from decimal import Decimal
from django.db.models import Sum, Count, Q  # type: ignore
from django.utils import timezone  # type: ignore
from rest_framework import status, permissions  # type: ignore
from rest_framework.views import APIView  # type: ignore
from rest_framework.response import Response  # type: ignore

from apps.api.viewsets.providers import require_provider_member, IsProviderMember
from apps.core.services import WalletService
from apps.orders.models import Order
from apps.core.models import ProviderSettings, ProviderPayoutAccount


class DashboardSummaryView(APIView):
    """
    GET /api/provider/dashboard/
    
    Retourne le résumé du tableau de bord :
    - Stats du jour/semaine/mois
    - Checklist de configuration
    - Nouvelles commandes
    - Solde wallet
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def get(self, request):
        provider, _ = require_provider_member(request)
        
        # Récupérer les settings
        try:
            settings = provider.settings
        except ProviderSettings.DoesNotExist:
            settings = ProviderSettings.objects.create(
                provider=provider,
                business_name=provider.nom_commercial
            )
        
        # Dates de référence
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)
        
        # Stats des commandes
        orders = Order.objects.filter(provider=provider)
        
        # Commandes du jour
        today_orders = orders.filter(created__gte=today_start)
        today_stats = today_orders.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(statut='pending')),
            delivered=Count('id', filter=Q(statut='delivered')),
            revenue=Sum('provider_net_amount', filter=Q(statut='delivered'))
        )
        
        # Commandes de la semaine
        week_orders = orders.filter(created__gte=week_start)
        week_stats = week_orders.aggregate(
            total=Count('id'),
            delivered=Count('id', filter=Q(statut='delivered')),
            revenue=Sum('provider_net_amount', filter=Q(statut='delivered'))
        )
        
        # Commandes du mois
        month_orders = orders.filter(created__gte=month_start)
        month_stats = month_orders.aggregate(
            total=Count('id'),
            delivered=Count('id', filter=Q(statut='delivered')),
            revenue=Sum('provider_net_amount', filter=Q(statut='delivered'))
        )
        
        # Nouvelles commandes en attente
        pending_orders = orders.filter(
            statut__in=['pending', 'confirmed']
        ).order_by('-created')[:5]
        
        # Wallet summary
        wallet_summary = WalletService.get_wallet_summary(provider)
        
        # Checklist de configuration
        checklist = self._get_checklist(provider, settings)
        
        # Photo du provider (priorité: settings.logo > provider.photo_local)
        photo_url = None
        if settings.logo:
            photo_url = settings.logo.url if hasattr(settings.logo, 'url') else str(settings.logo)
        elif provider.photo_local:
            photo_url = provider.photo_local.url if hasattr(provider.photo_local, 'url') else str(provider.photo_local)
        
        return Response({
            'provider': {
                'id': str(provider.id),
                'name': settings.business_name or provider.nom_commercial,
                'is_open': settings.is_open,
                'type': provider.type,
                'type_display': provider.get_type_display(),
                'photo': photo_url,
                'ville': provider.ville,
                'adresse': provider.adresse,
            },
            'stats': {
                'today': {
                    'total_orders': today_stats['total'],
                    'pending_orders': today_stats['pending'],
                    'delivered_orders': today_stats['delivered'],
                    'revenue': today_stats['revenue'] or Decimal('0'),
                },
                'week': {
                    'total_orders': week_stats['total'],
                    'delivered_orders': week_stats['delivered'],
                    'revenue': week_stats['revenue'] or Decimal('0'),
                },
                'month': {
                    'total_orders': month_stats['total'],
                    'delivered_orders': month_stats['delivered'],
                    'revenue': month_stats['revenue'] or Decimal('0'),
                },
            },
            'wallet': {
                'balance': wallet_summary['balance'],
                'pending_balance': wallet_summary['pending_balance'],
                'total_earned': wallet_summary['total_earned'],
            },
            'pending_orders': [
                {
                    'id': str(o.id),
                    'numero': o.numero,
                    'client_name': o.client.get_full_name(),
                    'total': o.total_estime,
                    'statut': o.statut,
                    'statut_display': o.get_statut_display(),
                    'created': o.created,
                }
                for o in pending_orders
            ],
            'checklist': checklist,
        }, status=status.HTTP_200_OK)
    
    def _get_checklist(self, provider, settings) -> list:
        """
        Retourne la checklist de configuration pour le prestataire.
        """
        checklist = []
        
        # 1. Onboarding terminé
        checklist.append({
            'id': 'onboarding',
            'label': 'Configuration initiale',
            'description': 'Identité, services et paiement',
            'completed': settings.onboarding_completed,
            'required': True,
        })
        
        # 2. Photo de couverture
        has_photo = bool(settings.storefront_photo) or bool(provider.photo_local)
        checklist.append({
            'id': 'storefront_photo',
            'label': 'Photo de couverture',
            'description': 'Ajoutez une photo de votre établissement',
            'completed': has_photo,
            'required': False,
        })
        
        # 3. Logo
        checklist.append({
            'id': 'logo',
            'label': 'Logo',
            'description': 'Ajoutez votre logo pour plus de visibilité',
            'completed': bool(settings.logo),
            'required': False,
        })
        
        # 4. Compte de payout vérifié
        has_verified_payout = ProviderPayoutAccount.objects.filter(
            provider=provider,
            status='verified'
        ).exists()
        has_any_payout = ProviderPayoutAccount.objects.filter(
            provider=provider
        ).exists()
        checklist.append({
            'id': 'payout_account',
            'label': 'Compte Mobile Money',
            'description': 'Configurez votre compte pour recevoir les paiements',
            'completed': has_any_payout,
            'verified': has_verified_payout,
            'required': True,
        })
        
        # 5. Services configurés
        services_count = provider.services.filter(is_active=True).count()
        checklist.append({
            'id': 'services',
            'label': 'Services et tarifs',
            'description': f'{services_count} service(s) configuré(s)',
            'completed': services_count > 0,
            'count': services_count,
            'required': True,
        })
        
        # 6. Première commande
        first_order = Order.objects.filter(provider=provider).exists()
        checklist.append({
            'id': 'first_order',
            'label': 'Première commande',
            'description': 'Recevez votre première commande',
            'completed': first_order,
            'required': False,
        })
        
        # 7. Boutique ouverte
        checklist.append({
            'id': 'is_open',
            'label': 'Boutique en ligne',
            'description': 'Activez votre boutique pour recevoir des commandes',
            'completed': settings.is_open,
            'required': True,
        })
        
        return checklist


class DashboardStatsView(APIView):
    """
    GET /api/provider/dashboard/stats/
    
    Retourne les statistiques détaillées.
    
    Query params:
    - period: today, week, month, year (défaut: week)
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def get(self, request):
        provider, _ = require_provider_member(request)
        
        period = request.query_params.get('period', 'week')
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if period == 'today':
            start_date = today_start
        elif period == 'week':
            start_date = today_start - timedelta(days=today_start.weekday())
        elif period == 'month':
            start_date = today_start.replace(day=1)
        elif period == 'year':
            start_date = today_start.replace(month=1, day=1)
        else:
            start_date = today_start - timedelta(days=7)
        
        orders = Order.objects.filter(
            provider=provider,
            created__gte=start_date
        )
        
        # Stats par statut
        status_stats = orders.values('statut').annotate(
            count=Count('id'),
            total=Sum('total_final')
        )
        
        # Revenu total (commandes livrées)
        revenue = orders.filter(statut='delivered').aggregate(
            total=Sum('provider_net_amount'),
            commission=Sum('commission_amount'),
            count=Count('id')
        )
        
        # Taux de conversion (confirmées / total)
        total_orders = orders.count()
        confirmed_orders = orders.filter(
            statut__in=['confirmed', 'collected', 'in_progress', 'ready', 'delivered']
        ).count()
        conversion_rate = (confirmed_orders / total_orders * 100) if total_orders > 0 else 0
        
        # Taux d'annulation
        cancelled_orders = orders.filter(statut='cancelled').count()
        cancellation_rate = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0
        
        return Response({
            'period': period,
            'start_date': start_date,
            'end_date': now,
            'orders': {
                'total': total_orders,
                'by_status': {
                    item['statut']: {
                        'count': item['count'],
                        'total': item['total'] or Decimal('0')
                    }
                    for item in status_stats
                },
            },
            'revenue': {
                'total': revenue['total'] or Decimal('0'),
                'commission_paid': revenue['commission'] or Decimal('0'),
                'orders_count': revenue['count'] or 0,
            },
            'rates': {
                'conversion': round(conversion_rate, 1),
                'cancellation': round(cancellation_rate, 1),
            },
        }, status=status.HTTP_200_OK)


class ShareLinkView(APIView):
    """
    GET /api/provider/share-link/
    
    Retourne le lien de partage de la boutique du prestataire.
    """
    permission_classes = [permissions.IsAuthenticated, IsProviderMember]
    
    def get(self, request):
        provider, _ = require_provider_member(request)
        
        # Construire l'URL de la boutique
        from django.conf import settings as django_settings
        
        frontend_url = getattr(django_settings, 'FRONTEND_URL', 'https://presso.ci')
        shop_url = f"{frontend_url}/pressing/{provider.id}"
        
        # Message WhatsApp prédéfini
        try:
            business_name = provider.settings.business_name
        except ProviderSettings.DoesNotExist:
            business_name = provider.nom_commercial
        
        whatsapp_message = (
            f"🧺 Découvrez {business_name} sur Presso !\n\n"
            f"Commandez votre lessive en ligne et faites-vous livrer.\n\n"
            f"👉 {shop_url}"
        )
        
        # URL de partage WhatsApp
        import urllib.parse
        whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(whatsapp_message)}"
        
        return Response({
            'shop_url': shop_url,
            'whatsapp_url': whatsapp_url,
            'whatsapp_message': whatsapp_message,
            'qr_code_data': shop_url,  # À utiliser avec une lib QR code côté frontend
        }, status=status.HTTP_200_OK)
