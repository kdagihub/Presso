"""Serializers pour l'onboarding des prestataires."""
from __future__ import annotations

from typing import Any, Optional
from decimal import Decimal

from rest_framework import serializers  # type: ignore

from apps.providers.models import Provider
from apps.core.models import ProviderSettings, ProviderPayoutAccount
from apps.services.models import Service, ServiceTemplate
from apps.tariffs.models import ProviderService as ProviderServiceLink


# =============================================================================
# ONBOARDING STATUS
# =============================================================================

class OnboardingStatusSerializer(serializers.Serializer):
    """Serializer pour le statut d'onboarding (lecture seule)."""
    completed = serializers.BooleanField(read_only=True)
    current_step = serializers.IntegerField(read_only=True)
    steps = serializers.DictField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True)
    
    # Données du provider pour le frontend
    provider_id = serializers.UUIDField(read_only=True)
    business_name = serializers.CharField(read_only=True)
    is_open = serializers.BooleanField(read_only=True)


# =============================================================================
# ÉTAPE 1 : IDENTITÉ DU PRESSING
# =============================================================================

class OnboardingIdentitySerializer(serializers.Serializer):
    """
    Étape 1 : Identité du pressing
    - Nom de la boutique
    - Localisation GPS
    - Logo / Photo de la devanture
    """
    business_name = serializers.CharField(
        max_length=200,
        help_text="Nom commercial du pressing"
    )
    
    # Localisation
    adresse = serializers.CharField(
        max_length=500,
        help_text="Adresse complète du pressing"
    )
    
    ville = serializers.CharField(
        max_length=120,
        help_text="Ville"
    )
    
    quartier = serializers.CharField(
        max_length=120,
        required=False,
        allow_blank=True,
        help_text="Quartier / Commune"
    )
    
    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
        help_text="Latitude GPS"
    )
    
    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
        help_text="Longitude GPS"
    )
    
    zone_couverture = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Quartiers ou communes desservis"
    )
    
    rayon_km = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text="Rayon de couverture en km"
    )
    
    # Images (optionnelles à l'étape 1, peuvent être ajoutées plus tard)
    logo = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Logo du pressing"
    )
    
    storefront_photo = serializers.ImageField(
        required=False,
        allow_null=True,
        help_text="Photo de la devanture"
    )
    
    def validate(self, attrs):
        # Si latitude est fournie, longitude doit l'être aussi
        lat = attrs.get('latitude')
        lng = attrs.get('longitude')
        if (lat is None) != (lng is None):
            raise serializers.ValidationError(
                "La latitude et la longitude doivent être fournies ensemble."
            )
        return attrs


# =============================================================================
# ÉTAPE 2 : SERVICES ET TARIFS
# =============================================================================

class OnboardingServiceItemSerializer(serializers.Serializer):
    """Un service avec son prix de base."""
    template_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="ID du template de service (optionnel)"
    )
    
    label = serializers.CharField(
        max_length=100,
        help_text="Nom du service (ex: Lavage, Repassage)"
    )
    
    mode_tarif = serializers.ChoiceField(
        choices=[('kg', 'Au kilogramme'), ('piece', 'Par pièce'), ('forfait', 'Forfait')],
        default='piece',
        help_text="Mode de tarification"
    )
    
    prix_base = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0'),
        help_text="Prix de base en FCFA"
    )
    
    delai = serializers.IntegerField(
        min_value=1,
        default=24,
        help_text="Délai de réalisation en heures"
    )


class OnboardingServicesSerializer(serializers.Serializer):
    """
    Étape 2 : Services et tarifs
    Au moins un service doit être configuré.
    """
    services = OnboardingServiceItemSerializer(
        many=True,
        min_length=1,
        help_text="Liste des services avec leurs tarifs"
    )
    
    def validate_services(self, value):
        if len(value) < 1:
            raise serializers.ValidationError(
                "Au moins un service doit être configuré."
            )
        
        # Vérifier les doublons de labels
        labels = [s['label'].lower().strip() for s in value]
        if len(labels) != len(set(labels)):
            raise serializers.ValidationError(
                "Les noms de services doivent être uniques."
            )
        
        return value


# =============================================================================
# ÉTAPE 3 : INFORMATIONS DE PAIEMENT
# =============================================================================

class OnboardingPayoutAccountSerializer(serializers.Serializer):
    """
    Étape 3 : Compte de paiement Mobile Money
    
    À ce stade, on enregistre simplement les informations.
    La vérification OTP sera faite séparément.
    """
    operator = serializers.ChoiceField(
        choices=[
            ('orange', 'Orange Money'),
            ('mtn', 'MTN Mobile Money'),
            ('moov', 'Moov Money'),
            ('wave', 'Wave'),
        ],
        help_text="Opérateur Mobile Money"
    )
    
    phone_number = serializers.CharField(
        max_length=20,
        help_text="Numéro de téléphone Mobile Money"
    )
    
    account_name = serializers.CharField(
        max_length=200,
        help_text="Nom du titulaire du compte"
    )
    
    def validate_phone_number(self, value):
        """
        Valide et normalise le numéro au format E.164.
        Accepte les formats ivoiriens courants :
        - 0712345678 (10 chiffres local)
        - +2250712345678 (avec indicatif)
        - 2250712345678 (sans +)
        - 07 12 34 56 78 (avec espaces)
        """
        # Nettoyer : garder uniquement les chiffres
        digits = ''.join(filter(str.isdigit, value))
        
        # Vérifier la longueur
        if len(digits) == 10:
            # Format local : 0712345678
            if not digits.startswith('0'):
                raise serializers.ValidationError(
                    "Numéro local invalide. Doit commencer par 0. Ex: 0712345678"
                )
            return f'+225{digits}'
        
        elif len(digits) == 12 and digits.startswith('225'):
            # Format avec indicatif sans + : 2250712345678
            return f'+{digits}'
        
        elif len(digits) == 13 and digits.startswith('225'):
            # Déjà en E.164 (cas rare mais possible)
            return f'+{digits}'
        
        else:
            raise serializers.ValidationError(
                "Format invalide. Utilisez : 0712345678, +2250712345678 ou 225 07 12 34 56 78"
            )


# =============================================================================
# SERIALIZERS DE LECTURE
# =============================================================================

class ProviderPayoutAccountReadSerializer(serializers.ModelSerializer):
    """Serializer pour la lecture des comptes de paiement."""
    operator_display = serializers.CharField(
        source='get_operator_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = ProviderPayoutAccount
        fields = [
            'id',
            'operator',
            'operator_display',
            'phone_number',
            'account_name',
            'is_primary',
            'status',
            'status_display',
            'verified_at',
            'created',
            'updated',
        ]
        read_only_fields = fields


class OnboardingCompleteResponseSerializer(serializers.Serializer):
    """Réponse après complétion de l'onboarding."""
    success = serializers.BooleanField()
    message = serializers.CharField()
    provider_id = serializers.UUIDField()
    business_name = serializers.CharField()
    is_open = serializers.BooleanField()
    services_count = serializers.IntegerField()
    payout_accounts_count = serializers.IntegerField()


# =============================================================================
# TOGGLE OUVERT/FERMÉ
# =============================================================================

class ProviderOpenStatusSerializer(serializers.Serializer):
    """Toggle l'état ouvert/fermé du pressing."""
    is_open = serializers.BooleanField(
        help_text="True pour ouvrir, False pour fermer"
    )
    
    closed_reason = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text="Raison de fermeture (optionnel)"
    )
    
    def validate(self, attrs):
        is_open = attrs.get('is_open')
        closed_reason = attrs.get('closed_reason', '')
        
        # Si on ouvre, on efface la raison de fermeture
        if is_open:
            attrs['closed_reason'] = ''
        
        return attrs
