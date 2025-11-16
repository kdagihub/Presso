from django.core.management.base import BaseCommand
from apps.services.models import ServiceTemplate, ArticleTypeTemplate, MatiereTemplate


class Command(BaseCommand):
    help = 'Initialise les templates de services, articles et matières pour Presso'

    def handle(self, *args, **options):
        # Services templates
        services_data = [
            {
                'label': 'Lavage simple',
                'description': 'Lavage standard de vêtements',
                'mode_tarif': 'kg',
                'duree_estimee': 1440,  # 24h
                'icone': 'washing-machine'
            },
            {
                'label': 'Lavage + Repassage',
                'description': 'Lavage et repassage complets',
                'mode_tarif': 'kg',
                'duree_estimee': 2880,  # 48h
                'icone': 'iron'
            },
            {
                'label': 'Repassage seul',
                'description': 'Repassage uniquement',
                'mode_tarif': 'piece',
                'duree_estimee': 720,  # 12h
                'icone': 'iron'
            },
            {
                'label': 'Service Express',
                'description': 'Lavage express en moins de 24h',
                'mode_tarif': 'kg',
                'duree_estimee': 720,  # 12h
                'icone': 'fast-forward'
            },
            {
                'label': 'Nettoyage à sec',
                'description': 'Pour tissus délicats',
                'mode_tarif': 'piece',
                'duree_estimee': 2880,  # 48h
                'icone': 'droplet'
            },
        ]
        
        # Types d'articles templates
        articles_data = [
            {'nom': 'Chemise', 'description': 'Chemise homme/femme'},
            {'nom': 'Pantalon', 'description': 'Pantalon classique'},
            {'nom': 'Jean', 'description': 'Pantalon en denim'},
            {'nom': 'Robe', 'description': 'Robe femme'},
            {'nom': 'Costume', 'description': 'Costume complet'},
            {'nom': 'Veste', 'description': 'Veste / Blazer'},
            {'nom': 'T-shirt', 'description': 'T-shirt / Polo'},
            {'nom': 'Pull', 'description': 'Pull / Sweat'},
            {'nom': 'Manteau', 'description': 'Manteau / Pardessus'},
            {'nom': 'Jupe', 'description': 'Jupe femme'},
            {'nom': 'Short', 'description': 'Short / Bermuda'},
            {'nom': 'Linge de maison', 'description': 'Draps, serviettes, nappes'},
        ]
        
        # Matières templates
        matieres_data = [
            {'nom': 'Coton', 'description': 'Tissu en coton'},
            {'nom': 'Lin', 'description': 'Tissu en lin'},
            {'nom': 'Soie', 'description': 'Tissu en soie'},
            {'nom': 'Laine', 'description': 'Tissu en laine'},
            {'nom': 'Polyester', 'description': 'Tissu synthétique'},
            {'nom': 'Denim', 'description': 'Tissu jean'},
            {'nom': 'Cuir', 'description': 'Cuir véritable'},
            {'nom': 'Synthétique', 'description': 'Matière synthétique'},
        ]
        
        # Créer les services templates
        self.stdout.write(self.style.HTTP_INFO('\n=== SERVICES TEMPLATES ==='))
        services_created = 0
        for service_data in services_data:
            service, created = ServiceTemplate.objects.get_or_create(
                label=service_data['label'],
                defaults=service_data
            )
            if created:
                services_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Service template "{service.label}" créé')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'○ Service template "{service.label}" existe déjà')
                )
        
        # Créer les articles templates
        self.stdout.write(self.style.HTTP_INFO('\n=== ARTICLES TEMPLATES ==='))
        articles_created = 0
        for article_data in articles_data:
            article, created = ArticleTypeTemplate.objects.get_or_create(
                nom=article_data['nom'],
                defaults=article_data
            )
            if created:
                articles_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Article template "{article.nom}" créé')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'○ Article template "{article.nom}" existe déjà')
                )
        
        # Créer les matières templates
        self.stdout.write(self.style.HTTP_INFO('\n=== MATIÈRES TEMPLATES ==='))
        matieres_created = 0
        for matiere_data in matieres_data:
            matiere, created = MatiereTemplate.objects.get_or_create(
                nom=matiere_data['nom'],
                defaults=matiere_data
            )
            if created:
                matieres_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Matière template "{matiere.nom}" créée')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'○ Matière template "{matiere.nom}" existe déjà')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Initialisation terminée :'
                f'\n  - {services_created} services templates créés'
                f'\n  - {articles_created} articles templates créés'
                f'\n  - {matieres_created} matières templates créées'
            )
        )

