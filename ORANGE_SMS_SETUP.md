# 📱 Configuration Orange SMS API

## 🎯 Prérequis

Tu as déjà :
- ✅ Créé un compte Orange Developer
- ✅ Souscrit au Bundle SMS Côte d'Ivoire (20 SMS pour 145 FCFA)
- ✅ Application ID et Secret

---

## 📋 Étapes de Configuration

### **1. Récupérer tes identifiants Orange**

Sur [Orange Developer](https://developer.orange.com) :

1. Va dans **"Mes applications"**
2. Sélectionne ton application (ou crée-en une)
3. Copie :
   - **Client ID** (Application ID)
   - **Client Secret**

### **2. Configurer le numéro émetteur**

Le **Sender Address** peut être :
- Un **numéro court** (short code) si tu en as un
- Un **numéro long** au format international : `tel:+225XXXXXXXXXX`
- Un **nom alphanumérique** (11 caractères max) : `Presso`

**Pour débuter** : utilise ton numéro de test fourni par Orange.

### **3. Mettre à jour le fichier .env**

Ouvre `/home/devfullstack/Bureau/CIACEMS TECHNOLOGIES/Business/presso_/Presso/.env` et remplace :

```bash
# -----------------------------------------------------------------
# ORANGE SMS API (Côte d'Ivoire)
# -----------------------------------------------------------------
ORANGE_SMS_CLIENT_ID=VOTRE_CLIENT_ID_ICI
ORANGE_SMS_CLIENT_SECRET=VOTRE_CLIENT_SECRET_ICI
ORANGE_SMS_SENDER_ADDRESS=tel:+225XXXXXXXXXX
ORANGE_SMS_SENDER_NAME=Presso
ORANGE_SMS_BASE_URL=https://api.orange.com
ORANGE_SMS_TOKEN_URL=https://api.orange.com/oauth/v3/token
ORANGE_SMS_DR_NOTIFY_URL=https://api.presso.pro/webhooks/orange/dr
```

**Exemple réel** :
```bash
ORANGE_SMS_CLIENT_ID=abc123def456
ORANGE_SMS_CLIENT_SECRET=xyz789uvw012
ORANGE_SMS_SENDER_ADDRESS=tel:+2250700000000
```

### **4. Réactiver les SMS**

```bash
NOTIFICATION_SMS_ENABLED=True
```

### **5. Tester la configuration**

```bash
# Valider la config
python3 validate_config.py

# Démarrer Docker
make up

# Tester l'envoi SMS
make shell

# Dans le shell Django
>>> from apps.core.utils.sms import send_sms
>>> send_sms('+2250700000000', 'Test PRESSO', tag='test')
```

---

## 🔧 Webhooks (Delivery Receipts)

### **Configurer l'URL de notification**

Orange enverra les **Delivery Receipts** (accusés de réception) à ton webhook.

**Webhook URL** : `https://api.presso.pro/webhooks/orange/dr`

**Important** :
- L'URL doit être **publique** (accessible depuis Internet)
- Utilise **ngrok** ou **localtunnel** en développement
- En production, configure ton domaine réel

### **Exemple avec ngrok (dev local)**

```bash
# Terminal 1: Démarrer ngrok
ngrok http 8000

# Tu obtiens une URL comme : https://abc123.ngrok.io

# Terminal 2: Mettre à jour .env
ORANGE_SMS_DR_NOTIFY_URL=https://abc123.ngrok.io/webhooks/orange/dr

# Redémarrer Docker
make restart
```

---

## 📊 Structure du Webhook Delivery Receipt

Orange enverra des POST à ton webhook :

```json
{
  "deliveryInfoNotification": {
    "deliveryInfo": {
      "address": "tel:+2250700000000",
      "deliveryStatus": "DeliveredToTerminal"
    },
    "callbackData": "otp_signup",
    "link": []
  }
}
```

**Statuts possibles** :
- `DeliveredToTerminal` : SMS délivré ✅
- `DeliveryImpossible` : Échec ❌
- `DeliveryUncertain` : Statut inconnu ⚠️

---

## 🧪 Tests

### **1. Test OAuth2 Token**

```python
# Shell Django
make shell

>>> from apps.core.utils.sms import get_orange_access_token
>>> token = get_orange_access_token()
>>> print(token)
'eyJhbGciOiJSUzI1NiIsI...'
```

### **2. Test Envoi SMS**

```python
>>> from apps.core.utils.sms import send_sms
>>> result = send_sms(
...     msisdn='+2250700000000',
...     message='Test PRESSO : Code OTP 123456',
...     tag='test'
... )
>>> print(result)
{'outboundSMSMessageRequest': {...}}
```

### **3. Test via l'API REST**

```bash
# Demander un OTP (nécessite un user existant)
curl -X POST http://localhost:8000/api/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+2250700000000",
    "purpose": "signup"
  }'
```

---

## 🐛 Dépannage

### **Erreur : "Unauthorized" (401)**

❌ **Client ID ou Secret incorrect**

✅ **Solution** : Vérifie tes identifiants sur Orange Developer

### **Erreur : "Insufficient funds"**

❌ **Bundle SMS épuisé**

✅ **Solution** : Achète un nouveau bundle sur Orange Developer

### **Erreur : "Invalid sender address"**

❌ **Format du numéro incorrect**

✅ **Solution** : Utilise le format `tel:+225XXXXXXXXXX`

### **SMS non reçu**

- Vérifie le numéro du destinataire
- Attends 1-2 minutes (délai réseau)
- Vérifie les logs Django : `docker logs presso_backend`
- Vérifie Celery : `docker logs presso_celery_worker`

---

## 📚 Ressources

- **Orange Developer** : https://developer.orange.com
- **API SMS Côte d'Ivoire** : https://developer.orange.com/apis/sms-ci
- **Documentation OAuth2** : https://developer.orange.com/resources/2-legged-oauth-flow-step-by-step
- **Guide API SMS** : https://developer.orange.com/apis/sms/getting-started

---

## 📝 Checklist

- [ ] Client ID récupéré
- [ ] Client Secret récupéré
- [ ] Sender Address configuré
- [ ] `.env` mis à jour
- [ ] `NOTIFICATION_SMS_ENABLED=True`
- [ ] Configuration validée (`python3 validate_config.py`)
- [ ] Test token réussi
- [ ] Test envoi SMS réussi
- [ ] Webhook configuré (optionnel)

---

🎉 **Une fois configuré, les SMS seront envoyés automatiquement pour :**

- ✉️ OTP à l'inscription
- ✉️ OTP réinitialisation mot de passe
- ✉️ Notifications importantes (commande, paiement)
- ✉️ Fallback si WebSocket/Push échouent

