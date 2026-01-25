"""
Signals pour l'application providers.
Gère la création automatique des ressources liées aux prestataires.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.providers.models import Provider


@receiver(post_save, sender=Provider)
def create_provider_wallet(sender, instance, created, **kwargs):
    """
    Crée automatiquement un wallet pour chaque nouveau prestataire.
    """
    if created:
        from apps.core.models import ProviderWallet
        
        # Vérifier si le wallet n'existe pas déjà (par sécurité)
        if not hasattr(instance, 'wallet') or instance.wallet is None:
            ProviderWallet.objects.get_or_create(provider=instance)


@receiver(post_save, sender=Provider)
def create_provider_settings(sender, instance, created, **kwargs):
    """
    Crée automatiquement les settings pour chaque nouveau prestataire.
    """
    if created:
        from apps.core.models import ProviderSettings
        
        # Vérifier si les settings n'existent pas déjà
        if not hasattr(instance, 'settings') or instance.settings is None:
            ProviderSettings.objects.get_or_create(
                provider=instance,
                defaults={
                    'business_name': instance.nom_commercial,
                }
            )
