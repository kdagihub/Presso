from django.db import migrations

PERMISSIONS = [
    ('orders.view', 'Voir les commandes', 'orders', 'Consulter les commandes'),
    ('orders.manage', 'Gérer les commandes', 'orders', 'Accepter, mettre à jour et livrer les commandes'),
    ('services.view', 'Voir le catalogue', 'services', 'Consulter les services et articles'),
    ('services.manage', 'Gérer le catalogue', 'services', 'Créer et mettre à jour les services'),
    ('tariffs.manage', 'Gérer les tarifs', 'tariffs', 'Configurer les tarifs personnalisés'),
    ('customers.view', 'Voir les clients', 'customers', 'Consulter les informations clients'),
    ('staff.manage', 'Gérer le staff', 'staff', "Inviter et administrer l'équipe"),
    ('settings.manage', 'Gérer les paramètres', 'settings', 'Modifier les paramètres du prestataire'),
    ('stats.view', 'Voir les statistiques', 'stats', 'Consulter les statistiques et rapports'),
]


def seed_permissions(apps, schema_editor):
    Permission = apps.get_model('core', 'Permission')
    for code, name, module, description in PERMISSIONS:
        Permission.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'module': module,
                'description': description,
                'is_active': True,
            },
        )


def unseed_permissions(apps, schema_editor):
    Permission = apps.get_model('core', 'Permission')
    Permission.objects.filter(code__in=[code for code, *_ in PERMISSIONS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_delete_otpcode'),
    ]

    operations = [
        migrations.RunPython(seed_permissions, unseed_permissions),
    ]
