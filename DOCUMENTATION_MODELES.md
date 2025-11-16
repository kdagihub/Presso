# Documentation des Modèles de Données - Presso

> Documentation destinée aux développeurs frontend pour comprendre la structure de la base de données

## 📋 Table des matières

1. [Utilisateurs et Authentification](#1-utilisateurs-et-authentification)
2. [Prestataires](#2-prestataires)
3. [Services et Catalogue](#3-services-et-catalogue)
4. [Tarification](#4-tarification)
5. [Commandes](#5-commandes)
6. [Paiements](#6-paiements)
7. [Avis et Évaluations](#7-avis-et-évaluations)
8. [Permissions et Rôles](#8-permissions-et-rôles)
9. [Codes OTP](#9-codes-otp)

---

## 1. Utilisateurs et Authentification

### Table: `User`

**Description**: Représente tous les utilisateurs de la plateforme (clients, prestataires, employés).

#### Champs principaux:

| Champ | Type | Description | Obligatoire |
|-------|------|-------------|-------------|
| `id` | UUID | Identifiant unique de l'utilisateur | ✅ |
| `username` | String | Nom d'utilisateur unique | ✅ |
| `email` | Email | Adresse email unique | ✅ |
| `phone` | String | Numéro de téléphone au format `+225XXXXXXXXXX` | ✅ |
| `phone_verified_at` | DateTime | Date de vérification du téléphone | ❌ |
| `first_name` | String | Prénom | ❌ |
| `last_name` | String | Nom de famille | ❌ |
| `photo_profil` | Image | Photo de profil | ❌ |
| `password` | String | Mot de passe hashé | ✅ |
| `role` | String | Rôle personnalisé (ex: "pressing_premium") | ❌ |
| `group` | ForeignKey | Référence vers un groupe (client, prestataire, etc.) | ❌ |
| `custom_role` | ForeignKey | Rôle personnalisé avec permissions granulaires | ❌ |
| `latitude` | Decimal | Latitude de localisation | ❌ |
| `longitude` | Decimal | Longitude de localisation | ❌ |
| `location` | Point | Point géographique (généré automatiquement) | ❌ |
| `adresse` | Text | Adresse complète | ❌ |
| `quartier` | String | Quartier ou commune | ❌ |
| `date_inscription` | DateTime | Date d'inscription (automatique) | ✅ |
| `is_active` | Boolean | Compte actif ou non | ✅ |

#### Méthodes importantes:
- `is_phone_verified()` → Retourne `true` si le téléphone est vérifié
- `mark_phone_verified()` → Marque le téléphone comme vérifié
- `get_provider()` → Retourne le prestataire associé (si applicable)
- `has_custom_permission(code)` → Vérifie si l'utilisateur a une permission spécifique

---

## 2. Prestataires

### Table: `Provider`

**Description**: Représente un prestataire de services (Pressing ou Fanico).

#### Champs principaux:

| Champ | Type | Description | Obligatoire |
|-------|------|-------------|-------------|
| `id` | UUID | Identifiant unique | ✅ |
| `user` | OneToOne | Référence vers l'utilisateur | ✅ |
| `type` | Choice | Type de prestataire: `pressing` ou `fanico` | ✅ |
| `nom_commercial` | String | Nom commercial de l'établissement | ✅ |
| `photo_local` | Image | Photo de l'établissement | ❌ |
| `zone_couverture` | Text | Description des zones desservies | ✅ |
| `rayon_km` | Decimal | Rayon de couverture en kilomètres (défaut: 5.00) | ✅ |
| `latitude` | Decimal | Latitude de localisation | ❌ |
| `longitude` | Decimal | Longitude de localisation | ❌ |
| `location` | Point | Point géographique (généré automatiquement) | ❌ |
| `adresse` | Text | Adresse complète | ✅ |
| `quartier` | String | Quartier ou commune | ❌ |
| `statut_kyc` | Choice | Statut KYC: `pending`, `verified`, `rejected` | ✅ |
| `document_identite` | File | Document d'identité pour vérification | ❌ |
| `is_active` | Boolean | Prestataire actif (peut recevoir commandes) | ✅ |
| `created` | DateTime | Date de création | ✅ |
| `updated` | DateTime | Dernière modification | ✅ |

#### Méthodes importantes:
- `find_nearby(lat, lng, max_km, type)` → Trouve les prestataires à proximité
- `is_within_range(user_or_point)` → Vérifie si un point est dans le rayon

---

## 3. Services et Catalogue

### Table: `ServiceTemplate`

**Description**: Templates de services créés par la plateforme (base commune).

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `label` | String | Libellé du service (ex: "Lavage simple") |
| `description` | Text | Description détaillée |
| `mode_tarif` | Choice | Mode: `kg` (kilogramme), `piece` (pièce), `forfait` |
| `duree_estimee` | Integer | Durée en minutes |
| `icone` | String | Nom de l'icône |
| `is_active` | Boolean | Template actif |

### Table: `Service`

**Description**: Services personnalisés par chaque prestataire.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `provider` | ForeignKey | Prestataire propriétaire |
| `template` | ForeignKey | Template de base (optionnel) |
| `label` | String | Libellé du service |
| `description` | Text | Description |
| `mode_tarif` | Choice | `kg`, `piece`, ou `forfait` |
| `duree_estimee` | Integer | Durée en minutes |
| `icone` | String | Nom de l'icône |
| `is_active` | Boolean | Service disponible |

### Table: `ArticleType`

**Description**: Types d'articles (vêtements) que le prestataire peut traiter.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `provider` | ForeignKey | Prestataire propriétaire |
| `template` | ForeignKey | Template de base (optionnel) |
| `nom` | String | Nom de l'article (ex: "Chemise") |
| `description` | Text | Description |

### Table: `Matiere`

**Description**: Matières/tissus gérés par le prestataire.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `provider` | ForeignKey | Prestataire propriétaire |
| `template` | ForeignKey | Template de base (optionnel) |
| `nom` | String | Nom de la matière (ex: "Coton", "Soie") |
| `description` | Text | Description |

---

## 4. Tarification

### Table: `ProviderService`

**Description**: Relation entre prestataire et services avec prix et délais.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `provider` | ForeignKey | Prestataire |
| `service` | ForeignKey | Service proposé |
| `prix_base` | Decimal | Prix de base en FCFA |
| `delai` | Integer | Délai en heures |
| `is_available` | Boolean | Service actuellement disponible |

### Table: `Tariff`

**Description**: Tarification détaillée par article, matière et service.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `provider` | ForeignKey | Prestataire |
| `article_type` | ForeignKey | Type d'article |
| `matiere` | ForeignKey | Matière (optionnel) |
| `service` | ForeignKey | Service appliqué |
| `prix` | Decimal | Prix en FCFA |

**Note**: Permet une tarification fine : "Chemise en soie + Repassage = 500 FCFA"

---

## 5. Commandes

### Table: `Order`

**Description**: Représente une commande de service de lessive.

#### Champs principaux:

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `numero` | String | Numéro de commande (ex: "ORD-2025-0001") |
| `client` | ForeignKey | Client qui commande |
| `provider` | ForeignKey | Prestataire assigné |
| `statut` | Choice | Statut actuel (voir ci-dessous) |
| `adresse_collecte` | Text | Adresse de collecte du linge |
| `latitude_collecte` | Decimal | Position GPS collecte |
| `longitude_collecte` | Decimal | Position GPS collecte |
| `adresse_livraison` | Text | Adresse de livraison |
| `latitude_livraison` | Decimal | Position GPS livraison |
| `longitude_livraison` | Decimal | Position GPS livraison |
| `creneau_collecte` | DateTime | Date/heure souhaitée pour collecte |
| `creneau_livraison` | DateTime | Date/heure estimée de livraison |
| `date_collecte` | DateTime | Date/heure réelle de collecte |
| `date_livraison` | DateTime | Date/heure réelle de livraison |
| `total_estime` | Decimal | Montant estimé en FCFA |
| `total_final` | Decimal | Montant final après traitement |
| `frais_livraison` | Decimal | Frais de livraison en FCFA |
| `notes_client` | Text | Instructions particulières du client |
| `notes_provider` | Text | Observations du prestataire |
| `signature_client` | Image | Signature à la livraison |
| `created` | DateTime | Date de création |
| `updated` | DateTime | Dernière modification |

#### Statuts possibles:
- `pending` : En attente
- `confirmed` : Confirmée
- `collected` : Collectée
- `in_progress` : En cours de traitement
- `ready` : Prête pour livraison
- `delivered` : Livrée
- `cancelled` : Annulée

### Table: `OrderItem`

**Description**: Ligne de commande - représente un article dans une commande.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `order` | ForeignKey | Commande parente |
| `article_type` | ForeignKey | Type d'article |
| `matiere` | ForeignKey | Matière (optionnel) |
| `service` | ForeignKey | Service appliqué |
| `quantite` | Decimal | Quantité (pièces ou kg) |
| `prix_unitaire` | Decimal | Prix unitaire en FCFA |
| `total_ligne` | Decimal | Total de la ligne (calculé automatiquement) |
| `photo` | Image | Photo du vêtement (optionnel) |
| `notes` | Text | Notes (taches, état, etc.) |
| `created` | DateTime | Date de création |

**Calcul automatique**: `total_ligne = quantite × prix_unitaire`

---

## 6. Paiements

### Table: `Payment`

**Description**: Suivi des transactions de paiement Mobile Money.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `order` | ForeignKey | Commande associée |
| `reference` | String | Référence unique (ex: "PAY-1234567890-ABC") |
| `operateur` | Choice | Opérateur: `orange`, `mtn`, `moov`, `wave` |
| `numero_payeur` | String | Numéro du payeur |
| `montant` | Decimal | Montant en FCFA |
| `statut` | Choice | Statut du paiement (voir ci-dessous) |
| `transaction_id` | String | ID externe de l'opérateur |
| `metadata` | JSON | Données supplémentaires |
| `error_message` | Text | Message d'erreur si échec |
| `date_initiation` | DateTime | Date de début |
| `date_completion` | DateTime | Date de finalisation |
| `is_refund` | Boolean | Est un remboursement |
| `refund_of` | ForeignKey | Paiement remboursé (si applicable) |
| `created` | DateTime | Date de création |
| `updated` | DateTime | Dernière modification |

#### Statuts possibles:
- `pending` : En attente
- `processing` : En cours
- `completed` : Complété
- `failed` : Échoué
- `refunded` : Remboursé
- `cancelled` : Annulé

#### Opérateurs Mobile Money:
- `orange` : Orange Money
- `mtn` : MTN Mobile Money
- `moov` : Moov Money
- `wave` : Wave

---

## 7. Avis et Évaluations

### Table: `Review`

**Description**: Avis client sur un prestataire après une commande.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `client` | ForeignKey | Client qui évalue |
| `provider` | ForeignKey | Prestataire évalué |
| `order` | OneToOne | Commande associée (un avis par commande) |
| `note` | Integer | Note globale (1 à 5 étoiles) |
| `commentaire` | Text | Commentaire textuel |
| `note_qualite` | Integer | Note qualité (1 à 5) |
| `note_delai` | Integer | Note respect des délais (1 à 5) |
| `note_service` | Integer | Note service client (1 à 5) |
| `is_approved` | Boolean | Avis approuvé (visible publiquement) |
| `is_flagged` | Boolean | Avis signalé pour modération |
| `reponse_provider` | Text | Réponse du prestataire |
| `date_reponse` | DateTime | Date de la réponse |
| `created` | DateTime | Date de création |
| `updated` | DateTime | Dernière modification |

---

## 8. Permissions et Rôles

### Table: `Permission`

**Description**: Permissions granulaires du système.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `code` | String | Code unique (ex: "view_orders") |
| `name` | String | Nom lisible |
| `description` | Text | Description |
| `module` | Choice | Module concerné |
| `is_active` | Boolean | Permission active |

#### Modules disponibles:
- `orders` : Gestion des commandes
- `services` : Gestion des services
- `tariffs` : Gestion des tarifs
- `stats` : Statistiques
- `staff` : Gestion du personnel
- `settings` : Paramètres
- `customers` : Gestion clients

### Table: `Role`

**Description**: Rôles personnalisés créés par chaque prestataire.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `provider` | ForeignKey | Prestataire propriétaire |
| `name` | String | Nom du rôle (ex: "Manager") |
| `description` | Text | Description |
| `permissions` | ManyToMany | Permissions associées |
| `is_active` | Boolean | Rôle actif |

### Table: `ProviderSettings`

**Description**: Configuration personnalisée par prestataire.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `provider` | OneToOne | Prestataire concerné |
| `business_name` | String | Nom commercial affiché |
| `logo` | Image | Logo |
| `primary_color` | String | Couleur principale (hex) |
| `auto_accept_orders` | Boolean | Acceptation automatique des commandes |
| `require_payment_before` | Boolean | Exiger paiement avant traitement |
| `min_order_amount` | Decimal | Montant minimum de commande |
| `delivery_fee` | Decimal | Frais de livraison par défaut |
| `email_notifications` | Boolean | Activer notifications email |
| `sms_notifications` | Boolean | Activer notifications SMS |
| `notification_email` | Email | Email de notification |
| `notification_phone` | String | Téléphone de notification |
| `opening_hours` | JSON | Horaires d'ouverture |
| `metadata` | JSON | Paramètres supplémentaires |

---

## 9. Codes OTP

### Table: `OTPCode`

**Description**: Codes OTP pour vérification téléphone et sécurité.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | UUID | Identifiant unique |
| `phone` | String | Numéro de téléphone |
| `code_hash` | String | Code haché (sécurité) |
| `purpose` | Choice | Objectif du code |
| `attempts` | Integer | Nombre de tentatives |
| `is_verified` | Boolean | Code vérifié |
| `created_at` | DateTime | Date de création |
| `expires_at` | DateTime | Date d'expiration |
| `verified_at` | DateTime | Date de vérification |
| `ip_address` | IP | Adresse IP de la requête |
| `user_agent` | Text | Navigateur/App utilisé |

#### Objectifs (purpose):
- `signup` : Inscription
- `reset_password` : Réinitialisation mot de passe
- `phone_verification` : Vérification téléphone
- `login_2fa` : Double authentification

#### Méthodes importantes:
- `is_expired()` → Vérifie si le code a expiré
- `is_valid()` → Vérifie si le code est valide (non expiré, non vérifié, tentatives OK)

---

## 🔗 Relations entre les tables

### Schéma de relations simplifié:

```
User ─────────┬─────── Provider (OneToOne)
              │
              ├─────── Order (ForeignKey - en tant que client)
              │
              ├─────── Review (ForeignKey - en tant que client)
              │
              └─────── Role (ForeignKey - custom_role)

Provider ─────┬─────── Order (ForeignKey)
              │
              ├─────── Service (ForeignKey)
              │
              ├─────── ArticleType (ForeignKey)
              │
              ├─────── Matiere (ForeignKey)
              │
              ├─────── Tariff (ForeignKey)
              │
              ├─────── ProviderService (ForeignKey)
              │
              ├─────── Review (ForeignKey)
              │
              ├─────── Role (ForeignKey)
              │
              └─────── ProviderSettings (OneToOne)

Order ────────┬─────── OrderItem (ForeignKey)
              │
              ├─────── Payment (ForeignKey)
              │
              └─────── Review (OneToOne)

OrderItem ────┬─────── ArticleType (ForeignKey)
              │
              ├─────── Matiere (ForeignKey)
              │
              └─────── Service (ForeignKey)
```

---

## 📝 Notes importantes

### Conventions de nommage:
- **UUID**: Tous les IDs sont des UUID (pas de simples entiers)
- **Timestamps**: `created` et `updated` sont automatiques
- **Soft delete**: Pas de suppression réelle, utilisation de `is_active`
- **Foreign Keys**: Relations protégées (PROTECT) pour éviter suppressions accidentelles

### Géolocalisation:
- Les champs `location` sont des **Points géographiques** (PostGIS)
- Calculés automatiquement depuis `latitude` et `longitude`
- Permettent des recherches spatiales (proximité, distance, etc.)

### Multitenant:
- Chaque prestataire a ses propres services, tarifs, articles
- Isolation des données par `provider`
- Templates globaux vs instances personnalisées

### Sécurité:
- Mots de passe hashés automatiquement
- Codes OTP hashés dans la base de données
- Vérification du téléphone obligatoire pour certaines actions
- Système de permissions granulaires

