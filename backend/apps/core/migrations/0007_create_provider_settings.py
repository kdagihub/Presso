from django.db import migrations


def create_provider_settings(apps, schema_editor):
    Provider = apps.get_model('providers', 'Provider')
    ProviderSettings = apps.get_model('core', 'ProviderSettings')
    for provider in Provider.objects.all():
        ProviderSettings.objects.get_or_create(
            provider=provider,
            defaults={
                'business_name': provider.nom_commercial,
                'notification_email': provider.user.email if provider.user else '',
                'notification_phone': provider.user.phone if provider.user else '',
            },
        )


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_seed_provider_permissions'),
        ('providers', '0004_alter_providerstaff_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(create_provider_settings, reverse_noop),
    ]
