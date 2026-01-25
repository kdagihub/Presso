# CONTEXTE MVP PRESSOW - PRESTATAIRE

> Document de contexte pour les conversations LLM futures
> Dernière mise à jour : 25 janvier 2026

---

## 1. PRÉSENTATION DU PROJET

### Pressow - Marketplace de Pressing à Domicile

**Pressow** est une plateforme marketplace connectant :
- **Clients** : Particuliers souhaitant faire nettoyer leurs vêtements
- **Prestataires** : Pressings/Blanchisseries proposant leurs services

### Stack Technique

| Composant | Technologie |
|-----------|-------------|
| **Backend** | Django 5.x + Django REST Framework |
| **Frontend** | Vue.js 3 + TypeScript + Vite |
| **Base de données** | PostgreSQL |
| **Cache/Queue** | Redis + Celery |
| **Notifications Push** | Firebase Cloud Messaging (FCM) |
| **Paiement** | Moneroo (Mobile Money) |
| **SMS** | Orange SMS API |
| **Conteneurisation** | Docker Compose |

### Structure du Projet

```
Presso/
├── backend/
│   ├── apps/
│   │   ├── api/          # ViewSets, Serializers, URLs
│   │   ├── core/         # Models principaux, Services
│   │   ├── users/        # Authentification, FCM Tokens
│   │   ├── providers/    # Modèles prestataires
│   │   ├── orders/       # Modèles commandes
│   │   └── reviews/      # Modèles avis (à connecter)
│   └── config/           # Settings Django
├── frontend/Pressow/Pressow/
│   ├── src/
│   │   ├── Views/        # Pages Vue
│   │   ├── Components/   # Composants réutilisables
│   │   ├── stores/       # Pinia stores
│   │   ├── services/     # API, Notifications
│   │   └── router/       # Vue Router
│   └── public/           # Assets statiques, Service Worker
└── docker-compose.yml
```

---

## 2. AUTHENTIFICATION & SESSIONS

### Architecture JWT

- **Access Token** : Durée 15 minutes, stocké en mémoire (Pinia store)
- **Refresh Token** : Durée 7 jours, stocké dans cookie HttpOnly

### Configuration Actuelle (settings.py)

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,  # Désactivé pour éviter les race conditions
}
```

### Fichiers Clés

| Fichier | Rôle |
|---------|------|
| `frontend/src/stores/auth.ts` | Store Pinia pour l'authentification |
| `frontend/src/services/api.ts` | Axios avec intercepteurs 401 |
| `frontend/src/main.ts` | Initialisation auth avant montage app |
| `backend/apps/api/viewsets/auth.py` | Endpoints login, refresh, logout |

### Points Importants

1. **`initAuth()`** dans `main.ts` : Tente de rafraîchir le token au démarrage
2. **Intercepteur 401** : Rafraîchit automatiquement le token si expiré
3. **Cookie refresh** : Path `/api/auth/`, HttpOnly, SameSite=Lax
4. **Protection race condition** : `DashboardLayout` attend `authReady` avant appels API

---

## 3. SYSTÈME DE NOTIFICATIONS

### Canaux Disponibles

| Canal | Provider | Status |
|-------|----------|--------|
| **Push** | Firebase Cloud Messaging | ✅ Fonctionnel |
| **Email** | SMTP (Brevo/Sendinblue) | ✅ Fonctionnel |
| **SMS** | Orange SMS API | ⚠️ Configuré (payant) |

### Architecture

```
NotificationDispatcher (backend/apps/core/services/notification_dispatcher.py)
├── notify_provider_new_order()          → Push + Email
├── notify_provider_payment_received()   → Push + Email
├── notify_provider_status_confirmation() → Push uniquement
├── notify_client_order_status_changed() → Push + Email + SMS(OTP)
└── _send_push() / _send_email() / _send_sms()
```

### Configuration FCM

- **Backend** : `firebase-admin` SDK, credentials JSON dans `backend/config/`
- **Frontend** : Service Worker `public/firebase-messaging-sw.js`
- **Tokens FCM** : Stockés dans `UserFCMToken` model

### Fichiers Clés

| Fichier | Rôle |
|---------|------|
| `backend/apps/core/services/notification_dispatcher.py` | Service centralisé |
| `backend/apps/core/utils/fcm.py` | Envoi FCM |
| `frontend/src/services/notifications.ts` | Gestion tokens côté client |
| `frontend/public/firebase-messaging-sw.js` | Service Worker |

---

## 4. GESTION DES COMMANDES

### Flux de Commande

```
pending → confirmed → collected → in_progress → ready → in_delivery → delivered
                                                   ↓
                                              cancelled
```

### Endpoints Principaux

| Endpoint | Méthode | Rôle |
|----------|---------|------|
| `/api/orders/` | POST | Créer commande (client) |
| `/api/providers/orders/` | GET | Liste commandes prestataire |
| `/api/providers/orders/<id>/status/` | PATCH/POST | Changer statut |
| `/api/providers/orders/<id>/assign/` | POST | Assigner staff/agence |

### OTP Livraison

- Généré automatiquement quand statut = `ready`
- Client reçoit le code par notification
- Livreur valide avec `/api/provider/orders/<id>/validate-otp/`

### Fichiers Clés

| Fichier | Rôle |
|---------|------|
| `backend/apps/orders/models.py` | Modèle Order, OrderItem |
| `backend/apps/api/viewsets/orders.py` | ViewSets commandes |
| `backend/apps/api/serializers/orders.py` | Serializers avec tous les champs |
| `frontend/src/Views/ViewsCommun/Commandes.vue` | Page commandes prestataire |
| `frontend/src/stores/orders.ts` | Store commandes |

---

## 5. PORTEFEUILLE & PAIEMENTS

### Flux de Paiement

```
1. Client passe commande
2. Client paie via Moneroo (Mobile Money)
3. Webhook Moneroo confirme paiement
4. Montant crédité au wallet prestataire (moins commission)
5. Prestataire demande payout
6. Virement vers compte Mobile Money
```

### Modèles

- `ProviderWallet` : Solde du prestataire
- `WalletTransaction` : Historique (credit, debit, payout, refund)
- `ProviderPayoutAccount` : Comptes Mobile Money pour retrait
- `PayoutRequest` : Demandes de retrait

### Endpoints

| Endpoint | Rôle |
|----------|------|
| `/api/provider/wallet/` | Résumé wallet |
| `/api/provider/wallet/transactions/` | Historique |
| `/api/provider/wallet/payout/` | Demander retrait |
| `/api/webhooks/moneroo/` | Webhook paiement |

---

## 6. PARAMÈTRES PRESTATAIRE

### Modèle ProviderSettings

```python
# Notifications - Canaux
push_notifications = True
email_notifications = True
sms_notifications = False

# Notifications - Types
notify_new_orders = True
notify_order_updates = True
notify_payments = True
notify_reminders = True

# Disponibilité
pause_mode = False
pause_reason = ""
max_orders_per_day = 0  # 0 = illimité
working_days = []  # ['monday', 'tuesday', ...]

# Sécurité
two_factor_auth = False
login_alerts = True
```

### Endpoints

| Endpoint | Rôle |
|----------|------|
| `/api/providers/settings/full/` | GET/PATCH settings complets |
| `/api/providers/pause/` | POST toggle pause mode |

---

## 7. ONBOARDING PRESTATAIRE

### Étapes

1. **Identité** : Nom commercial, adresse, GPS, logo
2. **Services** : Configuration des services et tarifs
3. **Payout** : Compte Mobile Money pour les retraits
4. **Validation** : Finalisation et ouverture

### Endpoints

| Endpoint | Rôle |
|----------|------|
| `/api/provider/onboarding/status/` | Statut actuel |
| `/api/provider/onboarding/identity/` | Étape 1 |
| `/api/provider/onboarding/services/` | Étape 2 |
| `/api/provider/onboarding/payout/` | Étape 3 |
| `/api/provider/onboarding/complete/` | Finalisation |

---

## 8. ÉTAT ACTUEL DU MVP

### ✅ Fonctionnel

| Module | Backend | Frontend | Notes |
|--------|---------|----------|-------|
| Authentification | ✅ | ✅ | JWT + Cookie refresh |
| Onboarding | ✅ | ✅ | 4 étapes |
| Dashboard | ✅ | ✅ | Stats, résumé |
| Commandes | ✅ | ✅ | CRUD + statuts + OTP |
| Services/Tarifs | ✅ | ✅ | CRUD complet |
| Portefeuille | ✅ | ✅ | Wallet + Payouts |
| Paramètres | ✅ | ✅ | Notifications, pause |
| Push Notifications | ✅ | ✅ | FCM fonctionnel |
| Email Notifications | ✅ | ✅ | Via SMTP |
| Profil | ✅ | ✅ | Photo, infos |

### ⚠️ À Finaliser

| Module | Backend | Frontend | Action Requise |
|--------|---------|----------|----------------|
| **Avis (Reviews)** | ✅ Modèle | ❌ Mockée | Créer API + connecter frontend |
| **Statistiques** | ⚠️ Basique | ❌ localStorage | Connecter à l'API réelle |

### 📋 Post-MVP

- Gestion multi-agences (API prête, pas de vue)
- Gestion du staff (API prête, pas de vue)
- Export PDF statistiques
- Notifications SMS (coût à valider)

---

## 9. PROBLÈMES RÉSOLUS

### 1. Déconnexion lors du refresh de page

**Cause** : Race condition entre `initAuth()` et les appels API du DashboardLayout, combinée avec le blacklist des tokens.

**Solution** :
- `BLACKLIST_AFTER_ROTATION: False` dans settings.py
- `DashboardLayout` attend `authReady` avant appels API
- Table blacklist vidée

### 2. Push notifications multicast 404

**Cause** : `messaging.send_multicast()` retournait 404 sur Firebase.

**Solution** : Remplacé par `messaging.send()` en boucle (plus fiable).

### 3. Méthode PATCH non autorisée sur changement statut

**Cause** : `ProviderOrderStatusUpdateView` n'avait que `post()`.

**Solution** : Ajout de `patch()` qui appelle `_update_status()`.

---

## 10. COMMANDES UTILES

### Docker

```bash
# Démarrer les services
docker compose up -d

# Redémarrer le backend
docker compose restart backend

# Logs backend
docker compose logs -f backend

# Shell Django
docker compose exec backend python manage.py shell
```

### Base de données

```bash
# Migrations
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate

# Vider blacklist tokens (si problème auth)
docker compose exec backend python manage.py shell -c "
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
BlacklistedToken.objects.all().delete()
"
```

### Frontend

```bash
cd frontend/Pressow/Pressow
npm run dev      # Dev server
npm run build    # Production build
```

---

## 11. VARIABLES D'ENVIRONNEMENT IMPORTANTES

```env
# Backend (.env)
DEBUG=True
SECRET_KEY=...
DATABASE_URL=postgres://...
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=15
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Firebase
FCM_CREDENTIALS_PATH=/app/config/pressow-42706-firebase-adminsdk-....json

# Moneroo
MONEROO_API_KEY=...
MONEROO_SECRET_KEY=...

# Email
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...

# Notifications
NOTIFICATION_CHANNELS_PUSH=True
NOTIFICATION_CHANNELS_EMAIL=True
NOTIFICATION_CHANNELS_SMS=False
```

---

## 12. CONTACTS & RESSOURCES

- **Firebase Console** : https://console.firebase.google.com/project/pressow-42706
- **Moneroo Dashboard** : https://dashboard.moneroo.io
- **API Docs** : http://localhost:8000/api/docs/ (si drf-spectacular configuré)

---

*Ce document sert de contexte pour les futures conversations avec le LLM. Mettez-le à jour après chaque session de développement significative.*
