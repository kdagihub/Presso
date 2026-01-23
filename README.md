# 🧺 PRESSO - Plateforme de Lessive Digitale

Plateforme moderne de pressing et laundry en Côte d'Ivoire, développée par **CIACEMS Technologies**.

---

## 📁 Structure du Projet

```
Presso/
├── backend/                    # Django REST API
│   ├── apps/                   # Applications Django
│   │   ├── core/              # Core multitenant + tasks Celery
│   │   ├── api/               # API REST centralisée (serializers, viewsets)
│   │   ├── users/             # Gestion utilisateurs
│   │   ├── providers/         # Prestataires (pressings, fanico)
│   │   ├── services/          # Services & articles
│   │   ├── tariffs/           # Tarification
│   │   ├── orders/            # Commandes
│   │   ├── order_items/       # Détails commandes
│   │   ├── payments/          # Paiements Mobile Money
│   │   └── reviews/           # Avis clients
│   ├── config/                # Configuration Django
│   │   ├── settings.py        # Settings (lecture .env)
│   │   ├── celery.py          # Config Celery (toutes les apps)
│   │   ├── urls.py            # URLs principales
│   │   └── wsgi.py
│   ├── .env.example           # Template variables d'environnement
│   ├── .env                   # Variables d'environnement (à créer)
│   ├── Dockerfile             # Image Docker backend
│   ├── requirements.txt       # Dépendances Python
│   └── manage.py
│
├── frontend/                   # Vue.js 3 (à venir)
│
├── docker-compose.yml          # Orchestration Docker (racine)
├── Makefile                    # Commandes simplifiées (racine)
└── README.md                   # Ce fichier
```

---

## 🏗️ Architecture Technique

### Backend
- **Framework** : Django 5.2.7 + Django REST Framework
- **Base de données** : PostgreSQL 16 + PostGIS (géolocalisation)
- **Cache** : Redis 7 (cache, JWT blacklist, Celery broker)
- **Tâches async** : Celery + Celery Beat
- **Authentification** : JWT (cookies HttpOnly + refresh rotation)
- **Documentation API** : Swagger UI (drf-spectacular)
- **SMS** : Orange SMS API Côte d'Ivoire
- **OTP** : Vérification par SMS (inscription + reset password)

### Frontend (à venir)
- **Framework** : Vue.js 3 + TypeScript
- **State Management** : Pinia
- **UI Library** : Tailwind CSS + Headless UI
- **Maps** : Leaflet (géolocalisation)

### Infrastructure
- **Conteneurisation** : Docker + Docker Compose
- **Reverse Proxy** : Nginx (production)
- **Déploiement** : Dokploy
- **Domaines** :
  - API : `https://api.presso.pro`
  - Frontend : `https://presso.pro`

---

## 🚀 Démarrage Rapide

### Prérequis
- Docker >= 24.0
- Docker Compose >= 2.20
- Make (optionnel, pour les commandes simplifiées)

### Installation

#### 1. Cloner le projet

```bash
cd /path/to/presso
```

#### 2. Générer les secrets sécurisés

```bash
# Générer DJANGO_SECRET_KEY, JWT_SECRET_KEY, DB_PASSWORD
make generate-secrets

# OU directement
python3 generate_secrets.py
```

**Output** :
```
🔐 PRESSO - GÉNÉRATEUR DE SECRETS SÉCURISÉS
======================================================================

📝 DJANGO_SECRET_KEY
----------------------------------------------------------------------
Jtz77!lpKdoQqxlsITH)5cY^vt&ERPPs6*MxloTVh-7APYJ81vJVtaB4aDE%CXA1

🔑 JWT_SECRET_KEY
----------------------------------------------------------------------
Vjwn)tqeMbL#e4_)^#@4Sq61JJH@Nx!XPcR^M3SkHf##6&60(X_zFxOLebMA!P#^

🗄️  DB_PASSWORD
----------------------------------------------------------------------
skeZI2VWxFJg-Rly7GKwxQZ-0hVB8_UF
```

### 3. Configurer le fichier .env

```bash
# Copier le template .env
cp .env.example .env

# Éditer le fichier .env avec vos valeurs
nano .env
```

**⚠️ Variables OBLIGATOIRES à modifier** :

```env
# Secrets (copiez depuis make generate-secrets)
DJANGO_SECRET_KEY=Jtz77!lpKdoQqxlsITH)5cY^vt&ERPPs6*MxloTVh-7APYJ81vJVtaB4aDE%CXA1
JWT_SECRET_KEY=Vjwn)tqeMbL#e4_)^#@4Sq61JJH@Nx!XPcR^M3SkHf##6&60(X_zFxOLebMA!P#^
DB_PASSWORD=skeZI2VWxFJg-Rly7GKwxQZ-0hVB8_UF

# Orange SMS API (depuis votre compte Orange Developer)
ORANGE_SMS_CLIENT_ID=votre_application_id
ORANGE_SMS_CLIENT_SECRET=votre_client_secret
ORANGE_SMS_SENDER_ADDRESS=tel:+225XXXXXXXXXX
```

#### 4. Lancer l'application

```bash
# Option 1: Initialisation complète (première fois)
make init

# Option 2: Manuellement
make build
make up
make migrate
make collectstatic
```

#### 5. Créer un superutilisateur

```bash
make createsuperuser
```

#### 6. Accéder à l'application

- **API** : http://localhost:8000
- **Admin Django** : http://localhost:8000/admin
- **Swagger UI** : http://localhost:8000/api/docs/
- **ReDoc** : http://localhost:8000/api/redoc/

---

## 📚 Commandes Make

### Gestion des services

```bash
make up              # Démarrer tous les services
make down            # Arrêter tous les services
make restart         # Redémarrer tous les services
make ps              # Voir l'état des services
make logs            # Voir tous les logs
make logs-backend    # Logs backend uniquement
make logs-celery     # Logs Celery uniquement
```

### Django

```bash
make shell           # Shell Django (iPython)
make bash            # Shell bash dans le conteneur
make migrate         # Appliquer les migrations
make makemigrations  # Créer de nouvelles migrations
make createsuperuser # Créer un superutilisateur
make check           # Vérifier la configuration
make test            # Lancer les tests
```

### Celery

```bash
make celery-status   # Statut de Celery
make celery-tasks    # Liste des tâches enregistrées
make celery-purge    # Purger les tâches en attente
```

### Base de données

```bash
make db-shell        # Shell PostgreSQL
make backup-db       # Sauvegarder la DB
make restore-db FILE=backups/xxx.sql  # Restaurer une sauvegarde
```

### Utilitaires

```bash
make generate-secrets # Générer secrets (DJANGO_SECRET_KEY, JWT_SECRET_KEY, DB_PASSWORD)
make redis-cli       # Redis CLI
make stats           # Stats des conteneurs
make clean           # Nettoyer conteneurs + volumes
```

### Aide

```bash
make help            # Afficher toutes les commandes
```

---

## 🐳 Services Docker

Le `docker-compose.yml` à la **racine du projet** orchestre 5 services :

| Service | Description | Port |
|---------|-------------|------|
| **postgres** | PostgreSQL 16 + PostGIS 3.4 | 5432 |
| **redis** | Redis 7 (Cache + Broker) | 6379 |
| **backend** | Django + Gunicorn (3 workers) | 8000 |
| **celery-worker** | Tâches asynchrones (SMS, emails) | - |
| **celery-beat** | Tâches planifiées (cron jobs) | - |

---

## 🌾 Tâches Celery

Celery découvre automatiquement les tâches dans **toutes les apps** listées :

- `apps.core`
- `apps.api`
- `apps.users`
- `apps.providers`
- `apps.services`
- `apps.tariffs`
- `apps.orders`
- `apps.order_items`
- `apps.payments`
- `apps.reviews`

### Tâches planifiées (Celery Beat)

| Tâche | Fréquence | Description |
|-------|-----------|-------------|
| `clean_expired_otp` | Toutes les 30 min | Nettoyer les codes OTP expirés |
| `clean_expired_tokens` | 1x/jour à 3h | Nettoyer les JWT blacklistés |
| `generate_daily_reports` | 1x/jour à 6h | Rapports quotidiens |

### Tâches asynchrones

- `send_sms_async` : Envoi SMS via Orange API
- `send_email_async` : Envoi d'emails

Pour créer une nouvelle tâche, ajoutez un fichier `tasks.py` dans votre app :

```python
# apps/mon_app/tasks.py
from celery import shared_task

@shared_task(name='apps.mon_app.tasks.ma_tache')
def ma_tache():
    # Votre logique
    pass
```

---

## 📡 API REST

### Endpoints d'authentification

```
POST   /api/auth/register/           # Inscription
POST   /api/auth/verify-phone/       # Vérifier OTP
POST   /api/auth/login/               # Connexion (JWT cookies)
POST   /api/auth/token/refresh/      # Refresh token
POST   /api/auth/token/verify/       # Vérifier token
GET    /api/auth/profile/            # Mon profil
PATCH  /api/auth/profile/            # Modifier profil
POST   /api/auth/change-password/    # Changer password
POST   /api/auth/forgot-password/    # Reset password (OTP SMS)
POST   /api/auth/reset-password/     # Confirmer reset
```

### Documentation

- **Swagger UI** : http://localhost:8000/api/docs/
- **ReDoc** : http://localhost:8000/api/redoc/
- **Schema OpenAPI** : http://localhost:8000/api/schema/

---

## 🔐 Authentification (Pattern B+)

### Architecture JWT + OTP

```
1. Inscription
   → POST /api/auth/register/
   → User créé (is_active=False)
   → OTP généré + SMS envoyé (Celery async)

2. Vérification OTP
   → POST /api/auth/verify-phone/
   → OTP vérifié → User activé
   → JWT généré → Cookies HttpOnly

3. Login
   → POST /api/auth/login/
   → JWT access (15min) + refresh (7j)
   → Cookies HttpOnly + Secure + SameSite=None

4. Refresh automatique
   → Interceptor Vue.js détecte 401
   → POST /api/auth/refresh/
   → Rotation + Blacklist ancien token
   → Nouveaux tokens dans cookies

5. Reset password
   → POST /api/auth/forgot-password/
   → OTP SMS
   → POST /api/auth/reset-password/
   → Password changé
```

**Sécurité** :
- ✅ Cookies HttpOnly (pas de XSS)
- ✅ Refresh rotation + blacklist (Redis)
- ✅ CORS strict (`.presso.pro`)
- ✅ CSRF protection
- ✅ Rate limiting (DRF throttling)

---

## 🧪 Tests

```bash
# Lancer tous les tests
make test

# Tests d'une app spécifique
docker-compose exec backend python manage.py test apps.users

# Tests avec coverage
docker-compose exec backend coverage run --source='.' manage.py test
docker-compose exec backend coverage report
```

---

## 🐛 Debugging

### Voir les logs

```bash
make logs              # Tous les services
make logs-backend      # Backend uniquement
make logs-celery       # Celery uniquement
```

### Shell Django

```bash
make shell

# Dans le shell
>>> from apps.users.models import User
>>> User.objects.count()
```

### Shell PostgreSQL

```bash
make db-shell

# Dans le shell
presso_db=# \dt
presso_db=# SELECT * FROM users_user LIMIT 5;
```

### Redis CLI

```bash
make redis-cli

# Dans le shell
127.0.0.1:6379> KEYS *
127.0.0.1:6379> GET presso:some_key
```

---

## 📊 Monitoring

### Statut des services

```bash
make ps
```

### Stats des conteneurs

```bash
make stats
```

### Tâches Celery

```bash
# Tâches actives
make celery-status

# Toutes les tâches enregistrées
make celery-tasks
```

---

## 🚢 Déploiement Production

### Avec Dokploy

1. **Préparer `.env` de production**

```env
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=VOTRE_CLE_PROD
DJANGO_ALLOWED_HOSTS=api.presso.pro
JWT_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
...
```

2. **Sur Dokploy**
   - Importer depuis Git
   - Pointer vers `docker-compose.yml` (racine)
   - Définir les variables d'environnement
   - Déployer

3. **Post-déploiement**

```bash
make migrate
make createsuperuser
make collectstatic
```

---

## 📝 Contribution

### Workflow Git

```bash
# Créer une branche
git checkout -b feature/ma-fonctionnalite

# Développer...

# Commit
git add .
git commit -m "feat: description"

# Push
git push origin feature/ma-fonctionnalite

# Créer une Pull Request
```

### Standards

- **Code** : PEP 8 (Python), ESLint (JS/TS)
- **Commits** : Conventional Commits
- **Tests** : Couverture > 80%
- **Documentation** : Docstrings + README

---

## 📄 Licence

Propriétaire - **CIACEMS Technologies** © 2025

---

## 🆘 Support

- **Email** : contact@presso.ci
- **Documentation** : [backend/README_DOCKER.md](backend/README_DOCKER.md)
- **Issues** : [GitHub Issues](https://github.com/votre-org/presso/issues)

---

## 🎯 Roadmap

### Phase 1 : Backend ✅
- [x] Architecture Django multitenant
- [x] GeoDjango (géolocalisation)
- [x] Docker Compose
- [x] Celery (async tasks)
- [x] Authentification JWT + OTP
- [ ] API complète (tous les endpoints)
- [ ] Tests unitaires/intégration

### Phase 2 : Frontend 🚧
- [ ] Vue.js 3 + TypeScript
- [ ] Design system (Tailwind)
- [ ] Authentification (interceptors)
- [ ] Carte interactive (Leaflet)
- [ ] Gestion commandes
- [ ] Paiement Mobile Money

### Phase 3 : Production 📅
- [ ] CI/CD (GitHub Actions)
- [ ] Monitoring (Sentry)
- [ ] Backup automatique
- [ ] Mise en production
- [ ] App mobile (React Native)

---

🧺 **PRESSO** - La révolution digitale du pressing en Côte d'Ivoire ! 🇨🇮


# #####################################

Une fois que le gérant a validé son compte par OTP, il ne peut pas voir de commandes tout de suite car son pressing est "vide" (pas de tarifs, pas d'adresse, pas de visibilité sur l'app client).
Voici l'étape intermédiaire obligatoire avant le Dashboard opérationnel : Le Setup de Configuration (Onboarding).
1. L'écran "Bienvenue" (L'état zéro)
Si c'est sa première connexion, tu ne lui affiches pas un dashboard vide avec des graphiques à 0. Tu lui affiches un parcours guidé (Steppers) pour rendre son pressing "Actif" sur ta plateforme.
Il doit remplir 3 sections essentielles avant d'accéder au reste :
Étape 1 : Identité du Pressing : Nom de la boutique, localisation GPS précise (pour les ramassages), et logo/photo de la devanture.
Étape 2 : Services & Tarifs : Il doit choisir ce qu'il traite (Chemises, Costumes, Draps, Pagnes) et fixer ses prix. Sans prix, le client ne peut pas commander en ligne.
Étape 3 : Information de Paiement : Où doit-on lui envoyer son argent (Numéro Mobile Money pour le retrait des fonds).
2. Une fois le Setup terminé : La "Landing Page" du Dashboard
Une fois qu'il est configuré et qu'il commence à recevoir des commandes, voici ce qu'il doit voir en premier dès qu'il se connecte (sa page d'accueil) :
L'écran "Aperçu de la Situation" (Overview)
Le gérant ne veut pas chercher l'information, elle doit lui sauter aux yeux. Cet écran doit afficher 3 zones :
Le "Status" du Pressing (Toggle Switch) :
Un gros bouton en haut : [ OUVERT ] ou [ FERMÉ ].
Si c'est sur "Fermé", son pressing disparaît de l'application client (pratique s'il a une panne de machine ou trop de travail).
Les Compteurs d'Urgence (Badges de notification) :
"Nouvelles commandes" (Celles qu'il n'a pas encore acceptées).
"Ramassages du jour" (Ce que le livreur doit aller chercher).
"Retards" (Linge qui aurait dû être livré mais qui ne l'est pas encore).
Le Flux d'Activité Récent :
Une liste chronologique des 5 dernières actions (ex: "Commande #452 payée par le client", "Livreur en route pour la commande #450").
Pourquoi ne pas afficher "La liste des commandes" directement ?
Parce que dans une marketplace, l'action la plus importante est l'acceptation des nouvelles demandes. Si tu affiches directement toute la liste (anciennes et nouvelles), il risque de rater une nouvelle commande urgente au milieu des autres.
Résumé de ce qu'il voit en arrivant (Dashboard Home) :
Son état de disponibilité (Ouvert/Fermé).
Son solde d'argent disponible (pour le motiver).
Les actions immédiates à faire (Nouvelles commandes à accepter).
