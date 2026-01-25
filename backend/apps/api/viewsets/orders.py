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
    CollectorVerifyQuantitySerializer,
    ClientAdjustmentResponseSerializer,
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

    def patch(self, request, order_id):
        """Support PATCH pour le frontend"""
        return self._update_status(request, order_id)
    
    def post(self, request, order_id):
        """Support POST pour rétrocompatibilité"""
        return self._update_status(request, order_id)
    
    def _update_status(self, request, order_id):
        provider, _ = require_can_manage_orders(request)
        order = _get_provider_order_or_404(provider, order_id)
        serializer = ProviderOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['statut']
        comment = serializer.validated_data.get('comment', '')

        if new_status == order.statut:
            raise ValidationError({'statut': 'Le statut est déjà appliqué.'})
        
        # ═══════════════════════════════════════════════════════════════════
        # VALIDATION WORKFLOW : Règles métier Pressow
        # ═══════════════════════════════════════════════════════════════════
        
        # Statuts qui NÉCESSITENT un paiement effectué
        STATUTS_APRES_PAIEMENT = ['collected', 'in_progress', 'ready', 'delivered']
        
        # Statuts de paiement considérés comme "payé"
        PAIEMENT_EFFECTUE = ['paid', 'escrow', 'released']
        
        # Règle : On ne peut pas passer à collected/in_progress/ready/delivered 
        # si le paiement n'a pas été effectué
        if new_status in STATUTS_APRES_PAIEMENT:
            if order.payment_status not in PAIEMENT_EFFECTUE:
                raise ValidationError({
                    'statut': f"Impossible de passer à '{new_status}' : le client n'a pas encore payé. "
                              f"Statut paiement actuel : {order.get_payment_status_display()}."
                })
        
        # Règle : Transitions valides
        TRANSITIONS_VALIDES = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['collected', 'cancelled'],  # collected seulement si payé (vérifié ci-dessus)
            'collected': ['in_progress', 'cancelled'],
            'in_progress': ['ready', 'cancelled'],
            'ready': ['delivered', 'cancelled'],
            'delivered': [],  # Statut final
            'cancelled': [],  # Statut final
        }
        
        transitions_possibles = TRANSITIONS_VALIDES.get(order.statut, [])
        if new_status not in transitions_possibles:
            raise ValidationError({
                'statut': f"Transition invalide : '{order.get_statut_display()}' → '{new_status}'. "
                          f"Transitions possibles : {transitions_possibles or 'aucune (statut final)'}."
            })

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
        
        # ═══════════════════════════════════════════════════════════════════
        # NOTIFICATIONS : Changement de statut
        # ═══════════════════════════════════════════════════════════════════
        try:
            from apps.core.services.notification_dispatcher import notification_dispatcher
            
            # Récupérer le code OTP si commande prête (pour la notification)
            otp_code = None
            if new_status == 'ready':
                # L'OTP est déjà généré par le service, récupérer depuis la commande
                order.refresh_from_db()
                otp_code = order.delivery_otp
            
            # 1. Notifier le CLIENT du changement de statut
            notification_dispatcher.notify_client_order_status_changed(
                order=order,
                new_status=new_status,
                otp_code=otp_code
            )
            
            # 2. Notifier le PRESTATAIRE (confirmation de l'action)
            notification_dispatcher.notify_provider_status_confirmation(
                order=order,
                new_status=new_status
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erreur envoi notification changement statut: {e}")
        
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


# ═══════════════════════════════════════════════════════════════════════════════
# VÉRIFICATION À LA COLLECTE (Livreur)
# ═══════════════════════════════════════════════════════════════════════════════

class CollectorVerifyQuantityView(APIView):
    """
    Endpoint pour le livreur pour vérifier la quantité réelle à la collecte.
    
    POST /api/orders/<order_id>/verify-quantity/
    {
        "verified_weight": 7.5,  // ou
        "verified_pieces": 15,
        "notes": "Le client avait sous-estimé le poids"
    }
    
    Retourne les détails de la vérification et l'ajustement requis.
    """
    permission_classes = [CanManageOrders]
    
    def post(self, request, order_id):
        provider, staff = require_can_manage_orders(request)
        order = _get_provider_order_or_404(provider, order_id)
        
        # Vérifier que la commande est dans un état approprié
        if order.statut not in ['confirmed', 'collected']:
            raise ValidationError({
                'statut': f"La vérification n'est possible que pour les commandes confirmées ou collectées. "
                          f"Statut actuel: {order.get_statut_display()}"
            })
        
        # Vérifier que le paiement initial a été effectué
        if order.payment_status not in ['paid_pending_verification', 'paid', 'escrow']:
            raise ValidationError({
                'payment_status': f"Le client n'a pas encore payé. Statut paiement: {order.get_payment_status_display()}"
            })
        
        serializer = CollectorVerifyQuantitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Effectuer la vérification
        result = order.verify_quantity(
            verified_weight=data.get('verified_weight'),
            verified_pieces=data.get('verified_pieces'),
            verified_by=staff,
            adjustment_timeout_minutes=data.get('timeout_minutes', 10)
        )
        
        # Envoyer notification au client si ajustement requis
        if result['adjustment_needed']:
            try:
                from apps.core.services.notification_dispatcher import notification_dispatcher
                notification_dispatcher.notify_client_adjustment_required(
                    order=order,
                    adjustment_amount=result['adjustment_amount'],
                    deadline=result['deadline']
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Erreur notification ajustement: {e}")
        
        # Si le client a trop payé, créditer son portefeuille
        elif result['credit_issued'] > 0:
            try:
                order.issue_credit_to_client()
                from apps.core.services.notification_dispatcher import notification_dispatcher
                notification_dispatcher.notify_client_credit_issued(
                    order=order,
                    credit_amount=result['credit_issued']
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Erreur crédit client: {e}")
        
        # Inclure les infos de la commande mise à jour
        refreshed = _get_provider_order_or_404(provider, order_id)
        
        return Response({
            'verification': result,
            'order': OrderSerializer(refreshed, context={'include_logs': True}).data,
            'message': self._get_message(result)
        })
    
    def _get_message(self, result):
        if result['adjustment_needed']:
            return (
                f"Écart détecté. Le client doit payer {result['adjustment_amount']} FCFA supplémentaires "
                f"ou réduire son linge. Délai: {result['deadline'].strftime('%H:%M')}"
            )
        elif result['credit_issued'] > 0:
            return f"Le client a trop payé. Un crédit de {result['credit_issued']} FCFA a été ajouté à son portefeuille."
        else:
            return "Quantité vérifiée. L'estimation du client était correcte."


class CollectorConfirmCollectionView(APIView):
    """
    Endpoint pour le livreur pour confirmer la collecte après vérification.
    
    POST /api/orders/<order_id>/confirm-collection/
    
    Ne peut être appelé que si :
    - La quantité a été vérifiée
    - L'ajustement a été réglé (paiement ou réduction acceptée)
    """
    permission_classes = [CanManageOrders]
    
    def post(self, request, order_id):
        provider, _ = require_can_manage_orders(request)
        order = _get_provider_order_or_404(provider, order_id)
        
        # Vérifier que la commande est confirmée
        if order.statut != 'confirmed':
            raise ValidationError({
                'statut': f"La collecte ne peut être confirmée que pour les commandes confirmées. "
                          f"Statut actuel: {order.get_statut_display()}"
            })
        
        # Vérifier que la quantité a été vérifiée
        if not order.quantity_verified_at:
            raise ValidationError({
                'verification': "Vous devez d'abord vérifier la quantité avant de confirmer la collecte."
            })
        
        # Vérifier que le paiement est en ordre
        if order.payment_status == 'adjustment_required':
            # Vérifier si le délai est dépassé
            if order.check_adjustment_timeout():
                # La réduction automatique a été appliquée
                pass
            else:
                raise ValidationError({
                    'payment_status': "Le client doit d'abord compléter le paiement ou accepter la réduction."
                })
        
        # Passer à "collectée"
        previous_status = order.statut
        order.statut = 'collected'
        order.statut_changed_at = timezone.now()
        order.date_collecte = timezone.now()
        order.save(update_fields=['statut', 'statut_changed_at', 'date_collecte', 'updated'])
        
        order.log_status(
            event='status_change',
            previous_status=previous_status,
            new_status='collected',
            comment='Collecte confirmée après vérification',
            performed_by=request.user,
        )
        
        # Notifier le client
        try:
            from apps.core.services.notification_dispatcher import notification_dispatcher
            notification_dispatcher.notify_client_order_status_changed(
                order=order,
                new_status='collected'
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erreur notification collecte: {e}")
        
        refreshed = _get_provider_order_or_404(provider, order_id)
        return Response(OrderSerializer(refreshed, context={'include_logs': True}).data)


# ═══════════════════════════════════════════════════════════════════════════════
# RÉPONSE CLIENT À L'AJUSTEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class ClientAdjustmentStatusView(APIView):
    """
    Endpoint pour le client pour voir l'état de l'ajustement requis.
    
    GET /api/orders/<order_id>/adjustment/
    
    Retourne les détails de l'écart et les options disponibles.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, client=request.user)
        except Order.DoesNotExist:
            raise NotFound("Commande introuvable.")
        
        # Vérifier si un ajustement est en cours
        if order.payment_status != 'adjustment_required':
            return Response({
                'adjustment_required': False,
                'order': OrderSerializer(order).data
            })
        
        # Vérifier si le délai est dépassé
        timeout_passed = False
        if order.adjustment_deadline and timezone.now() > order.adjustment_deadline:
            timeout_passed = True
        
        return Response({
            'adjustment_required': True,
            'estimated': {
                'weight': order.estimated_weight,
                'pieces': order.estimated_pieces,
            },
            'verified': {
                'weight': order.verified_weight,
                'pieces': order.verified_pieces,
            },
            'initial_paid': order.initial_amount_paid,
            'new_total': order.total_estime,
            'adjustment_amount': order.adjustment_amount,
            'deadline': order.adjustment_deadline,
            'timeout_passed': timeout_passed,
            'options': {
                'can_pay': not timeout_passed,
                'can_reduce': True,
            },
            'order': OrderSerializer(order).data
        })


class ClientCompleteAdjustmentView(APIView):
    """
    Endpoint pour le client pour compléter le paiement de l'ajustement.
    
    POST /api/orders/<order_id>/adjustment/complete/
    {
        "payment_method": "orange_money"
    }
    
    Initie un nouveau paiement pour le montant de l'ajustement.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, client=request.user)
        except Order.DoesNotExist:
            raise NotFound("Commande introuvable.")
        
        # Vérifier que l'ajustement est requis
        if order.payment_status != 'adjustment_required':
            raise ValidationError({
                'payment_status': "Aucun ajustement n'est requis pour cette commande."
            })
        
        # Vérifier le délai
        if order.adjustment_deadline and timezone.now() > order.adjustment_deadline:
            raise ValidationError({
                'deadline': "Le délai pour compléter le paiement est dépassé. "
                           "Le livreur ne prendra que le linge correspondant au montant déjà payé."
            })
        
        serializer = ClientAdjustmentResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Initier le paiement de l'ajustement
        from apps.core.services.payment_gateway import PaymentGateway
        
        gateway = PaymentGateway()
        
        try:
            # Créer une transaction de paiement pour l'ajustement
            payment_result = gateway.initiate_payment(
                amount=order.adjustment_amount,
                customer_email=request.user.email or f"{request.user.phone}@presso.ci",
                customer_phone=request.user.phone,
                customer_name=request.user.get_full_name() or request.user.phone,
                description=f"Complément commande {order.numero}",
                metadata={
                    'order_id': str(order.id),
                    'order_numero': order.numero,
                    'payment_type': 'adjustment',
                    'original_amount': str(order.initial_amount_paid),
                    'adjustment_amount': str(order.adjustment_amount),
                }
            )
            
            return Response({
                'success': True,
                'payment': payment_result,
                'adjustment_amount': order.adjustment_amount,
                'message': f"Veuillez compléter le paiement de {order.adjustment_amount} FCFA"
            })
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erreur paiement ajustement: {e}")
            raise ValidationError({
                'payment': f"Erreur lors de l'initiation du paiement: {str(e)}"
            })


class ClientAcceptReductionView(APIView):
    """
    Endpoint pour le client pour accepter de réduire le linge.
    
    POST /api/orders/<order_id>/adjustment/reduce/
    
    Le livreur ne prendra que le linge correspondant au montant déjà payé.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, client=request.user)
        except Order.DoesNotExist:
            raise NotFound("Commande introuvable.")
        
        # Vérifier que l'ajustement est requis
        if order.payment_status != 'adjustment_required':
            raise ValidationError({
                'payment_status': "Aucun ajustement n'est requis pour cette commande."
            })
        
        # Appliquer la réduction
        result = order.accept_reduction()
        
        # Notifier le prestataire
        try:
            from apps.core.services.notification_dispatcher import notification_dispatcher
            notification_dispatcher.notify_provider_client_accepted_reduction(
                order=order,
                accepted_quantity=result['accepted_weight'] or result['accepted_pieces']
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erreur notification réduction: {e}")
        
        return Response({
            'success': True,
            'accepted_weight': result['accepted_weight'],
            'accepted_pieces': result['accepted_pieces'],
            'final_total': result['final_total'],
            'message': f"Vous avez accepté la réduction. Le livreur ne prendra que "
                      f"{result['accepted_weight'] or result['accepted_pieces']} "
                      f"{'kg' if result['accepted_weight'] else 'pièces'}.",
            'order': OrderSerializer(order).data
        })


# ═══════════════════════════════════════════════════════════════════════════════
# RÉCLAMATION CLIENT (Après livraison)
# ═══════════════════════════════════════════════════════════════════════════════

class ClientClaimStatusView(APIView):
    """
    Endpoint pour le client pour voir l'état de sa possibilité de réclamation.
    
    GET /api/orders/<order_id>/claim/
    
    Retourne le temps restant et si une réclamation peut être soumise.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, client=request.user)
        except Order.DoesNotExist:
            raise NotFound("Commande introuvable.")
        
        # Vérifier si une réclamation est possible
        can_submit, reason = order.can_submit_claim()
        remaining_time = order.get_claim_remaining_time()
        
        return Response({
            'order_id': str(order.id),
            'order_numero': order.numero,
            'statut': order.statut,
            'can_submit_claim': can_submit,
            'reason': reason if not can_submit else None,
            'remaining_time': remaining_time,
            'claim_status': order.claim_status,
            'claim_status_display': order.get_claim_status_display(),
            'existing_claim': {
                'reason': order.claim_reason,
                'reason_display': order.get_claim_reason_display() if order.claim_reason else None,
                'details': order.claim_details,
                'submitted_at': order.claim_submitted_at,
            } if order.claim_status != 'none' else None,
            'claim_reasons': [
                {'code': code, 'label': label}
                for code, label in Order.CLAIM_REASON_CHOICES
            ]
        })


class ClientSubmitClaimView(APIView):
    """
    Endpoint pour le client pour soumettre une réclamation.
    
    POST /api/orders/<order_id>/claim/
    {
        "reason": "damaged",
        "details": "Description du problème...",
        "photos": ["url1", "url2"]  // optionnel
    }
    
    Ne peut être appelé que dans les 30 minutes suivant la livraison.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, client=request.user)
        except Order.DoesNotExist:
            raise NotFound("Commande introuvable.")
        
        # Valider les données
        reason = request.data.get('reason', '').strip()
        details = request.data.get('details', '').strip()
        photos = request.data.get('photos', [])
        
        if not reason:
            raise ValidationError({'reason': "La raison de la réclamation est requise."})
        
        if not details:
            raise ValidationError({'details': "Veuillez décrire le problème rencontré."})
        
        if len(details) < 20:
            raise ValidationError({
                'details': "Veuillez fournir une description plus détaillée (minimum 20 caractères)."
            })
        
        # Vérifier que photos est une liste
        if not isinstance(photos, list):
            photos = []
        
        # Soumettre la réclamation
        try:
            result = order.submit_claim(
                reason=reason,
                details=details,
                photos=photos
            )
        except ValueError as e:
            raise ValidationError({'error': str(e)})
        
        # Notifier le prestataire et l'équipe Pressow
        try:
            from apps.core.services.notification_dispatcher import notification_dispatcher
            notification_dispatcher.notify_claim_submitted(
                order=order,
                reason=reason,
                details=details
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erreur notification réclamation: {e}")
        
        return Response({
            'success': True,
            'claim_status': order.claim_status,
            'claim_submitted_at': order.claim_submitted_at,
            'message': "Votre réclamation a été enregistrée. Notre équipe vous contactera dans les plus brefs délais.",
            'order': OrderSerializer(order).data
        })


# ═══════════════════════════════════════════════════════════════════════════════
# PORTEFEUILLE CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

class ClientWalletView(APIView):
    """
    Endpoint pour le client pour voir son portefeuille.
    
    GET /api/wallet/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        from apps.core.models import ClientWallet
        
        wallet = ClientWallet.get_or_create_for_user(request.user)
        
        # Récupérer les dernières transactions
        transactions = wallet.transactions.all()[:20]
        
        return Response({
            'balance': wallet.balance,
            'total_credited': wallet.total_credited,
            'total_used': wallet.total_used,
            'is_active': wallet.is_active,
            'transactions': [
                {
                    'id': str(t.id),
                    'type': t.transaction_type,
                    'type_display': t.get_transaction_type_display(),
                    'direction': t.direction,
                    'amount': t.amount,
                    'balance_after': t.balance_after,
                    'description': t.description,
                    'order_numero': t.order.numero if t.order else None,
                    'created': t.created,
                }
                for t in transactions
            ]
        })
