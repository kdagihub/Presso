
# 🧼 Projet Marketplace Digitale de Lessive (PRESSO) – Côte d’Ivoire 🇨🇮

## 📌 Contexte & Objectif

En Côte d’Ivoire, de nombreuses personnes n’ont ni le temps ni les moyens de gérer leur lessive elles-mêmes.  
Deux types de prestataires existent :

- Les **pressings formels** avec locaux, souvent plus chers.
- Les **fanicos**, prestataires informels, souvent des femmes lavant à domicile, difficiles à localiser.

Aujourd’hui, l’accès à un service de lessive fiable, abordable et rapide est un vrai **besoin non résolu**.  
Notre objectif est de **digitaliser l’accès à ces services** à travers une **application mobile**.

---

## 🎯 Objectif du projet

Créer une **plateforme web/mobile** (type marketplace) permettant :

- Aux **clients** : de trouver facilement des prestataires de lessive (pressings & fanicos), comparer les prix, commander, payer, et suivre leur commande.
- Aux **prestataires** : de recevoir des commandes, gérer leurs services et disponibilités, encaisser les paiements.
- À l’**opérateur** : de gérer les utilisateurs, les litiges, les avis, les tarifs et les zones desservies.

---

## 🔧 Stack choisie

- **Frontend** : Flutter (mobile) + Vue.js (admin web)
- **Backend** : Django (REST API) avec PostgreSQL
- **Auth** : Login par téléphone, e-mail ou username
- **RBAC** : Groupes Django (`client`, `fanico`, `pressing`, `livreur`, `admin`) + champ `role` pour granularité
- **DB** : UUID pour tous les IDs + champs `created` (sauf User)
- **Champs sensibles** : téléphone, e-mail chiffrés
- **Paiement** : intégration Mobile Money (OM, MTN, Moov)

---

## 📐 Modélisation (MCD simplifié)

### Utilisateur (User)
- id (UUID)
- username, nom, prénom
- téléphone, email
- group (FK → Group)
- role (string, ex: fanico_express)
- date_inscription
- is_active

### Prestataire (Provider)
- id
- user_id
- type (pressing/fanico)
- nom_commercial, zone_couverture, rayon_km
- statut_KYC

### Service
- id, label, mode_tarif (kg, pièce, forfait), durée_estimee

### ProviderService
- provider_id, service_id
- prix_base, délai

### Order
- id, client_id, provider_id
- adresse_collecte, livraison
- créneau, statut, total_estime, total_final
- preuve_livraison_url

### OrderItem (ligne de commande)
- order_id, service_id
- quantité, prix_unitaire, total_ligne

### Payment
- id, order_id, opérateur, statut, montant, référence

### Review
- id, client_id, provider_id, order_id, note, commentaire

---

## 👥 Groupes Django utilisés

- `client`
- `fanico`
- `pressing`
- `livreur`
- `admin`

Tous les utilisateurs appartiennent à un **groupe** et peuvent avoir un **rôle personnalisé** (stocké dans `User.role`).

---

## ✅ Fonctionnalités principales MVP

- Auth OTP (login via téléphone/email/username)
- Géolocalisation des prestataires
- Commande simple : choix du prestataire + service + créneau + collecte/livraison
- Paiement mobile money
- Suivi de commande étape par étape
- Notation et avis
- Dashboard admin + back-office
- Gestion des litiges, des services, des tarifs

---

## 📙 User Stories (extraits MVP)

### US01 – En tant que client
```gherkin
Given que je suis connecté à l’app,
When je consulte la liste des prestataires autour de moi,
Then je peux filtrer par prix, délai, type de service.
````

### US02 – En tant que client

```gherkin
Given que j’ai choisi un prestataire,
When je crée une commande avec mes vêtements,
Then je peux payer et suivre les étapes (collecte, lavage, livraison).
```

### US03 – En tant que fanico

```gherkin
Given que je suis connecté,
When je reçois une commande,
Then je peux l’accepter ou la refuser selon ma dispo.
```

### US04 – En tant qu’admin

```gherkin
Given que je suis dans le back-office,
When je vois les commandes en retard,
Then je peux envoyer un rappel ou intervenir en cas de litige.
```

---

## 🔐 Sécurité & bonnes pratiques

* Authentification sécurisée (JWT + refresh)
* Cryptage des données sensibles
* Permissions contrôlées par groupes Django + logique métier
* UUID pour tous les IDs
* Timestamps pour audit (`created`)

---

## 🚀 Objectifs de cette première phase

* [x] MCD validé
* [ ] Génération des modèles Django avec UUID + rôles + groupes
* [ ] Auth multi-identifiants + OTP
* [ ] API REST + Swagger docs
* [ ] Mobile Flutter (client + prestataire)
* [ ] Back-office Vue.js
* [ ] Intégration paiement Mobile Money
* [ ] Déploiement sur VPS (Docker + Dokploy)

---

## 📎 Notes pour IA développeur (Cursor, etc.)

* Générer les modèles Django avec UUIDField comme `id`
* Étendre `AbstractUser` pour User
* Ajouter groupe (Group FK) et `role` textuel
* Générer migrations + serializers + ViewSets DRF
* Setup fixtures initiales pour les Groupes
* Générer tests unitaires pour chaque modèle
* Si possible : validation automatisée du login multi-identifiants

---

```

---

```
