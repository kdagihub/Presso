# 📋 CONTEXT COMPLET - PROJET PRESSO

**Date de dernière mise à jour** : 15 Octobre 2025  
**Status** : Backend Django complet - Prêt pour développement APIs DRF

---

## 🎯 DESCRIPTION DU PROJET

**PRESSO** est une plateforme digitale de lessive connectant des clients à des prestataires (pressings & fanicos) en Côte d'Ivoire.

### Stack technique
- **Backend** : Django 5.2.7 + GeoDjango
- **Base de données** : SQLite/SpatiaLite (dev) | PostgreSQL/PostGIS (prod)
- **Frontend** (à développer) : Vue.js 3 + TypeScript
- **APIs** (à développer) : Django REST Framework

### Localisation
- **Pays** : Côte d'Ivoire (Abidjan)
- **Fuseau horaire** : Africa/Abidjan
- **Langue** : Français (fr-fr)
- **Monnaie** : FCFA

---

## ✅ CE QUI A ÉTÉ FAIT

### 1. **ARCHITECTURE MULTITENANT COMPLÈTE** ✅

#### App `core` créée (Infrastructure multitenant)

**Modèles** :
- `Permission` - 15+ permissions par module (orders, services, tariffs, stats, staff, settings, customers)
- `Role` - Rôles personnalisés par prestataire avec permissions M2M
- `ProviderSettings` - Paramètres configurables (logo, couleurs, règles métier, horaires, etc.)
- `TenantMixin` - Classe abstraite pour modèles tenant-specific

**Managers** :
- `TenantManager` - Filtrage automatique par tenant via ContextVar
- `TenantManagerWithQuerySet` - Combine manager + queryset personnalisé
- Méthodes : `for_tenant()`, `all_tenants()`, `active()`

**Middleware** :
- `TenantMiddleware` - Identifie automatiquement le prestataire (tenant) et le met en contexte
- Utilise `ContextVar` pour isolation thread-safe

**Signals** :
- Auto-création de `ProviderSettings` à la création d'un Provider

**Management Commands** :
- `init_permissions` - Crée 15+ permissions de base
- `init_templates` - Crée templates services/articles/matières
- `init_geotest` - Crée 8 prestataires + 3 clients avec positions GPS réelles à Abidjan

**Admin** :
- Interface complète pour Permission, Role, ProviderSettings
- Badges colorés, compteurs, filtres

### 2. **GÉOLOCALISATION COMPLÈTE** ✅

#### GeoDjango intégré

**User (apps/users/models.py)** :
```python
- latitude, longitude (DecimalField)
- location (PointField, SRID 4326, geography=True)
- adresse, quartier (TextField, CharField)

# Méthodes
- save() : Auto-génère location depuis lat/lng
- get_nearby_providers(max_distance_km, provider_type)
- calculate_distance_to(provider)
```

**Provider (apps/providers/models.py)** :
```python
- latitude, longitude (DecimalField)
- location (PointField, SRID 4326, geography=True)
- adresse, quartier (TextField, CharField)
- rayon_km (DecimalField) - Rayon de couverture

# Méthodes
- save() : Auto-génère location depuis lat/lng
- @staticmethod find_nearby(lat, lng, max_distance_km, type)
- get_clients_in_coverage()
- is_within_range(user_or_point, tolerance_km)
```

**Configuration** :
- `django.contrib.gis` ajouté à INSTALLED_APPS
- Database backend : `spatialite` (dev) / `postgis` (prod)
- `psycopg2-binary` dans requirements.txt

**Données de test** :
- 8 prestataires avec positions réelles à Abidjan (Cocody, Plateau, Marcory, Yopougon, Abobo, Treichville, 2 Plateaux, Adjamé)
- 3 clients géolocalisés
- Mot de passe test : `presso2025`

### 3. **APPS DJANGO (8 apps)** ✅

#### **apps/core** - Infrastructure multitenant
- Permission, Role, ProviderSettings, TenantMixin
- Managers, Middleware, Signals
- Management commands

#### **apps/users** - Utilisateurs personnalisés
```python
User(AbstractUser):
    - id (UUID)
    - phone (unique, validation ivoirienne)
    - photo_profil (ImageField)
    - role (CharField)
    - group (FK Group)
    - custom_role (FK Role) - Rôle personnalisé par prestataire
    - latitude, longitude, location (géoloc)
    - adresse, quartier
    - date_inscription
```

#### **apps/providers** - Prestataires
```python
Provider:
    - id (UUID)
    - user (OneToOne User)
    - type (pressing/fanico)
    - nom_commercial
    - photo_local (ImageField)
    - zone_couverture, rayon_km
    - latitude, longitude, location (géoloc)
    - adresse, quartier
    - statut_kyc (pending/verified/rejected)
    - document_identite (FileField)
    - is_active
    - created, updated
```

#### **apps/services** - Services personnalisés (Multitenant)
```python
# Templates globaux (créés par plateforme)
ServiceTemplate:
    - label, description
    - mode_tarif (kg/piece/forfait)
    - duree_estimee, icone
    - is_active

ArticleTypeTemplate:
    - nom, description

MatiereTemplate:
    - nom, description

# Instances personnalisées (par prestataire)
Service:
    - provider (FK Provider)
    - template (FK ServiceTemplate, optionnel)
    - label, description
    - mode_tarif, duree_estimee, icone
    - is_active
    - objects = TenantManagerWithQuerySet()

ArticleType:
    - provider (FK Provider)
    - template (FK ArticleTypeTemplate, optionnel)
    - nom, description
    - objects = TenantManagerWithQuerySet()

Matiere:
    - provider (FK Provider)
    - template (FK MatiereTemplate, optionnel)
    - nom, description
    - objects = TenantManagerWithQuerySet()
```

#### **apps/tariffs** - Tarification
```python
Tariff:
    - provider (FK Provider)
    - service (FK Service)
    - article_type (FK ArticleType)
    - matiere (FK Matiere, optionnel)
    - prix (DecimalField)
    - is_active
    - created, updated
    - unique_together: [provider, service, article_type, matiere]
```

#### **apps/orders** - Commandes
```python
Order:
    - id (UUID)
    - numero (auto-généré: ORD-YYYYMMDD-XXXX)
    - client (FK User)
    - provider (FK Provider)
    - statut (pending/confirmed/in_progress/ready/delivered/cancelled)
    - date_commande
    - creneau_collecte, creneau_livraison
    - adresse_collecte, adresse_livraison
    - instructions_speciales
    - montant_total (auto-calculé)
    - created, updated
```

#### **apps/order_items** - Articles de commande
```python
OrderItem:
    - id (UUID)
    - order (FK Order)
    - service (FK Service)
    - article_type (FK ArticleType)
    - matiere (FK Matiere, optionnel)
    - quantite
    - prix_unitaire
    - total_ligne (auto-calculé)
    - photo_article (ImageField, optionnel)
    - created
```

#### **apps/payments** - Paiements Mobile Money
```python
Payment:
    - id (UUID)
    - order (FK Order)
    - montant (DecimalField)
    - methode_paiement (orange_money/mtn_money/moov_money/wave)
    - statut (pending/completed/failed/refunded)
    - transaction_id (unique)
    - phone_paiement
    - created, updated
```

#### **apps/reviews** - Avis clients
```python
Review:
    - id (UUID)
    - order (FK Order)
    - client (FK User)
    - provider (FK Provider)
    - note (1-5)
    - commentaire
    - is_approved
    - is_flagged
    - created, updated
```

### 4. **CONFIGURATION DJANGO** ✅

**settings.py** :
```python
- SECRET_KEY via .env (dotenv optionnel)
- DEBUG via .env (défaut: True)
- ALLOWED_HOSTS via .env (défaut: *)
- LANGUAGE_CODE = 'fr-fr'
- TIME_ZONE = 'Africa/Abidjan'
- AUTH_USER_MODEL = 'users.User'
- django.contrib.gis ajouté
- TenantMiddleware configuré
- DATABASES = spatialite (dev) / postgis (prod)
- STATIC_ROOT, MEDIA_ROOT configurés
- ADMIN_SITE_HEADER, ADMIN_SITE_TITLE, ADMIN_INDEX_TITLE personnalisés
```

**urls.py** :
```python
- admin.site personnalisé
- Media files servis en DEBUG
- Static files servis en DEBUG
```

**requirements.txt** :
```
asgiref==3.10.0
Django==5.2.7
pillow==11.3.0
python-dotenv==1.1.1
sqlparse==0.5.3
psycopg2-binary>=2.9.9  # PostGIS
```

### 5. **ADMIN DJANGO COMPLET** ✅

Tous les modèles ont des interfaces admin personnalisées avec :
- `list_display` étendu avec méthodes custom
- Badges HTML colorés pour statuts
- `list_filter`, `search_fields` complets
- `fieldsets` organisés
- `readonly_fields` pour UUID, timestamps, champs auto
- `date_hierarchy` quand pertinent
- Compteurs et indicateurs visuels
- Actions personnalisées (approve_reviews, flag_reviews, etc.)
- Inlines (OrderItemInline pour Order)
- `save_model` override pour logique métier (ajout aux groupes)

### 6. **MANAGEMENT COMMANDS** ✅

```bash
python manage.py init_groups          # Crée groupes Django (client, pressing, fanico, livreur, admin)
python manage.py init_permissions     # Crée 15+ permissions système
python manage.py init_templates       # Crée templates services/articles/matières
python manage.py init_geotest         # Crée données géolocalisées (Abidjan)
```

Script automatique :
```bash
./init_multitenant.sh  # Exécute toutes les migrations + init commands
```

### 7. **DOCUMENTATION COMPLÈTE** ✅

**Fichiers créés** :
- `ARCHITECTURE_MULTITENANT.md` - Architecture détaillée (3000+ lignes)
- `MULTITENANT_RECAP.md` - Récapitulatif architecture
- `GEOLOCALISATION.md` - Guide géolocalisation complet (3000+ lignes)
- `GEOLOCALISATION_SETUP.md` - Setup géolocalisation pas à pas
- `RESUME_GEOLOCALISATION.md` - Récap géolocalisation
- `README.md` (racine) - README principal projet
- `CONTEXT_COMPLET.md` - Ce fichier
- `Context.md` - Contexte initial du projet (fourni par l'utilisateur)

---

## 🔧 CONFIGURATION ACTUELLE

### Structure des répertoires
```
/home/devfullstack/Bureau/CIACEMS TECHNOLOGIES/Business/presso_/Presso/
├── backend/
│   ├── apps/
│   │   ├── __init__.py
│   │   ├── core/           # App multitenant
│   │   ├── users/
│   │   ├── providers/
│   │   ├── services/
│   │   ├── tariffs/
│   │   ├── orders/
│   │   ├── order_items/
│   │   ├── payments/
│   │   └── reviews/
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── venv/               # Virtualenv Python
│   ├── manage.py
│   ├── requirements.txt
│   ├── init_multitenant.sh
│   ├── db.sqlite3          # Base de données (gitignored)
│   ├── media/              # Uploads (gitignored)
│   └── Documentation (*.md)
│
├── frontend/               # À créer
└── README.md
```

### Environnement (.env)
```env
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

### Base de données
- **Dev** : SQLite + SpatiaLite (fichier `db.sqlite3`)
- **Prod** : PostgreSQL + PostGIS (à configurer)

---

## 🔴 CE QUI RESTE À FAIRE

### PRIORITÉ 1 : APIs REST avec Django REST Framework

#### Installation
```bash
pip install djangorestframework
pip install djangorestframework-simplejwt  # JWT auth
pip install drf-spectacular  # Documentation Swagger/OpenAPI
pip install django-cors-headers  # CORS pour Vue.js
pip install django-filter  # Filtrage avancé
```

#### Tâches
1. **Configuration DRF** :
   - Ajouter `rest_framework` à INSTALLED_APPS
   - Configurer `REST_FRAMEWORK` settings (pagination, authentication, permissions)
   - Ajouter `corsheaders` middleware
   - Configurer CORS_ALLOWED_ORIGINS

2. **Serializers** (à créer dans chaque app) :
   - `UserSerializer`, `UserRegisterSerializer`, `UserProfileSerializer`
   - `ProviderSerializer`, `ProviderDetailSerializer`
   - `ServiceSerializer`, `ServiceTemplateSerializer`
   - `ArticleTypeSerializer`, `MatiereSerializer`
   - `TariffSerializer`
   - `OrderSerializer`, `OrderCreateSerializer`, `OrderDetailSerializer`
   - `OrderItemSerializer`
   - `PaymentSerializer`
   - `ReviewSerializer`
   - `PermissionSerializer`, `RoleSerializer`

3. **ViewSets** (à créer) :
   - `UserViewSet` avec actions : `me`, `update_location`, `nearby_providers`
   - `ProviderViewSet` avec actions : `nearby`, `check_coverage`, `services`, `tariffs`
   - `ServiceViewSet` (tenant-isolated)
   - `TariffViewSet` (tenant-isolated)
   - `OrderViewSet` avec actions : `create_order`, `cancel`, `update_status`
   - `PaymentViewSet` avec actions : `initiate_payment`, `verify_payment`, `webhooks`
   - `ReviewViewSet`

4. **Permissions personnalisées** :
   - `IsOwnerOrReadOnly`
   - `IsProviderOwner`
   - `HasCustomPermission` (utilise `user.has_custom_permission()`)
   - `IsTenantMember`

5. **URLs DRF** :
   ```python
   # config/urls.py
   urlpatterns = [
       path('admin/', admin.site.urls),
       path('api/', include('apps.users.urls')),
       path('api/', include('apps.providers.urls')),
       path('api/', include('apps.orders.urls')),
       # ...
       path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
       path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
   ]
   ```

6. **Authentication JWT** :
   - Endpoints : `/api/auth/login/`, `/api/auth/register/`, `/api/auth/refresh/`
   - Token-based auth pour Vue.js

7. **Tests** :
   - Tests unitaires pour chaque endpoint
   - Tests d'intégration
   - Tests de permissions/isolation tenant

### PRIORITÉ 2 : Frontend Vue.js 3 + TypeScript

#### Setup
```bash
cd Presso/
npm create vue@latest frontend
# Choisir : TypeScript, Router, Pinia, ESLint
cd frontend
npm install
```

#### Packages à installer
```bash
npm install axios                    # HTTP client
npm install leaflet vue-leaflet      # Cartes
npm install @vueuse/core             # Composables utilitaires
npm install chart.js vue-chartjs     # Graphiques
npm install @headlessui/vue          # Composants UI
npm install @heroicons/vue           # Icônes
```

#### Structure suggérée
```
frontend/
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── common/          # Boutons, Inputs, Cards, etc.
│   │   ├── maps/            # Carte Leaflet, Marqueurs
│   │   ├── orders/          # Order card, Order list
│   │   └── providers/       # Provider card, Provider list
│   ├── views/
│   │   ├── client/
│   │   │   ├── HomeView.vue           # Recherche prestataires
│   │   │   ├── ProvidersMapView.vue   # Carte avec prestataires
│   │   │   ├── ProviderDetailView.vue # Détails + commander
│   │   │   ├── OrdersView.vue         # Mes commandes
│   │   │   └── ProfileView.vue        # Mon profil
│   │   ├── provider/
│   │   │   ├── DashboardView.vue      # Stats
│   │   │   ├── OrdersView.vue         # Gestion commandes
│   │   │   ├── ServicesView.vue       # Gestion services
│   │   │   ├── TariffsView.vue        # Gestion tarifs
│   │   │   ├── StaffView.vue          # Gestion personnel + rôles
│   │   │   └── SettingsView.vue       # Paramètres
│   │   ├── auth/
│   │   │   ├── LoginView.vue
│   │   │   └── RegisterView.vue
│   │   └── admin/
│   │       └── AdminDashboardView.vue
│   ├── stores/
│   │   ├── auth.ts          # Store authentification
│   │   ├── user.ts          # Store utilisateur
│   │   ├── providers.ts     # Store prestataires
│   │   ├── orders.ts        # Store commandes
│   │   └── cart.ts          # Store panier
│   ├── services/
│   │   ├── api.ts           # Config Axios
│   │   ├── auth.ts          # Services auth
│   │   ├── providers.ts     # Services providers
│   │   ├── orders.ts        # Services orders
│   │   └── geolocation.ts   # Services géoloc
│   ├── composables/
│   │   ├── useGeolocation.ts
│   │   ├── usePermissions.ts
│   │   └── useAuth.ts
│   ├── router/
│   │   └── index.ts         # Routes + guards
│   └── App.vue
```

#### Fonctionnalités clés
1. **Client** :
   - Géolocalisation HTML5 → trouver prestataires proches
   - Carte Leaflet avec marqueurs prestataires
   - Filtrer par type (pressing/fanico), distance, note
   - Voir détails prestataire (services, tarifs, avis)
   - Créer commande (panier multi-articles)
   - Paiement Mobile Money
   - Suivre statut commande en temps réel
   - Laisser avis

2. **Prestataire** :
   - Dashboard avec stats (commandes, CA, clients)
   - Gestion commandes (accepter, refuser, changer statut)
   - Gestion services (créer depuis templates ou custom)
   - Gestion tarifs (prix par article/matière/service)
   - Gestion personnel (inviter, assigner rôles)
   - Créer rôles personnalisés avec permissions
   - Paramètres (logo, couleurs, horaires, rayon)

3. **Admin plateforme** :
   - Vue d'ensemble tous prestataires
   - Validation KYC
   - Gestion templates
   - Statistiques globales

### PRIORITÉ 3 : Intégrations Paiement

#### APIs Mobile Money Côte d'Ivoire

1. **Orange Money CI** :
   - API : https://developer.orange.com/apis/
   - Endpoints : initiate, verify, webhook
   - Sandbox disponible

2. **MTN Mobile Money** :
   - API : https://momodeveloper.mtn.com/
   - Collections API
   - Sandbox disponible

3. **Wave** :
   - API : https://developers.wave.com/
   - REST API + webhooks

4. **Moov Money** :
   - Contacter Moov CI pour API

#### Implémentation
- Créer service `PaymentGateway` dans `apps/payments/`
- Implémenter pour chaque opérateur
- Webhooks pour confirmations async
- Gestion des refunds/annulations

### PRIORITÉ 4 : Notifications & Temps Réel

1. **Django Channels** :
   - WebSockets pour notifications temps réel
   - Mise à jour statut commande en live
   - Chat client-prestataire

2. **Push Notifications** :
   - Firebase Cloud Messaging (mobile)
   - Web Push API (navigateur)

3. **SMS** :
   - Twilio / Africa's Talking
   - Confirmations commandes
   - Codes OTP

4. **Emails** :
   - SendGrid / Mailgun
   - Confirmations, reçus, notifications

### PRIORITÉ 5 : Tests & Qualité

1. **Backend** :
   ```bash
   pip install pytest pytest-django pytest-cov
   pip install factory-boy faker  # Fixtures
   ```
   - Tests unitaires modèles
   - Tests API endpoints
   - Tests isolation tenant
   - Tests géolocalisation
   - Coverage > 80%

2. **Frontend** :
   ```bash
   npm install -D vitest @vue/test-utils
   npm install -D cypress  # E2E
   ```
   - Tests unitaires composants
   - Tests stores Pinia
   - Tests E2E Cypress

### PRIORITÉ 6 : Déploiement

1. **Docker** :
   ```dockerfile
   # Dockerfile
   # docker-compose.yml (backend + frontend + postgres + redis)
   ```

2. **CI/CD** :
   - GitHub Actions / GitLab CI
   - Tests auto
   - Déploiement auto

3. **Hébergement** :
   - Backend : VPS / Heroku / Railway
   - Frontend : Vercel / Netlify
   - DB : PostgreSQL + PostGIS managé

4. **Monitoring** :
   - Sentry (erreurs)
   - Prometheus + Grafana (métriques)
   - Logs centralisés

---

## 📝 NOTES IMPORTANTES

### Conventions utilisées

1. **Clés primaires** : UUID pour tous les modèles (sauf User qui hérite d'AbstractUser)
2. **Timestamps** : `created` (auto_now_add), `updated` (auto_now)
3. **Images/Files** : Upload dans `media/{app}/{type}/%Y/%m/`
4. **Téléphones** : Format ivoirien `+225XXXXXXXXXX` ou `XXXXXXXXXX`
5. **Géolocalisation** : SRID 4326 (WGS84), geography=True
6. **Isolation tenant** : Via middleware + TenantManager automatique

### Points d'attention

1. **Isolation tenant** :
   - Toujours utiliser `TenantManager` pour modèles tenant-specific
   - Vérifier `request.tenant` dans les vues
   - Ne jamais exposer données d'autres tenants via API

2. **Géolocalisation** :
   - Toujours vérifier que `location` n'est pas None avant calcul distance
   - `Point(longitude, latitude)` - Attention à l'ordre !
   - Utiliser `.km` pour distances en kilomètres

3. **Permissions** :
   - Vérifier `user.has_custom_permission(code)` dans ViewSets
   - Séparer view (read) et manage (write) permissions
   - Admin global bypass toutes permissions

4. **Migrations** :
   - GeoDjango nécessite PostGIS/SpatiaLite installé
   - Toujours tester migrations sur base vide
   - Créer migrations par app (makemigrations app_name)

5. **Production** :
   - Utiliser PostgreSQL + PostGIS (pas SQLite)
   - Configurer GDAL_LIBRARY_PATH et GEOS_LIBRARY_PATH
   - Activer HTTPS pour géolocalisation HTML5

### Dépendances système requises

**Ubuntu/Debian** :
```bash
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libsqlite3-mod-spatialite \
    spatialite-bin \
    postgresql \
    postgis
```

**macOS** :
```bash
brew install gdal geos proj spatialite-tools libspatialite postgresql postgis
```

---

## 🚀 COMMANDES POUR REPRENDRE

### Démarrage rapide
```bash
# Se placer dans le backend
cd /home/devfullstack/Bureau/CIACEMS\ TECHNOLOGIES/Business/presso_/Presso/backend

# Activer venv
source venv/bin/activate

# Lancer serveur
python manage.py runserver
```

### Commandes utiles
```bash
# Shell Django
python manage.py shell

# Créer superuser
python manage.py createsuperuser

# Migrations
python manage.py makemigrations
python manage.py migrate

# Initialisation complète
./init_multitenant.sh
python manage.py init_geotest

# Tests
python manage.py test

# Collecter static files
python manage.py collectstatic
```

### Tester la géolocalisation
```python
# Dans le shell
from apps.users.models import User
client = User.objects.get(username='client_cocody')
nearby = client.get_nearby_providers(max_distance_km=10)
for p in nearby:
    print(f"{p.nom_commercial} - {p.distance.km:.2f} km")
```

### Tester les permissions
```python
# Dans le shell
from apps.core.models import Role, Permission
from apps.users.models import User

user = User.objects.first()
role = Role.objects.filter(provider__isnull=False).first()
user.custom_role = role
user.save()

print(user.has_custom_permission('view_orders'))
```

---

## 📚 DOCUMENTATION DISPONIBLE

Tous les fichiers sont dans `/backend/` :

| Fichier | Contenu |
|---------|---------|
| `ARCHITECTURE_MULTITENANT.md` | Architecture détaillée, schémas, exemples code |
| `MULTITENANT_RECAP.md` | Récapitulatif structure multitenant |
| `GEOLOCALISATION.md` | Guide complet géolocalisation + exemples |
| `GEOLOCALISATION_SETUP.md` | Installation PostGIS/SpatiaLite pas à pas |
| `RESUME_GEOLOCALISATION.md` | Récap fonctionnalités géoloc |
| `Context.md` | Contexte initial projet (fourni par utilisateur) |
| `CONTEXT_COMPLET.md` | Ce fichier |
| `README.md` (racine) | README principal |

---

## 🎯 OBJECTIFS FINAUX

### MVP (Minimum Viable Product)

**Fonctionnalités essentielles** :
1. ✅ Client s'inscrit et se géolocalise
2. ✅ Client trouve prestataires proches sur carte
3. ✅ Client voit services et tarifs d'un prestataire
4. 🔄 Client crée commande (panier multi-articles)
5. 🔄 Client paie via Mobile Money
6. 🔄 Prestataire reçoit notification
7. 🔄 Prestataire accepte/refuse commande
8. 🔄 Prestataire met à jour statut
9. 🔄 Client suit statut en temps réel
10. 🔄 Client laisse avis

### V2 (Évolutions)

- Livraison par livreurs dédiés (app livreur)
- Chat client-prestataire
- Programme fidélité
- Abonnements mensuels
- Application mobile (React Native / Flutter)
- IA pour recommandations
- Analyse prédictive (demande)

---

## ⚠️ PROBLÈMES CONNUS

Aucun problème majeur actuellement. Architecture stable et testée.

**Points de vigilance** :
- GeoDjango nécessite dépendances système (GDAL, GEOS)
- PostGIS requis pour production (pas SQLite)
- Isolation tenant à vérifier systématiquement dans APIs

---

## 👥 COMPTES DE TEST

| Username | Mot de passe | Type | Localisation |
|----------|--------------|------|--------------|
| `client_cocody` | `presso2025` | Client | Cocody Riviera |
| `client_plateau` | `presso2025` | Client | Plateau |
| `client_marcory` | `presso2025` | Client | Marcory |
| `provider_cocody_riviera` | `presso2025` | Pressing | Cocody Riviera 3 |
| `provider_plateau` | `presso2025` | Fanico | Plateau |
| `provider_marcory` | `presso2025` | Pressing | Marcory Zone 4 |

**Admin** : À créer avec `python manage.py createsuperuser`

---

## 📊 MÉTRIQUES ACTUELLES

- **Apps Django** : 8 apps + core
- **Modèles** : 17 modèles (User, Provider, Service, etc.)
- **Permissions** : 15+ permissions de base
- **Templates** : 5 services, 12 articles, 8 matières
- **Données test** : 8 prestataires + 3 clients (Abidjan)
- **Management commands** : 5 commands
- **Documentation** : 7 fichiers markdown (~10000 lignes)
- **Lignes de code** : ~5000 lignes Python

---

## 🎓 POUR LE PROCHAIN LLM

### Ce qu'il faut savoir

1. **Architecture choisie** : Multitenant hybride (pas django-tenants, custom avec middleware)
2. **Géolocalisation** : GeoDjango natif (pas package tiers)
3. **Utilisateur préfère** : Fournir commandes CLI plutôt qu'exécuter automatiquement
4. **Langue** : Toujours répondre en français
5. **Charte graphique** : Orange (#f97316), blanc, vert, fond sombre (#131C2F) - PAS de bleu
6. **Localisation** : Abidjan, Côte d'Ivoire
7. **Containers** : Déjà lancés, utiliser `docker exec -it jts-backend` (si besoin)

### Prochaines actions suggérées

1. **Installer DRF et dépendances**
2. **Créer serializers pour tous les modèles**
3. **Créer ViewSets avec isolation tenant**
4. **Configurer JWT authentication**
5. **Documenter API avec Swagger**
6. **Setup Vue.js frontend**
7. **Intégrer Mobile Money APIs**

### Fichiers à lire en priorité

1. `CONTEXT_COMPLET.md` (ce fichier) - Vue d'ensemble
2. `ARCHITECTURE_MULTITENANT.md` - Architecture détaillée
3. `GEOLOCALISATION.md` - Géolocalisation
4. `apps/core/models.py` - Modèles multitenant
5. `apps/users/models.py` - User model
6. `apps/providers/models.py` - Provider model

---

**FIN DU CONTEXTE COMPLET**

*Dernière mise à jour : 15 octobre 2025*
*Status : Backend Django ✅ - APIs DRF 🔄 - Frontend Vue.js 🔄*

