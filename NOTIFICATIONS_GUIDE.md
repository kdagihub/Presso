# 📱 PRESSO - Guide des Notifications Push

## ✅ Configuration Terminée

### **1. Firebase configuré**
- ✅ Projet Firebase : `presso-668d4`
- ✅ Credentials : `backend/firebase-adminsdk.json`
- ✅ Ajouté au `.gitignore` (sécurité)
- ✅ Variables `.env` configurées

### **2. Backend configuré**
- ✅ Daphne (serveur ASGI pour WebSockets)
- ✅ Django Channels (WebSockets temps réel)
- ✅ Firebase Admin SDK (push notifications)
- ✅ Système unifié de notifications

---

## 🏗️ Architecture des Notifications

### **3 Canaux de Notification**

```
┌─────────────────────────────────────────────────────┐
│               SYSTÈME DE NOTIFICATIONS              │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1️⃣ WebSocket (Temps Réel)                         │
│     User connecté à l'app                           │
│     → Notification instantanée via WS               │
│                                                      │
│  2️⃣ Push Notification (FCM)                        │
│     User déconnecté mais app installée             │
│     → Push via Firebase Cloud Messaging            │
│                                                      │
│  3️⃣ SMS (Orange API)                               │
│     Pas d'internet / App non installée             │
│     → SMS via Orange SMS API                        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### **Logique de Fallback**

```python
# Le système essaie dans cet ordre :
1. WebSocket (si user connecté) → Instantané
2. Push FCM (si app installée) → Quelques secondes
3. SMS (fallback) → Backup si échec
```

---

## 🚀 Utilisation

### **1. Envoyer une notification (Simple)**

```python
from apps.core.notifications import notification_service

# Envoyer à un utilisateur
notification_service.send_notification(
    user_id='123',
    notification_type='order_created',
    title='Nouvelle commande',
    message='Vous avez reçu une nouvelle commande #CMD001',
    data={'order_id': 'cmd_123', 'amount': 5000}
)
```

**Le système essaiera automatiquement les 3 canaux !**

---

### **2. Envoyer depuis une vue Django**

```python
# apps/orders/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.core.notifications import notification_service

@api_view(['POST'])
def create_order(request):
    # ... créer la commande ...
    
    # Notifier le prestataire
    notification_service.send_notification(
        user_id=str(provider.user.id),
        notification_type='order_created',
        title='Nouvelle commande',
        message=f'Commande #{order.numero_commande} reçue',
        data={'order_id': str(order.id)}
    )
    
    return Response({'success': True})
```

---

### **3. Envoyer depuis Celery (Async)**

```python
# apps/orders/tasks.py
from celery import shared_task
from apps.core.notifications import notification_service

@shared_task
def notify_order_ready(order_id):
    """Notifier le client que sa commande est prête"""
    from apps.orders.models import Order
    
    order = Order.objects.get(id=order_id)
    
    notification_service.send_notification(
        user_id=str(order.client.id),
        notification_type='order_ready',
        title='Commande prête !',
        message=f'Votre commande #{order.numero_commande} est prête',
        data={'order_id': str(order_id)}
    )

# Utilisation
notify_order_ready.delay(order_id='cmd_123')
```

---

### **4. Envoyer depuis un Signal Django**

```python
# apps/orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.orders.models import Order
from apps.core.notifications import notification_service

@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, **kwargs):
    """Notifier quand le statut de la commande change"""
    
    if instance.statut == 'pret':
        notification_service.send_notification(
            user_id=str(instance.client.id),
            notification_type='order_ready',
            title='Commande prête',
            message=f'Commande #{instance.numero_commande} est prête',
            data={'order_id': str(instance.id)}
        )
```

---

## 🔧 Configuration Frontend

### **1. Vue.js - WebSocket**

```javascript
// composables/useNotifications.js
import { ref, onMounted, onUnmounted } from 'vue'

export function useNotifications(userId) {
  const socket = ref(null)
  const notifications = ref([])
  
  onMounted(() => {
    // Connexion WebSocket
    socket.value = new WebSocket(
      `ws://localhost:8000/ws/notifications/${userId}/`
    )
    
    // Recevoir les notifications
    socket.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'notification') {
        notifications.value.unshift(data.notification)
        
        // Afficher une toast notification
        showToast(data.notification.title, data.notification.message)
      }
    }
    
    // Keep-alive (ping toutes les 30s)
    setInterval(() => {
      if (socket.value.readyState === WebSocket.OPEN) {
        socket.value.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  })
  
  onUnmounted(() => {
    socket.value?.close()
  })
  
  return { notifications }
}
```

---

### **2. Vue.js - Firebase (PWA)**

```javascript
// plugins/firebase.js
import { initializeApp } from 'firebase/app'
import { getMessaging, getToken, onMessage } from 'firebase/messaging'

const firebaseConfig = {
  apiKey: "...",
  projectId: "presso-668d4",
  messagingSenderId: "...",
  appId: "..."
}

const app = initializeApp(firebaseConfig)
const messaging = getMessaging(app)

// Demander la permission et obtenir le token
export async function requestNotificationPermission() {
  try {
    const permission = await Notification.requestPermission()
    
    if (permission === 'granted') {
      // Obtenir le FCM token
      const token = await getToken(messaging, {
        vapidKey: 'YOUR_VAPID_KEY'
      })
      
      // Envoyer le token au backend
      await fetch('https://api.presso.pro/api/users/fcm-token/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ fcm_token: token })
      })
      
      return token
    }
  } catch (error) {
    console.error('Erreur permission:', error)
  }
}

// Écouter les messages en foreground
onMessage(messaging, (payload) => {
  console.log('Notification reçue:', payload)
  
  // Afficher la notification
  new Notification(payload.notification.title, {
    body: payload.notification.body,
    icon: '/logo.png'
  })
})
```

---

### **3. Android (React Native / Flutter)**

```kotlin
// MainActivity.kt
import com.google.firebase.messaging.FirebaseMessaging

FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        
        // Envoyer le token au backend Django
        sendTokenToBackend(token)
    }
}

fun sendTokenToBackend(token: String) {
    // API call to Django
    api.post("https://api.presso.pro/api/users/fcm-token/", 
        json = mapOf("fcm_token" to token)
    )
}
```

---

## 📊 Modèle User (Stockage FCM Token)

### **Ajouter le champ au modèle User**

```python
# apps/users/models.py
from django.db import models

class User(AbstractUser):
    # ... champs existants ...
    
    # FCM Token pour les push notifications
    fcm_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Token Firebase Cloud Messaging"
    )
    
    # Multiples devices (optionnel)
    # fcm_tokens = models.JSONField(default=list, blank=True)
```

### **Endpoint pour sauvegarder le token**

```python
# apps/api/viewsets/auth.py
from rest_framework.decorators import action

class AuthViewSet(viewsets.GenericViewSet):
    
    @action(detail=False, methods=['post'], url_path='fcm-token')
    def save_fcm_token(self, request):
        """
        POST /api/auth/fcm-token/
        Body: { "fcm_token": "..." }
        """
        user = request.user
        fcm_token = request.data.get('fcm_token')
        
        if fcm_token:
            user.fcm_token = fcm_token
            user.save(update_fields=['fcm_token'])
            
            # Souscrire à des topics (optionnel)
            from apps.core.utils.fcm import subscribe_to_topic
            
            if user.role == 'prestataire':
                subscribe_to_topic(fcm_token, 'providers')
            else:
                subscribe_to_topic(fcm_token, 'clients')
            
            return Response({'success': True})
        
        return Response({'error': 'Token manquant'}, status=400)
```

---

## 🧪 Tests

### **1. Tester WebSocket**

```bash
# Terminal 1: Démarrer le serveur
make up

# Terminal 2: Tester avec websocat
websocat ws://localhost:8000/ws/notifications/USER_ID/

# OU avec curl
curl --include \
     --no-buffer \
     --header "Connection: Upgrade" \
     --header "Upgrade: websocket" \
     --header "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
     --header "Sec-WebSocket-Version: 13" \
     http://localhost:8000/ws/notifications/USER_ID/
```

### **2. Tester Push Notification**

```python
# Shell Django
make shell

>>> from apps.core.utils.fcm import send_fcm_notification
>>> 
>>> notification = {
...     'title': 'Test PRESSO',
...     'message': 'Notification de test',
...     'data': {'test': 'true'}
... }
>>> 
>>> send_fcm_notification('DEVICE_FCM_TOKEN', notification)
True
```

### **3. Tester le système complet**

```python
make shell

>>> from apps.core.notifications import notification_service
>>> from apps.users.models import User
>>> 
>>> user = User.objects.first()
>>> 
>>> notification_service.send_notification(
...     user_id=str(user.id),
...     notification_type='order_created',
...     title='Test Notification',
...     message='Ceci est un test',
...     data={'test': True}
... )
```

---

## 📋 Types de Notifications Configurés

```python
# Définis dans settings.py
NOTIFICATION_TYPES = {
    'order_created': {
        'title': 'Nouvelle commande',
        'priority': 'high'
    },
    'order_status_changed': {
        'title': 'Mise à jour commande',
        'priority': 'high'
    },
    'payment_received': {
        'title': 'Paiement reçu',
        'priority': 'normal'
    },
    'order_ready': {
        'title': 'Commande prête',
        'priority': 'high'
    },
    'order_delivered': {
        'title': 'Livraison effectuée',
        'priority': 'normal'
    },
}
```

---

## 🔐 Sécurité

### **Checklist**
- [x] `firebase-adminsdk.json` dans `.gitignore`
- [x] Fichier JSON hors du dossier `config/`
- [x] WebSocket avec authentification JWT
- [x] Validation user_id dans le consumer
- [ ] Rate limiting sur les notifications
- [ ] Chiffrement des données sensibles

---

## 🚀 Déploiement Production

### **1. Variables d'environnement**

```env
# Production .env
FCM_CREDENTIALS_PATH=/app/firebase-adminsdk.json
FCM_PROJECT_ID=presso-668d4
NOTIFICATION_WEBSOCKET_ENABLED=True
NOTIFICATION_PUSH_ENABLED=True
NOTIFICATION_SMS_ENABLED=True
```

### **2. Docker Volume pour Firebase JSON**

```yaml
# docker-compose.yml (Production)
services:
  backend:
    volumes:
      - ./firebase-adminsdk.json:/app/firebase-adminsdk.json:ro
```

### **3. Nginx pour WebSockets**

```nginx
# nginx.conf
location /ws/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

---

## 📚 Ressources

- **Firebase Docs** : https://firebase.google.com/docs/cloud-messaging
- **Django Channels** : https://channels.readthedocs.io/
- **Daphne** : https://github.com/django/daphne
- **WebSocket Test** : https://www.websocket.org/echo.html

---

🎉 **Système de notifications prêt pour PRESSO !**

