from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers  # type: ignore

from apps.order_items.models import OrderItem
from apps.orders.models import Order, OrderStatusLog
from apps.providers.models import Provider, ProviderAgency, ProviderStaff
from apps.services.models import ArticleType, Matiere
from apps.tariffs.models import ProviderService as ProviderServiceLink, Tariff


class OrderItemInputSerializer(serializers.Serializer):
    provider_service_id = serializers.UUIDField()
    article_type_id = serializers.UUIDField()
    matiere_id = serializers.UUIDField(required=False, allow_null=True)
    quantity = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal('0.1'))


class OrderItemSerializer(serializers.ModelSerializer):
    article_type = serializers.SerializerMethodField()
    matiere = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'article_type',
            'matiere',
            'service',
            'quantite',
            'prix_unitaire',
            'total_ligne',
            'notes',
            'created',
        ]

    def get_article_type(self, obj):
        return {'id': str(obj.article_type.id), 'nom': obj.article_type.nom}

    def get_matiere(self, obj):
        if obj.matiere:
            return {'id': str(obj.matiere.id), 'nom': obj.matiere.nom}
        return None

    def get_service(self, obj):
        return {'id': str(obj.service.id), 'label': obj.service.label, 'mode_tarif': obj.service.mode_tarif}


class OrderSerializer(serializers.ModelSerializer):
    provider = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    client = serializers.SerializerMethodField()
    agency = serializers.SerializerMethodField()
    assigned_staff = serializers.SerializerMethodField()
    logs = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'numero',
            'statut',
            'statut_changed_at',
            'client',
            'provider',
            'agency',
            'assigned_staff',
            'adresse_collecte',
            'adresse_livraison',
            'creneau_collecte',
            'creneau_livraison',
            'total_estime',
            'total_final',
            'frais_livraison',
            'notes_client',
            'notes_provider',
            'created',
            'updated',
            'items',
            'logs',
        ]

    def get_provider(self, obj):
        return {
            'id': str(obj.provider.id),
            'nom_commercial': obj.provider.nom_commercial,
        }

    def get_client(self, obj):
        return {
            'id': str(obj.client.id),
            'nom': obj.client.get_full_name() or obj.client.username,
            'phone': obj.client.phone,
        }

    def get_agency(self, obj):
        if not obj.agency:
            return None
        return {
            'id': str(obj.agency.id),
            'name': obj.agency.name,
            'ville': obj.agency.ville,
            'is_default': obj.agency.is_default,
        }

    def get_assigned_staff(self, obj):
        staff = obj.assigned_staff
        if not staff:
            return None
        return {
            'id': str(staff.id),
            'name': staff.user.get_full_name() if staff.user else '',
            'system_role': staff.system_role,
            'status': staff.status,
        }

    def get_logs(self, obj):
        if not self.context.get('include_logs'):
            return None
        logs = OrderStatusLogSerializer(obj.status_logs.all(), many=True)
        return logs.data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self.context.get('include_logs'):
            data.pop('logs', None)
        return data


class OrderCreateSerializer(serializers.Serializer):
    provider_id = serializers.UUIDField()
    agency_id = serializers.UUIDField(required=False, allow_null=True)
    adresse_collecte = serializers.CharField()
    adresse_livraison = serializers.CharField()
    latitude_collecte = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude_collecte = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    latitude_livraison = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude_livraison = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    creneau_collecte = serializers.DateTimeField()
    notes_client = serializers.CharField(required=False, allow_blank=True)
    frais_livraison = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=Decimal('0.00'))
    items = OrderItemInputSerializer(many=True)

    def validate(self, attrs):
        request = self.context['request']
        try:
            provider = Provider.objects.get(id=attrs['provider_id'], is_active=True)
        except Provider.DoesNotExist as exc:
            raise serializers.ValidationError({'provider_id': 'Prestataire introuvable.'}) from exc

        agency = None
        agency_id = attrs.get('agency_id')
        if agency_id:
            try:
                agency = ProviderAgency.objects.get(id=agency_id, provider=provider, is_active=True)
            except ProviderAgency.DoesNotExist as exc:
                raise serializers.ValidationError({'agency_id': "Agence introuvable ou inactive pour ce prestataire."}) from exc

        if not attrs.get('items'):
            raise serializers.ValidationError({'items': 'La commande doit contenir au moins un article.'})

        frais = attrs.get('frais_livraison') or Decimal('0.00')
        items_data = []
        items_total = Decimal('0.00')

        for raw_item in attrs['items']:
            provider_service = self._get_provider_service(provider, raw_item['provider_service_id'])
            article_type = self._get_article_type(provider, raw_item['article_type_id'])
            matiere = self._get_matiere(provider, raw_item.get('matiere_id'))
            quantity = raw_item['quantity']
            unit_price = self._resolve_tariff(provider, provider_service.service, article_type, matiere)
            line_total = (unit_price * quantity).quantize(Decimal('0.01'))

            items_data.append({
                'provider_service': provider_service,
                'service': provider_service.service,
                'article_type': article_type,
                'matiere': matiere,
                'quantity': quantity,
                'unit_price': unit_price,
                'line_total': line_total,
            })
            items_total += line_total

        attrs['provider'] = provider
        attrs['client'] = request.user
        attrs['items_data'] = items_data
        attrs['items_total'] = items_total
        attrs['frais_livraison'] = frais
        attrs['agency'] = agency
        return attrs

    def _get_provider_service(self, provider, provider_service_id):
        try:
            return ProviderServiceLink.objects.select_related('service').get(
                id=provider_service_id,
                provider=provider,
                is_available=True,
            )
        except ProviderServiceLink.DoesNotExist as exc:
            raise serializers.ValidationError({'items': 'Service indisponible pour ce prestataire.'}) from exc

    def _get_article_type(self, provider, article_type_id):
        try:
            return ArticleType.objects.get(id=article_type_id, provider=provider)
        except ArticleType.DoesNotExist as exc:
            raise serializers.ValidationError({'items': "Type d'article invalide."}) from exc

    def _get_matiere(self, provider, matiere_id):
        if not matiere_id:
            return None
        try:
            return Matiere.objects.get(id=matiere_id, provider=provider)
        except Matiere.DoesNotExist as exc:
            raise serializers.ValidationError({'items': 'Matière invalide.'}) from exc

    def _resolve_tariff(self, provider, service, article_type, matiere):
        qs = Tariff.objects.filter(provider=provider, service=service, article_type=article_type)
        if matiere:
            tariff = qs.filter(matiere=matiere).first()
            if tariff:
                return tariff.prix
        tariff = qs.filter(matiere__isnull=True).first()
        if tariff:
            return tariff.prix
        raise serializers.ValidationError({'items': 'Tarif indisponible pour cet article.'})

    def create(self, validated_data):
        provider = validated_data['provider']
        client = validated_data['client']
        items_data = validated_data['items_data']
        items_total = validated_data['items_total']
        frais = validated_data['frais_livraison']

        order = Order.objects.create(
            client=client,
            provider=provider,
            adresse_collecte=validated_data['adresse_collecte'],
            adresse_livraison=validated_data['adresse_livraison'],
            latitude_collecte=validated_data.get('latitude_collecte'),
            longitude_collecte=validated_data.get('longitude_collecte'),
            latitude_livraison=validated_data.get('latitude_livraison'),
            longitude_livraison=validated_data.get('longitude_livraison'),
            creneau_collecte=validated_data['creneau_collecte'],
            notes_client=validated_data.get('notes_client', ''),
            frais_livraison=frais,
            agency=validated_data.get('agency'),
        )

        for item in items_data:
            OrderItem.objects.create(
                order=order,
                article_type=item['article_type'],
                matiere=item['matiere'],
                service=item['service'],
                quantite=item['quantity'],
                prix_unitaire=item['unit_price'],
                total_ligne=item['line_total'],
            )

        order.total_estime = (items_total + frais).quantize(Decimal('0.01'))
        order.save(update_fields=['total_estime', 'frais_livraison', 'updated'])
        order.log_status(
            event='creation',
            new_status=order.statut,
            previous_status=None,
            performed_by=client,
            comment='Commande créée par le client',
        )
        if validated_data.get('agency'):
            order.log_status(
                event='assignment',
                new_status=order.statut,
                previous_status=order.statut,
                comment="Agence sélectionnée par le client",
                performed_by=client,
            )
        return order


class OrderStatusLogSerializer(serializers.ModelSerializer):
    performed_by = serializers.SerializerMethodField()

    class Meta:
        model = OrderStatusLog
        fields = [
            'id',
            'event',
            'previous_status',
            'new_status',
            'comment',
            'performed_by',
            'created',
        ]

    def get_performed_by(self, obj):
        if not obj.performed_by:
            return None
        return {
            'id': str(obj.performed_by.id),
            'nom': obj.performed_by.get_full_name() or obj.performed_by.username,
            'phone': obj.performed_by.phone,
        }


class ProviderOrderStatusSerializer(serializers.Serializer):
    statut = serializers.ChoiceField(choices=Order.STATUT_CHOICES)
    comment = serializers.CharField(required=False, allow_blank=True)


class ProviderOrderAssignSerializer(serializers.Serializer):
    agency_id = serializers.UUIDField(required=False, allow_null=True)
    staff_id = serializers.UUIDField(required=False, allow_null=True)
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        provider: Provider = self.context['provider']
        set_agency = 'agency_id' in self.initial_data
        set_staff = 'staff_id' in self.initial_data
        if not set_agency and not set_staff:
            raise serializers.ValidationError("Précisez au moins l'agence ou le staff à affecter.")

        agency = None
        if set_agency:
            agency_id = attrs.get('agency_id')
            if agency_id is None:
                agency = None
            else:
                try:
                    agency = ProviderAgency.objects.get(id=agency_id, provider=provider, is_active=True)
                except ProviderAgency.DoesNotExist as exc:
                    raise serializers.ValidationError({'agency_id': "Agence introuvable ou inactive."}) from exc

        staff_member = None
        if set_staff:
            staff_id = attrs.get('staff_id')
            if staff_id is None:
                staff_member = None
            else:
                try:
                    staff_member = ProviderStaff.objects.get(id=staff_id, provider=provider, status='active')
                except ProviderStaff.DoesNotExist as exc:
                    raise serializers.ValidationError({'staff_id': "Membre du staff introuvable ou inactif."}) from exc

        attrs['agency'] = agency
        attrs['staff'] = staff_member
        attrs['set_agency'] = set_agency
        attrs['set_staff'] = set_staff
        return attrs
