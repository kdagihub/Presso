# 🚨 DIAGNOSTIC ORANGE SMS CI - Non-réception des SMS

## 📊 État actuel

### ✅ Ce qui fonctionne
- Token OAuth obtenu avec succès
- API Orange retourne `200 OK` pour tous les envois
- 2 SMS "envoyés avec succès" selon les logs :
  - SMS #1 → `+2250544166309` (ID: `63499acf-d2f2-4bf6-802f-57cfb7021731`)
  - SMS #2 → `+2250797969394` (ID: `994a732a-c97f-466b-8c6a-5ce9a270a7a3`)
- Configuration technique correcte (payload, format, etc.)

### ❌ Le problème
- **AUCUN SMS n'a été reçu** sur les deux numéros
- **"Usage & Billing" n'existe pas** sur le portail Orange Developer
- Les SMS semblent acceptés par l'API mais **jamais livrés**

---

## 🔍 CAUSE PROBABLE N°1 : Sender Address non autorisé

### Le problème
Orange SMS Côte d'Ivoire **n'autorise généralement PAS** l'envoi de SMS depuis :
- ❌ Des numéros personnels (comme `+2250797969394`)
- ❌ Des numéros "normaux" sans autorisation

### Ce qui est accepté
- ✅ **Short Codes** officiels (numéros courts professionnels : ex. `1234`)
- ✅ **Numéros longue distance autorisés** par Orange Business Services
- ✅ **Alpha Sender IDs** (dans certains pays, mais **PAS en Côte d'Ivoire**)

### Pourquoi l'API retourne `200 OK` ?
L'API Orange **accepte** la requête (authentification OK, format OK) mais le **routeur SMS d'Orange CI** peut **silencieusement bloquer** les messages provenant de senders non autorisés.

---

## 🔍 CAUSE PROBABLE N°2 : Bundle non activé

### Signes révélateurs
- Absence de l'onglet "Usage & Billing" ou "Statistics"
- Bundle acheté mais pas lié à l'application
- Bundle expiré (valide 7 jours seulement)

### Vérification à faire
1. Allez sur https://developer.orange.com
2. **"My Apps"** → Sélectionnez votre app
3. Onglet **"Subscriptions"** ou **"APIs"**
4. Vérifiez que **"SMS Cote d'Ivoire (2.0)"** est présent et **actif**
5. Onglet **"Billing"** ou **"Credits"**
6. Vérifiez le solde de votre bundle

---

## 💡 SOLUTIONS

### Solution 1 : Obtenir un Short Code officiel ⭐ (RECOMMANDÉ pour production)

**Qu'est-ce qu'un Short Code ?**
Un numéro court professionnel (ex : `1234`, `8888`) enregistré auprès d'Orange CI pour votre entreprise.

**Avantages :**
- ✅ Taux de livraison proche de 100%
- ✅ Crédibilité et confiance des utilisateurs
- ✅ Branding (ex: "SMS de 8888 - Presso")
- ✅ Support prioritaire Orange Business

**Comment l'obtenir ?**
1. Contactez **Orange Business Services Côte d'Ivoire**
   - Email : `oss-ci@orange.com` ou `entreprises@orange.ci`
   - Téléphone : `+225 07 08 99 99 99`
2. Demandez un **Short Code dédié** pour votre application "Presso"
3. Fournissez :
   - Nom de l'entreprise (CIACEMS TECHNOLOGIES)
   - Description du service (plateforme de pressing)
   - Volume estimé de SMS/mois
   - Cas d'usage (OTP, notifications)
4. Délai : généralement **2-4 semaines**
5. Coût : variable selon le type de Short Code

**Après obtention :**
```bash
# Mettre à jour le .env
ORANGE_SMS_SENDER_ADDRESS=tel:+2251234  # Votre Short Code
```

---

### Solution 2 : Demander l'autorisation pour votre numéro personnel (temporaire)

**Contact Orange Developer Support :**
1. Allez sur https://developer.orange.com/support
2. Ouvrez un ticket avec :
   - **Sujet** : "Autorisation sender address pour SMS CI"
   - **App ID** : Votre `client_id` Orange
   - **Sender souhaité** : `+2250797969394`
   - **Justification** : "Tests OTP pour application de pressing en développement"

**Délai :** 2-5 jours ouvrés

⚠️ **Note :** Cette solution est généralement pour **tests uniquement**, pas pour production.

---

### Solution 3 : Utiliser un service SMS alternatif (plan B)

Si Orange CI bloque systématiquement, considérez :

**Twilio (international, fonctionne en CI)**
- ✅ Sender ID alphanumérique accepté ("Presso")
- ✅ Dashboard complet avec statistiques
- ✅ Bonne délivrabilité en Afrique
- 💰 ~$0.08/SMS en CI
- 🌐 https://www.twilio.com

**Africa's Talking (spécialisé Afrique)**
- ✅ Couvre 19 pays africains dont CI
- ✅ Pricing compétitif
- ✅ API similaire à Orange
- 🌐 https://africastalking.com

**Configuration pour Twilio (exemple) :**
```python
# backend/apps/core/utils/sms_twilio.py
from twilio.rest import Client

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
message = client.messages.create(
    body="Votre code Presso : 123456",
    from_="Presso",  # Sender ID alphanumérique
    to="+2250544166309"
)
```

---

## 🔧 ACTIONS IMMÉDIATES (à faire MAINTENANT)

### 1. Vérifier le portail Orange Developer

**Étapes précises :**
```
1. https://developer.orange.com
2. Login
3. "My Apps" → Cliquez sur votre app
4. Onglet "Overview" : notez le "Status" de l'app
5. Onglet "Subscriptions" : vérifiez que "SMS CI" est présent
6. Onglet "Credentials" : vérifiez Client ID/Secret
7. Cherchez un onglet "Statistics", "Usage", "Billing" ou "Credits"
```

**Faites des captures d'écran de :**
- La page "Subscriptions"
- La page "Overview"
- Tout onglet lié au bundle/crédit

### 2. Contacter le support Orange

**Email à envoyer :**
```
À : developer-support@orange.com
Sujet : SMS CI - Messages non livrés malgré API 200 OK

Bonjour,

J'utilise l'API "SMS Cote d'Ivoire (2.0)" avec les informations suivantes :
- Client ID : UbCeojyTVn2S70kC5rLJ... (vos 20 premiers caractères)
- Application : Presso (plateforme de pressing)
- Bundle acheté : Bundle 0 (20 SMS)

Problème :
- L'API retourne 200 OK pour tous mes envois
- J'ai les message_id de confirmation
- AUCUN SMS n'est jamais délivré aux destinataires
- Je n'ai pas d'onglet "Usage & Billing" dans mon dashboard

Envois testés :
1. Message ID: 63499acf-d2f2-4bf6-802f-57cfb7021731 (vers +2250544166309)
2. Message ID: 994a732a-c97f-466b-8c6a-5ce9a270a7a3 (vers +2250797969394)

Sender Address utilisé : tel:+2250797969394

Questions :
1. Mon sender address est-il autorisé pour envoyer des SMS ?
2. Mon bundle est-il correctement activé ?
3. Comment puis-je obtenir un Short Code pour production ?

Merci de votre aide,
[Votre nom]
CIACEMS TECHNOLOGIES
```

### 3. Tester avec un autre numéro

Essayez d'envoyer un SMS vers un **autre opérateur** (MTN, Moov) pour voir si c'est un problème Orange-to-Orange :

```bash
# Tester vers un numéro MTN (05XXXXXXXX)
curl -X POST http://localhost:8000/api/auth/otp/request/ \
  -H "Content-Type: application/json" \
  -d '{"phone":"+22505XXXXXXXX","purpose":"phone_verification"}'
```

---

## 📡 Webhooks Delivery Receipts (maintenant implémentés)

J'ai ajouté des webhooks pour recevoir les **statuts de livraison réels** d'Orange.

### Endpoints disponibles :
- `GET /api/webhooks/health/` → Test santé
- `POST /api/webhooks/orange/dr/` → Delivery Receipts
- `POST /api/webhooks/orange/mo/` → SMS entrants

### Configuration sur Orange Developer :

**Quand vous obtiendrez un Short Code :**
1. Allez dans votre app Orange Developer
2. Section "SMS" → "Delivery Receipt Subscriptions"
3. Ajoutez votre URL de webhook :
   ```
   https://api.presso.pro/api/webhooks/orange/dr/
   ```
4. Relancez un envoi SMS
5. Consultez les logs Django :
   ```bash
   docker compose logs backend | grep "Orange Delivery Receipt"
   ```

**Vous verrez des logs comme :**
```
✅ SMS delivered successfully to tel:+225XXXXXXXXXX
❌ SMS delivery failed to tel:+225XXXXXXXXXX (raison: ...)
```

---

## 📝 CONCLUSION

### Diagnostic probable
**Votre sender address (`+2250797969394`) n'est PAS autorisé par Orange CI pour envoyer des SMS via l'API.**

L'API accepte vos requêtes (d'où le 200 OK) mais le routeur SMS bloque silencieusement la livraison.

### Solutions par ordre de priorité

1. **Court terme (dev/test)** : Contactez Orange Support pour autoriser votre numéro personnel
2. **Moyen terme (prod)** : Obtenez un Short Code officiel auprès d'Orange Business
3. **Plan B** : Basculez sur Twilio ou Africa's Talking

### Prochaines étapes

1. ✅ **FAIT** : Configuration technique correcte, webhooks implémentés
2. 🔄 **EN COURS** : Diagnostic du problème de sender address
3. ⏳ **BLOQUÉ** : Attente réponse Orange Support OU obtention Short Code
4. ⏳ **ALTERNATIVE** : Évaluation Twilio/Africa's Talking

---

## 🆘 Support

Si vous avez besoin d'aide :
- **Orange Developer Support** : https://developer.orange.com/support
- **Orange Business CI** : +225 07 08 99 99 99
- **Email** : entreprises@orange.ci

---

*Document généré le 2025-10-17*
*Presso API - CIACEMS TECHNOLOGIES*

