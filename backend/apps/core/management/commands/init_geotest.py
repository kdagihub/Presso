from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from apps.providers.models import Provider
from apps.users.models import User
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Initialise des données de test avec géolocalisation (Abidjan)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer les données de test existantes'
        )

    def handle(self, *args, **options):
        # Positions réelles à Abidjan
        ABIDJAN_POSITIONS = {
            'cocody_riviera': {
                'name': 'Pressing Riviera Premium',
                'type': 'pressing',
                'latitude': 5.3599517,
                'longitude': -3.9598355,
                'quartier': 'Cocody Riviera 3',
                'adresse': 'Boulevard Latrille, Cocody Riviera 3, Abidjan'
            },
            'plateau': {
                'name': 'Fanico Plateau Express',
                'type': 'fanico',
                'latitude': 5.3238665,
                'longitude': -4.0084323,
                'quartier': 'Plateau',
                'adresse': 'Avenue Delafosse, Plateau, Abidjan'
            },
            'marcory': {
                'name': 'Pressing Marcory Zone 4',
                'type': 'pressing',
                'latitude': 5.2897848,
                'longitude': -3.9866547,
                'quartier': 'Marcory Zone 4',
                'adresse': 'Boulevard VGE, Marcory Zone 4, Abidjan'
            },
            'yopougon': {
                'name': 'Fanico Yop City',
                'type': 'fanico',
                'latitude': 5.3364208,
                'longitude': -4.0839411,
                'quartier': 'Yopougon',
                'adresse': 'Yopougon Niangon, Abidjan'
            },
            'abobo': {
                'name': 'Pressing Abobo Gare',
                'type': 'pressing',
                'latitude': 5.4242082,
                'longitude': -4.0159683,
                'quartier': 'Abobo Gare',
                'adresse': 'Abobo Gare, face marché, Abidjan'
            },
            'treichville': {
                'name': 'Fanico Treichville',
                'type': 'fanico',
                'latitude': 5.2846284,
                'longitude': -4.0042634,
                'quartier': 'Treichville',
                'adresse': 'Boulevard de Marseille, Treichville, Abidjan'
            },
            'cocody_deux_plateaux': {
                'name': 'Pressing 2 Plateaux',
                'type': 'pressing',
                'latitude': 5.3698,
                'longitude': -3.9912,
                'quartier': 'Cocody 2 Plateaux',
                'adresse': 'Vallon, 2 Plateaux, Abidjan'
            },
            'adjame': {
                'name': 'Fanico Adjamé',
                'type': 'fanico',
                'latitude': 5.3507,
                'longitude': -4.0216,
                'quartier': 'Adjamé',
                'adresse': 'Adjamé 220 Logements, Abidjan'
            }
        }
        
        if options['clear']:
            self.stdout.write(self.style.WARNING('🗑️  Suppression des données de test...'))
            Provider.objects.filter(nom_commercial__contains='Test').delete()
            User.objects.filter(username__startswith='test_').delete()
            self.stdout.write(self.style.SUCCESS('✓ Données supprimées'))
            return
        
        self.stdout.write(self.style.HTTP_INFO('\n=== INITIALISATION GÉOLOCALISATION ===\n'))
        
        # Créer les groupes si nécessaire
        pressing_group, _ = Group.objects.get_or_create(name='pressing')
        fanico_group, _ = Group.objects.get_or_create(name='fanico')
        client_group, _ = Group.objects.get_or_create(name='client')
        
        providers_created = 0
        
        # Créer les prestataires
        for key, data in ABIDJAN_POSITIONS.items():
            # Créer l'utilisateur du prestataire
            username = f"provider_{key}"
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@presso.ci',
                    'phone': f'+225{str(providers_created).zfill(10)}',
                    'first_name': data['name'].split()[0],
                    'last_name': data['name'].split()[-1],
                    'group': pressing_group if data['type'] == 'pressing' else fanico_group
                }
            )
            
            if user_created:
                user.set_password('presso2025')
                user.save()
            
            # Créer le prestataire
            provider, created = Provider.objects.get_or_create(
                nom_commercial=data['name'],
                defaults={
                    'user': user,
                    'type': data['type'],
                    'latitude': data['latitude'],
                    'longitude': data['longitude'],
                    'quartier': data['quartier'],
                    'adresse': data['adresse'],
                    'zone_couverture': f"{data['quartier']} et environs",
                    'rayon_km': 5.0,
                    'statut_kyc': 'verified',
                    'is_active': True
                }
            )
            
            if created:
                providers_created += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ {data["name"]} créé à {data["quartier"]} '
                        f'({data["latitude"]:.4f}, {data["longitude"]:.4f})'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'○ {data["name"]} existe déjà')
                )
        
        # Créer quelques clients de test
        self.stdout.write(self.style.HTTP_INFO('\n=== CLIENTS TEST ===\n'))
        
        clients_positions = [
            ('client_cocody', 'Jean', 'Kouassi', 5.3599517, -3.9598355, 'Cocody Riviera'),
            ('client_plateau', 'Marie', 'Bamba', 5.3238665, -4.0084323, 'Plateau'),
            ('client_marcory', 'Koffi', 'Yao', 5.2897848, -3.9866547, 'Marcory'),
        ]
        
        clients_created = 0
        for username, first, last, lat, lng, quartier in clients_positions:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'phone': f'+225{str(100 + clients_created).zfill(10)}',
                    'first_name': first,
                    'last_name': last,
                    'group': client_group,
                    'latitude': lat,
                    'longitude': lng,
                    'quartier': quartier,
                    'adresse': f'{quartier}, Abidjan'
                }
            )
            
            if created:
                user.set_password('presso2025')
                user.save()
                clients_created += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Client {first} {last} créé à {quartier}')
                )
        
        # Afficher un résumé avec distances
        self.stdout.write(self.style.HTTP_INFO('\n=== RÉSUMÉ DES DISTANCES ===\n'))
        
        client = User.objects.filter(username='client_cocody').first()
        if client and client.location:
            nearby = client.get_nearby_providers(max_distance_km=10)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n📍 Prestataires proches de {client.get_full_name()} ({client.quartier}) :\n'
                )
            )
            
            for provider in nearby[:5]:
                distance = provider.distance.km
                icon = '🔵' if provider.type == 'pressing' else '🟠'
                self.stdout.write(
                    f'  {icon} {provider.nom_commercial} - {distance:.2f} km'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Initialisation terminée :'
                f'\n  - {providers_created} prestataires créés'
                f'\n  - {clients_created} clients créés'
                f'\n  - Mot de passe par défaut : presso2025'
            )
        )
        
        self.stdout.write(
            self.style.WARNING(
                f'\n💡 Testez avec :'
                f'\n  python manage.py shell'
                f'\n  >>> from apps.users.models import User'
                f'\n  >>> client = User.objects.get(username="client_cocody")'
                f'\n  >>> nearby = client.get_nearby_providers(max_distance_km=10)'
                f'\n  >>> for p in nearby: print(f"{{p.nom_commercial}} - {{p.distance.km:.2f}} km")'
            )
        )

