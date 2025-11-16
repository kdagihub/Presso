from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.providers.models import Provider
from .models import ProviderSettings


@receiver(post_save, sender=Provider)
def create_provider_settings(sender, instance, created, **kwargs):
    """
    Crée automatiquement les paramètres pour un nouveau prestataire
    """
    if created:
        ProviderSettings.objects.create(
            provider=instance,
            business_name=instance.nom_commercial
        )

