from __future__ import annotations

from django.db.models import Q  # type: ignore
from django.utils import timezone  # type: ignore
from rest_framework import permissions, status  # type: ignore
from rest_framework.exceptions import NotFound, ValidationError  # type: ignore
from rest_framework.response import Response  # type: ignore
from rest_framework.views import APIView  # type: ignore

from apps.orders.models import Order
from apps.api.permissions import (
    IsProviderMember,
    CanManageOrders,
    require_provider_member,
    require_can_manage_orders,
)
from apps.api.serializers.orders import (
    OrderCreateSerializer,
    OrderSerializer,
    ProviderOrderStatusSerializer,
    ProviderOrderAssignSerializer,
)


class OrderListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(client=request.user).order_by('-created').prefetch_related('items__article_type', 'items__matiere', 'items__service')
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, order_id):
        try:
            return Order.objects.prefetch_related('items__article_type', 'items__matiere', 'items__service').get(id=order_id, client=request.user)
        except Order.DoesNotExist as exc:
            raise permissions.PermissionDenied("Commande introuvable.") from exc

    def get(self, request, order_id):
        order = self.get_object(request, order_id)
        return Response(OrderSerializer(order).data)


def _provider_order_queryset():
    return Order.objects.select_related(
        'client',
        'agency',
        'assigned_staff__user',
    ).prefetch_related(
        'items__article_type',
        'items__matiere',
        'items__service',
        'status_logs__performed_by',
    )


def _get_provider_order_or_404(provider, order_id):
    try:
        return _provider_order_queryset().get(id=order_id, provider=provider)
    except Order.DoesNotExist as exc:
        raise NotFound("Commande introuvable.") from exc


class ProviderOrderListView(APIView):
    permission_classes = [IsProviderMember]

    def get(self, request):
        provider, _ = require_provider_member(request)
        queryset = _provider_order_queryset().filter(provider=provider).order_by('-created')

        statut = request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)

        agency_id = request.query_params.get('agency_id')
        if agency_id:
            queryset = queryset.filter(agency_id=agency_id)

        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search)
                | Q(client__first_name__icontains=search)
                | Q(client__last_name__icontains=search)
                | Q(client__phone__icontains=search)
            )

        limit = request.query_params.get('limit')
        try:
            limit_value = min(int(limit), 200) if limit else 50
        except ValueError:
            raise ValidationError({'limit': 'La limite doit être un entier.'})

        queryset = queryset[:limit_value]
        serializer = OrderSerializer(queryset, many=True)
        return Response(serializer.data)


class ProviderOrderDetailView(APIView):
    permission_classes = [IsProviderMember]

    def get(self, request, order_id):
        provider, _ = require_provider_member(request)
        order = _get_provider_order_or_404(provider, order_id)
        serializer = OrderSerializer(order, context={'include_logs': True})
        return Response(serializer.data)


class ProviderOrderStatusUpdateView(APIView):
    permission_classes = [CanManageOrders]

    def post(self, request, order_id):
        provider, _ = require_can_manage_orders(request)
        order = _get_provider_order_or_404(provider, order_id)
        serializer = ProviderOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['statut']
        comment = serializer.validated_data.get('comment', '')

        if new_status == order.statut:
            raise ValidationError({'statut': 'Le statut est déjà appliqué.'})

        previous_status = order.statut
        order.statut = new_status
        order.statut_changed_at = timezone.now()
        order.save(update_fields=['statut', 'statut_changed_at', 'updated'])
        order.log_status(
            event='status_change',
            previous_status=previous_status,
            new_status=new_status,
            comment=comment,
            performed_by=request.user,
        )
        refreshed = _get_provider_order_or_404(provider, order_id)
        return Response(OrderSerializer(refreshed, context={'include_logs': True}).data)


class ProviderOrderAssignView(APIView):
    permission_classes = [CanManageOrders]

    def post(self, request, order_id):
        provider, _ = require_can_manage_orders(request)
        order = _get_provider_order_or_404(provider, order_id)
        serializer = ProviderOrderAssignSerializer(data=request.data, context={'provider': provider})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        updated_fields = []
        if data.get('set_agency'):
            order.agency = data.get('agency')
            updated_fields.append('agency')

        if data.get('set_staff'):
            order.assigned_staff = data.get('staff')
            updated_fields.append('assigned_staff')

        if not updated_fields:
            raise ValidationError("Aucune modification à appliquer.")

        order.save(update_fields=updated_fields + ['updated'])
        order.log_status(
            event='assignment',
            previous_status=order.statut,
            new_status=order.statut,
            comment=data.get('comment', ''),
            performed_by=request.user,
        )
        refreshed = _get_provider_order_or_404(provider, order_id)
        return Response(OrderSerializer(refreshed, context={'include_logs': True}).data)
