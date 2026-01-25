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
    # Objets complets (pour compatibilité)
    article_type = serializers.SerializerMethodField()
    matiere = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()
    
    # Noms directs (pour le frontend)
    service_name = serializers.SerializerMethodField()
    article_type_name = serializers.SerializerMethodField()
    matiere_name = serializers.SerializerMethodField()
    
    # Aliases pour le frontend
    quantity = serializers.DecimalField(source='quantite', max_digits=8, decimal_places=2, read_only=True)
    unit_price = serializers.DecimalField(source='prix_unitaire', max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(source='total_ligne', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            # Objets complets
            'article_type',
            'matiere',
            'service',
            # Noms directs (frontend)
            'service_name',
            'article_type_name',
            'matiere_name',
            # Quantités et prix (aliases + originaux)
            'quantite',
            'quantity',
            'prix_unitaire',
            'unit_price',
            'total_ligne',
            'total_price',
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

    def get_service_name(self, obj) -> str:
        return obj.service.label if obj.service else ''

    def get_article_type_name(self, obj) -> str:
        return obj.article_type.nom if obj.article_type else ''

    def get_matiere_name(self, obj):
        return obj.matiere.nom if obj.matiere else None


class OrderSerializer(serializers.ModelSerializer):
    provider = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    client = serializers.SerializerMethodField()
    agency = serializers.SerializerMethodField()
    assigned_staff = serializers.SerializerMethodField()
    logs = serializers.SerializerMethodField()
    
    # Champs display pour le frontend
    statut_display = serializers.SerializerMethodField()
    payment_status_display = serializers.SerializerMethodField()
    payout_status_display = serializers.SerializerMethodField()
    
    # Champs OTP
    has_delivery_otp = serializers.SerializerMethodField()
    is_delivery_validated = serializers.SerializerMethodField()
    
    # Champs vérification à la collecte
    counting_mode_display = serializers.SerializerMethodField()
    verification_status = serializers.SerializerMethodField()
    has_adjustment = serializers.SerializerMethodField()
    
    # Champs réclamation client
    claim_status_display = serializers.SerializerMethodField()
    claim_reason_display = serializers.SerializerMethodField()
    claim_info = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'numero',
            # Statut
            'statut',
            'statut_display',
            'statut_changed_at',
            # Mode de comptage
            'counting_mode',
            'counting_mode_display',
            # Relations
            'client',
            'provider',
            'agency',
            'assigned_staff',
            # Adresses
            'adresse_collecte',
            'latitude_collecte',
            'longitude_collecte',
            'adresse_livraison',
            'latitude_livraison',
            'longitude_livraison',
            # Créneaux
            'creneau_collecte',
            'creneau_livraison',
            # Dates réelles
            'date_collecte',
            'date_livraison',
            # Montants
            'total_estime',
            'total_final',
            'frais_livraison',
            # Quantités estimées / vérifiées
            'estimated_weight',
            'estimated_pieces',
            'verified_weight',
            'verified_pieces',
            'quantity_verified_at',
            'verification_status',
            # Ajustement paiement
            'initial_amount_paid',
            'adjustment_amount',
            'adjustment_deadline',
            'adjustment_paid_at',
            'credit_issued',
            'client_accepted_reduction',
            'has_adjustment',
            # Paiement
            'payment_status',
            'payment_status_display',
            'payment_method',
            'paid_at',
            # Commission et montants calculés
            'commission_percent',
            'commission_amount',
            'payout_fee',
            'provider_net_amount',
            # OTP Livraison
            'has_delivery_otp',
            'delivery_otp_generated_at',
            'delivery_otp_validated_at',
            'is_delivery_validated',
            # Payout
            'payout_status',
            'payout_status_display',
            'payout_scheduled_at',
            'payout_completed_at',
            # Annulation
            'cancellation_reason',
            'cancellation_notes',
            'cancelled_at',
            # Réclamation client
            'claim_deadline',
            'claim_status',
            'claim_status_display',
            'claim_reason',
            'claim_reason_display',
            'claim_details',
            'claim_submitted_at',
            'claim_resolved_at',
            'claim_info',
            # Notes
            'notes_client',
            'notes_provider',
            # Timestamps
            'created',
            'updated',
            # Relations
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

    def get_statut_display(self, obj) -> str:
        """Retourne le libellé du statut en français"""
        return obj.get_statut_display()

    def get_payment_status_display(self, obj) -> str:
        """Retourne le libellé du statut de paiement en français"""
        return obj.get_payment_status_display()

    def get_payout_status_display(self, obj) -> str:
        """Retourne le libellé du statut de payout en français"""
        return obj.get_payout_status_display()

    def get_has_delivery_otp(self, obj) -> bool:
        """Indique si un OTP de livraison a été généré"""
        return bool(obj.delivery_otp)

    def get_is_delivery_validated(self, obj) -> bool:
        """Indique si la livraison a été validée par OTP"""
        return obj.delivery_otp_validated_at is not None
    
    def get_counting_mode_display(self, obj) -> str:
        """Retourne le libellé du mode de comptage"""
        return obj.get_counting_mode_display()
    
    def get_verification_status(self, obj) -> dict:
        """Retourne l'état de la vérification à la collecte"""
        return {
            'verified': obj.quantity_verified_at is not None,
            'verified_at': obj.quantity_verified_at,
            'estimated': {
                'weight': obj.estimated_weight,
                'pieces': obj.estimated_pieces,
            },
            'verified_values': {
                'weight': obj.verified_weight,
                'pieces': obj.verified_pieces,
            },
            'has_discrepancy': (
                obj.adjustment_amount is not None and 
                obj.adjustment_amount != 0
            ),
        }
    
    def get_has_adjustment(self, obj) -> bool:
        """Indique si un ajustement de paiement est requis ou a été effectué"""
        return obj.adjustment_amount is not None and obj.adjustment_amount != 0
    
    def get_claim_status_display(self, obj) -> str:
        """Retourne le libellé du statut de réclamation"""
        return obj.get_claim_status_display()
    
    def get_claim_reason_display(self, obj) -> str:
        """Retourne le libellé de la raison de réclamation"""
        if obj.claim_reason:
            return obj.get_claim_reason_display()
        return None
    
    def get_claim_info(self, obj) -> dict:
        """Retourne les informations complètes sur la réclamation"""
        # Vérifier si le client peut encore soumettre une réclamation
        can_submit, reason = obj.can_submit_claim()
        remaining_time = obj.get_claim_remaining_time()
        
        return {
            'can_submit_claim': can_submit,
            'submit_reason': reason if not can_submit else None,
            'remaining_time': remaining_time,
            'has_claim': obj.claim_status != 'none',
            'claim': {
                'status': obj.claim_status,
                'status_display': obj.get_claim_status_display(),
                'reason': obj.claim_reason,
                'reason_display': obj.get_claim_reason_display() if obj.claim_reason else None,
                'details': obj.claim_details,
                'photos': obj.claim_photos,
                'submitted_at': obj.claim_submitted_at,
                'resolved_at': obj.claim_resolved_at,
            } if obj.claim_status != 'none' else None,
        }

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
        
        # ═══════════════════════════════════════════════════════════════════
        # NOTIFICATION : Nouvelle commande pour le prestataire
        # ═══════════════════════════════════════════════════════════════════
        try:
            from apps.core.services.notification_dispatcher import notification_dispatcher
            notification_dispatcher.notify_provider_new_order(order)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erreur envoi notification nouvelle commande: {e}")
        
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


# ═══════════════════════════════════════════════════════════════════════════════
# VÉRIFICATION À LA COLLECTE
# ═══════════════════════════════════════════════════════════════════════════════

class CollectorVerifyQuantitySerializer(serializers.Serializer):
    """
    Serializer pour la vérification de quantité par le livreur.
    """
    verified_weight = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        allow_null=True,
        help_text="Poids réel constaté en kg"
    )
    verified_pieces = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        help_text="Nombre de pièces réel constaté"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Notes du livreur sur la vérification"
    )
    timeout_minutes = serializers.IntegerField(
        required=False,
        default=10,
        min_value=5,
        max_value=60,
        help_text="Délai accordé au client pour répondre (minutes)"
    )
    
    def validate(self, attrs):
        verified_weight = attrs.get('verified_weight')
        verified_pieces = attrs.get('verified_pieces')
        
        if verified_weight is None and verified_pieces is None:
            raise serializers.ValidationError(
                "Vous devez fournir soit le poids vérifié (verified_weight), "
                "soit le nombre de pièces vérifié (verified_pieces)."
            )
        
        if verified_weight is not None and verified_pieces is not None:
            raise serializers.ValidationError(
                "Fournissez uniquement l'un des deux : poids OU nombre de pièces, pas les deux."
            )
        
        return attrs


class ClientAdjustmentResponseSerializer(serializers.Serializer):
    """
    Serializer pour la réponse du client à l'ajustement.
    """
    payment_method = serializers.ChoiceField(
        choices=[
            ('orange_money', 'Orange Money'),
            ('mtn_momo', 'MTN Mobile Money'),
            ('moov_money', 'Moov Money'),
            ('wave', 'Wave'),
        ],
        required=False,
        help_text="Méthode de paiement pour le complément"
    )
