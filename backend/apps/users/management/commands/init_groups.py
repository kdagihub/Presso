from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Initialise les groupes Django pour Presso (client, pressing, fanico, livreur, admin)'

    def handle(self, *args, **options):
        groups = ['client', 'pressing', 'fanico', 'livreur', 'admin']
        
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Groupe "{group_name}" créé')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'○ Groupe "{group_name}" existe déjà')
                )
        
        self.stdout.write(
            self.style.SUCCESS('\n✓ Initialisation des groupes terminée !')
        )

