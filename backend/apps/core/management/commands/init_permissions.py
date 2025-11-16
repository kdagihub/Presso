from django.core.management.base import BaseCommand
from apps.core.models import Permission


class Command(BaseCommand):
    help = 'Initialise les permissions de base pour le système multitenant Presso'

    def handle(self, *args, **options):
        permissions_data = [
            # Commandes
            {
                'code': 'view_orders',
                'name': 'Voir les commandes',
                'description': 'Permet de voir les commandes',
                'module': 'orders'
            },
            {
                'code': 'manage_orders',
                'name': 'Gérer les commandes',
                'description': 'Permet de créer, modifier et supprimer les commandes',
                'module': 'orders'
            },
            {
                'code': 'change_order_status',
                'name': 'Changer le statut des commandes',
                'description': 'Permet de modifier le statut des commandes',
                'module': 'orders'
            },
            
            # Services
            {
                'code': 'view_services',
                'name': 'Voir les services',
                'description': 'Permet de voir les services',
                'module': 'services'
            },
            {
                'code': 'manage_services',
                'name': 'Gérer les services',
                'description': 'Permet de créer, modifier et supprimer les services',
                'module': 'services'
            },
            
            # Tarifs
            {
                'code': 'view_tariffs',
                'name': 'Voir les tarifs',
                'description': 'Permet de voir les tarifs',
                'module': 'tariffs'
            },
            {
                'code': 'manage_tariffs',
                'name': 'Gérer les tarifs',
                'description': 'Permet de créer, modifier et supprimer les tarifs',
                'module': 'tariffs'
            },
            
            # Statistiques
            {
                'code': 'view_stats',
                'name': 'Voir les statistiques',
                'description': 'Permet de voir les statistiques et rapports',
                'module': 'stats'
            },
            {
                'code': 'export_stats',
                'name': 'Exporter les statistiques',
                'description': 'Permet d\'exporter les statistiques',
                'module': 'stats'
            },
            
            # Personnel
            {
                'code': 'view_staff',
                'name': 'Voir le personnel',
                'description': 'Permet de voir les membres du personnel',
                'module': 'staff'
            },
            {
                'code': 'manage_staff',
                'name': 'Gérer le personnel',
                'description': 'Permet de créer, modifier et supprimer les membres du personnel',
                'module': 'staff'
            },
            {
                'code': 'manage_roles',
                'name': 'Gérer les rôles',
                'description': 'Permet de créer et modifier les rôles personnalisés',
                'module': 'staff'
            },
            
            # Paramètres
            {
                'code': 'view_settings',
                'name': 'Voir les paramètres',
                'description': 'Permet de voir les paramètres',
                'module': 'settings'
            },
            {
                'code': 'manage_settings',
                'name': 'Gérer les paramètres',
                'description': 'Permet de modifier les paramètres du prestataire',
                'module': 'settings'
            },
            
            # Clients
            {
                'code': 'view_customers',
                'name': 'Voir les clients',
                'description': 'Permet de voir les clients',
                'module': 'customers'
            },
            {
                'code': 'manage_customers',
                'name': 'Gérer les clients',
                'description': 'Permet de gérer les clients',
                'module': 'customers'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for perm_data in permissions_data:
            permission, created = Permission.objects.update_or_create(
                code=perm_data['code'],
                defaults=perm_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Permission "{permission.name}" créée')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'○ Permission "{permission.name}" mise à jour')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Initialisation terminée : {created_count} créées, {updated_count} mises à jour')
        )

