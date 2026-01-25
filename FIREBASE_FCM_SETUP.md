# Configuration Firebase Cloud Messaging (FCM) - Pressow

Ce document explique comment configurer les notifications push pour Pressow.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FIREBASE                                        │
│                         (Google Cloud)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────┐           ┌───────────────────┐
        │  Backend Django   │           │  Frontend Vue.js  │
        │                   │           │                   │
        │  Service Account  │           │  firebaseConfig   │
        │  (JSON file)      │           │  + VAPID Key      │
        │                   │           │                   │
        │  ENVOIE les       │           │  REÇOIT les       │
        │  notifications    │           │  notifications    │
        └───────────────────┘           └───────────────────┘
```

## Informations du projet Firebase Pressow

| Paramètre | Valeur |
|-----------|--------|
| Nom du projet | Pressow |
| Project ID | `pressow-42706` |
| Numéro du projet | `803839731409` |

---

## 1. Configuration Backend (Django)

### Fichiers requis

1. **Service Account JSON** : `pressow-42706-firebase-adminsdk-fbsvc-aa1d0b7787.json`
   - Téléchargé depuis Firebase Console > Comptes de service
   - À placer dans `/backend/config/`

### Variables d'environnement (.env)

```bash
# Firebase Cloud Messaging
FCM_CREDENTIALS_PATH=/app/config/pressow-42706-firebase-adminsdk-fbsvc-aa1d0b7787.json
FCM_PROJECT_ID=pressow-42706
FCM_VAPID_KEY=BIjqfwstFwVV4WvienVdTM-1RoByeMGro8AJD8Sq932KfFqRR4CL3VeKmXxdsYGet8Ng9Ig_8iAmmMzaJ5JN0Y4

# Canaux de notification
NOTIFICATION_PUSH_ENABLED=True
```

### API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/notifications/fcm/register/` | POST | Enregistrer un token FCM |
| `/api/notifications/fcm/unregister/` | POST | Supprimer un token FCM |
| `/api/notifications/devices/` | GET | Lister les devices enregistrés |
| `/api/notifications/devices/<id>/` | DELETE | Supprimer un device |
| `/api/notifications/test/` | POST | Envoyer une notification de test |

---

## 2. Configuration Frontend (Vue.js)

### Installation

```bash
cd frontend
npm install firebase
```

### Configuration Firebase (`src/config/firebase.ts`)

```typescript
// src/config/firebase.ts
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage, type Messaging } from 'firebase/messaging';

const firebaseConfig = {
  apiKey: "AIzaSyDP4KDSkN23jzBNqZfy537Z400WSuNSfw8",
  authDomain: "pressow-42706.firebaseapp.com",
  projectId: "pressow-42706",
  storageBucket: "pressow-42706.firebasestorage.app",
  messagingSenderId: "803839731409",
  appId: "1:803839731409:web:cfeef23b397bcaae8607f0",
  measurementId: "G-EEZZ55XWH9"
};

// Clé VAPID pour les notifications Web Push
const VAPID_KEY = 'BIjqfwstFwVV4WvienVdTM-1RoByeMGro8AJD8Sq932KfFqRR4CL3VeKmXxdsYGet8Ng9Ig_8iAmmMzaJ5JN0Y4';

// Initialiser Firebase
const app = initializeApp(firebaseConfig);

// Messaging (uniquement si le navigateur supporte les notifications)
let messaging: Messaging | null = null;

if (typeof window !== 'undefined' && 'Notification' in window) {
  messaging = getMessaging(app);
}

/**
 * Demande la permission de notification et retourne le token FCM
 */
export async function requestNotificationPermission(): Promise<string | null> {
  if (!messaging) {
    console.warn('Notifications non supportées par ce navigateur');
    return null;
  }

  try {
    const permission = await Notification.requestPermission();
    
    if (permission !== 'granted') {
      console.log('Permission de notification refusée');
      return null;
    }

    // Obtenir le token FCM
    const token = await getToken(messaging, { vapidKey: VAPID_KEY });
    console.log('Token FCM obtenu:', token);
    
    return token;
  } catch (error) {
    console.error('Erreur lors de la demande de permission:', error);
    return null;
  }
}

/**
 * Écoute les messages reçus quand l'app est au premier plan
 */
export function onForegroundMessage(callback: (payload: any) => void): void {
  if (!messaging) return;
  
  onMessage(messaging, (payload) => {
    console.log('Message reçu (foreground):', payload);
    callback(payload);
  });
}

export { app, messaging };
```

### Service Worker (`public/firebase-messaging-sw.js`)

Ce fichier DOIT être à la racine du dossier `public/` pour fonctionner.

```javascript
// public/firebase-messaging-sw.js
// Service Worker pour recevoir les notifications en arrière-plan

importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.0/firebase-messaging-compat.js');

// Configuration Firebase (même que dans l'app)
firebase.initializeApp({
  apiKey: "AIzaSyDP4KDSkN23jzBNqZfy537Z400WSuNSfw8",
  authDomain: "pressow-42706.firebaseapp.com",
  projectId: "pressow-42706",
  storageBucket: "pressow-42706.firebasestorage.app",
  messagingSenderId: "803839731409",
  appId: "1:803839731409:web:cfeef23b397bcaae8607f0"
});

const messaging = firebase.messaging();

// Gestion des messages en arrière-plan
messaging.onBackgroundMessage((payload) => {
  console.log('[SW] Message reçu en arrière-plan:', payload);

  const notificationTitle = payload.notification?.title || 'Pressow';
  const notificationOptions = {
    body: payload.notification?.body || '',
    icon: '/logo-192x192.png',
    badge: '/badge-72x72.png',
    tag: payload.data?.type || 'default',
    data: payload.data,
    // Actions (optionnel)
    actions: [
      { action: 'open', title: 'Ouvrir' },
      { action: 'close', title: 'Fermer' }
    ]
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Gestion du clic sur la notification
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification cliquée:', event);
  
  event.notification.close();
  
  // Ouvrir l'app ou focus sur l'onglet existant
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Si l'app est déjà ouverte, focus dessus
        for (const client of clientList) {
          if (client.url.includes('pressow.com') && 'focus' in client) {
            return client.focus();
          }
        }
        // Sinon, ouvrir une nouvelle fenêtre
        if (clients.openWindow) {
          const url = event.notification.data?.url || '/';
          return clients.openWindow(url);
        }
      })
  );
});
```

### Service d'enregistrement (`src/services/notifications.ts`)

```typescript
// src/services/notifications.ts
import api from './api';
import { requestNotificationPermission, onForegroundMessage } from '@/config/firebase';

interface FCMRegisterResponse {
  success: boolean;
  message: string;
  device?: {
    id: string;
    type: string;
    name: string;
  };
}

/**
 * Initialise les notifications push pour l'utilisateur connecté
 */
export async function initializeNotifications(): Promise<boolean> {
  try {
    // 1. Demander la permission et obtenir le token
    const token = await requestNotificationPermission();
    
    if (!token) {
      console.log('Pas de token FCM obtenu');
      return false;
    }

    // 2. Détecter le type de device
    const deviceType = detectDeviceType();
    const deviceName = getDeviceName();

    // 3. Enregistrer le token sur le serveur
    const response = await api.post<FCMRegisterResponse>('/notifications/fcm/register/', {
      token,
      device_type: deviceType,
      device_name: deviceName,
      device_info: {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
      }
    });

    if (response.data.success) {
      console.log('Token FCM enregistré avec succès');
      
      // 4. Écouter les messages au premier plan
      setupForegroundListener();
      
      return true;
    }

    return false;
  } catch (error) {
    console.error('Erreur lors de l\'initialisation des notifications:', error);
    return false;
  }
}

/**
 * Désactive les notifications pour ce device
 */
export async function disableNotifications(token: string): Promise<boolean> {
  try {
    await api.post('/notifications/fcm/unregister/', { token });
    return true;
  } catch (error) {
    console.error('Erreur lors de la désactivation des notifications:', error);
    return false;
  }
}

/**
 * Configure le listener pour les messages au premier plan
 */
function setupForegroundListener(): void {
  onForegroundMessage((payload) => {
    // Afficher une notification native ou un toast dans l'app
    const { title, body } = payload.notification || {};
    
    // Option 1: Toast dans l'app (recommandé)
    // useToast().add({ title, description: body, type: 'info' });
    
    // Option 2: Notification native (si l'app est visible)
    if (Notification.permission === 'granted') {
      new Notification(title || 'Pressow', {
        body: body || '',
        icon: '/logo-192x192.png'
      });
    }
  });
}

function detectDeviceType(): 'web' | 'android' | 'ios' {
  const ua = navigator.userAgent.toLowerCase();
  if (/android/.test(ua)) return 'android';
  if (/iphone|ipad|ipod/.test(ua)) return 'ios';
  return 'web';
}

function getDeviceName(): string {
  const ua = navigator.userAgent;
  
  // Navigateur
  let browser = 'Navigateur';
  if (ua.includes('Chrome')) browser = 'Chrome';
  else if (ua.includes('Firefox')) browser = 'Firefox';
  else if (ua.includes('Safari')) browser = 'Safari';
  else if (ua.includes('Edge')) browser = 'Edge';
  
  // OS
  let os = '';
  if (ua.includes('Windows')) os = 'Windows';
  else if (ua.includes('Mac')) os = 'Mac';
  else if (ua.includes('Linux')) os = 'Linux';
  else if (ua.includes('Android')) os = 'Android';
  else if (ua.includes('iOS') || ua.includes('iPhone')) os = 'iOS';
  
  return `${browser} sur ${os}`;
}
```

### Utilisation dans App.vue

```typescript
// Dans App.vue ou après le login
import { initializeNotifications } from '@/services/notifications';

// Après connexion réussie de l'utilisateur
onMounted(async () => {
  if (authStore.isAuthenticated) {
    // Attendre un peu pour ne pas bloquer le chargement initial
    setTimeout(async () => {
      await initializeNotifications();
    }, 2000);
  }
});
```

---

## 3. Flux de fonctionnement

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FLUX D'ACTIVATION                                    │
└─────────────────────────────────────────────────────────────────────────────┘

1. Utilisateur se connecte sur Vue.js
              │
              ▼
2. Vue.js demande permission (Notification.requestPermission())
              │
              ▼
3. Navigateur affiche popup "Autoriser les notifications ?"
              │
              ▼
4. Si accepté → Firebase génère un token FCM unique
              │
              ▼
5. Vue.js envoie le token à Django (POST /api/notifications/fcm/register/)
              │
              ▼
6. Django stocke le token dans UserFCMToken

┌─────────────────────────────────────────────────────────────────────────────┐
│                       FLUX D'ENVOI DE NOTIFICATION                           │
└─────────────────────────────────────────────────────────────────────────────┘

1. Événement côté Django (ex: nouvelle commande)
              │
              ▼
2. Django récupère les tokens FCM de l'utilisateur
              │
              ▼
3. Django envoie via Firebase Admin SDK
              │
              ▼
4. Firebase route vers le navigateur/mobile
              │
              ▼
5. Service Worker reçoit et affiche la notification
```

---

## 4. Dépannage

### Le token n'est pas généré

1. Vérifier que le site est en HTTPS (obligatoire pour les notifications)
2. Vérifier que le Service Worker est bien enregistré
3. Vérifier la console pour les erreurs Firebase

### Les notifications n'arrivent pas

1. Vérifier que le token est bien enregistré côté Django :
   ```bash
   python manage.py shell
   >>> from apps.users.models import UserFCMToken
   >>> UserFCMToken.objects.filter(user__username='test').values('token', 'is_active')
   ```

2. Tester l'envoi depuis Django :
   ```python
   from apps.core.utils.fcm import send_fcm_notification
   send_fcm_notification('TOKEN_ICI', {'title': 'Test', 'message': 'Hello!'})
   ```

3. Utiliser l'endpoint de test :
   ```bash
   curl -X POST https://api.pressow.com/api/notifications/test/ \
     -H "Authorization: Bearer TOKEN_JWT"
   ```

### Erreurs courantes

| Erreur | Solution |
|--------|----------|
| `UNREGISTERED` | Le token n'est plus valide, le supprimer de la base |
| `INVALID_ARGUMENT` | Le token est malformé |
| `messaging/permission-blocked` | L'utilisateur a bloqué les notifications |

---

## 5. Sécurité

1. **Ne jamais exposer le fichier JSON du service account** côté frontend
2. **La clé VAPID** peut être exposée (c'est une clé publique)
3. **Valider les tokens** côté serveur avant de les stocker
4. **Rate limiting** sur l'endpoint d'enregistrement des tokens
