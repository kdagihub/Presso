# Documentation des Modèles - Presso API

Documentation technique des modèles de données pour le développement frontend.

## Table des matières
- [Modèle User](#modèle-user)
- [Modèle Provider](#modèle-provider)
- [Relations entre modèles](#relations-entre-modèles)
- [Exemples de données JSON](#exemples-de-données-json)

---

## Modèle User

### Description
Modèle utilisateur personnalisé basé sur `AbstractUser` de Django. Gère les clients, prestataires et administrateurs de la plateforme Presso.

### Champs

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `id` | UUID | Auto | Identifiant unique (UUID v4) |
| `username` | String | ✅ | Nom d'utilisateur (champ de connexion principal) |
| `email` | Email | ✅ | Adresse email |
| `phone` | String(15) | ✅ | Numéro de téléphone (format: `+225XXXXXXXXXX` ou `XXXXXXXXXX`) |
| `phone_verified_at` | DateTime | ❌ | Date/heure de vérification du téléphone |
| `password` | String | ✅ | Mot de passe haché |
| `first_name` | String(150) | ❌ | Prénom |
| `last_name` | String(150) | ❌ | Nom de famille |
| `photo_profil` | ImageField | ❌ | Photo de profil (URL) |
| `role` | String(50) | ❌ | Rôle personnalisé (ex: `fanico_express`, `pressing_premium`) |
| `group` | ForeignKey | ❌ | Groupe Django (relation vers `Group`) |
| `custom_role` | ForeignKey | ❌ | Rôle personnalisé créé par un prestataire (relation vers `Role`) |
| `latitude` | Decimal(9,6) | ❌ | Latitude GPS du client |
| `longitude` | Decimal(9,6) | ❌ | Longitude GPS du client |
| `location` | PointField | ❌ | Point géographique PostGIS (auto-généré) |
| `adresse` | Text | ❌ | Adresse complète du client |
| `quartier` | String(200) | ❌ | Quartier/Commune |
| `is_active` | Boolean | Auto | Compte actif |
| `is_staff` | Boolean | Auto | Accès admin Django |
| `is_superuser` | Boolean | Auto | Super administrateur |
| `date_inscription` | DateTime | Auto | Date de création du compte |
| `date_joined` | DateTime | Auto | Date d'inscription (hérité) |
| `last_login` | DateTime | ❌ | Dernière connexion |

### Méthodes utiles

#### `get_role_display()`
Retourne une représentation lisible du rôle de l'utilisateur.

**Retour:** String (ex: `"client"`, `"Pressing ABC - Gérant"`)

#### `has_custom_permission(permission_code)`
Vérifie si l'utilisateur a une permission spécifique via son rôle personnalisé.

**Paramètre:** `permission_code` (String)  
**Retour:** Boolean

#### `get_provider()`
Retourne le prestataire associé à cet utilisateur (si applicable).

**Retour:** Instance `Provider` ou `None`

#### `is_phone_verified()`
Vérifie si le numéro de téléphone a été vérifié.

**Retour:** Boolean

#### `get_nearby_providers(max_distance_km=10, provider_type=None)`
Retourne les prestataires dans un rayon donné autour de la position du client.

**Paramètres:**
- `max_distance_km` (int): Distance maximale en km (défaut: 10)
- `provider_type` (String): `'pressing'` ou `'fanico'` (optionnel)

**Retour:** Liste de `Provider` triés par distance

#### `calculate_distance_to(provider)`
Calcule la distance en km entre le user et un prestataire.

**Paramètre:** Instance `Provider`  
**Retour:** Float (distance en km) ou `None`

---

## Modèle Provider

### Description
Modèle représentant un prestataire de service (Pressing ou Fanico) avec géolocalisation et gestion KYC.

### Champs

| Champ | Type | Requis | Description |
|-------|------|--------|-------------|
| `id` | UUID | Auto | Identifiant unique (UUID v4) |
| `user` | OneToOneField | ✅ | Utilisateur associé (relation vers `User`) |
| `type` | String(20) | ✅ | Type de prestataire : `'pressing'` ou `'fanico'` |
| `nom_commercial` | String(200) | ✅ | Nom de l'établissement ou du prestataire |
| `photo_local` | ImageField | ❌ | Photo de l'établissement (URL) |
| `zone_couverture` | Text | ✅ | Quartiers ou communes desservis |
| `rayon_km` | Decimal(5,2) | ✅ | Rayon de couverture en km (défaut: 5.00) |
| `latitude` | Decimal(9,6) | ❌ | Latitude GPS du prestataire |
| `longitude` | Decimal(9,6) | ❌ | Longitude GPS du prestataire |
| `location` | PointField | ❌ | Point géographique PostGIS (auto-généré) |
| `adresse` | Text | ✅ | Adresse complète |
| `quartier` | String(200) | ❌ | Quartier/Commune |
| `statut_kyc` | String(20) | ✅ | Statut de vérification : `'pending'`, `'verified'`, `'rejected'` |
| `document_identite` | FileField | ❌ | Document d'identité (URL du fichier) |
| `is_active` | Boolean | ✅ | Le prestataire peut recevoir des commandes (défaut: `true`) |
| `created` | DateTime | Auto | Date de création |
| `updated` | DateTime | Auto | Dernière modification |

### Choix disponibles

#### Type de prestataire (`type`)
```python
[
    ('pressing', 'Pressing'),
    ('fanico', 'Fanico')
]
```

#### Statut KYC (`statut_kyc`)
```python
[
    ('pending', 'En attente'),      # État initial
    ('verified', 'Vérifié'),        # Validé par l'admin
    ('rejected', 'Rejeté')          # Refusé par l'admin
]
```

### Méthodes utiles

#### `find_nearby(latitude, longitude, max_distance_km=10, provider_type=None)` (static)
Trouve les prestataires proches d'une position donnée.

**Paramètres:**
- `latitude` (float): Latitude de recherche
- `longitude` (float): Longitude de recherche
- `max_distance_km` (int): Distance maximale en km (défaut: 10)
- `provider_type` (String): `'pressing'` ou `'fanico'` (optionnel)

**Retour:** Liste de `Provider` triés par distance (du plus proche au plus éloigné)

**Exemple d'utilisation:**
```python
# Trouver tous les pressings dans un rayon de 5km
providers = Provider.find_nearby(
    latitude=5.3600,
    longitude=-4.0083,
    max_distance_km=5,
    provider_type='pressing'
)
```

#### `get_clients_in_coverage()`
Retourne les clients dans la zone de couverture du prestataire.

**Retour:** Liste de `User` (clients) triés par distance

#### `is_within_range(user_or_point, tolerance_km=0)`
Vérifie si un utilisateur ou point GPS est dans le rayon de couverture.

**Paramètres:**
- `user_or_point`: Instance `User` ou `Point` GeoDjango
- `tolerance_km` (float): Tolérance supplémentaire en km (défaut: 0)

**Retour:** Boolean

---

## Relations entre modèles

### User ↔ Provider (OneToOne)
- Un `User` peut avoir un profil `Provider` associé via `user.provider_profile`
- Un `Provider` est toujours lié à un `User` via `provider.user`

```python
# Accès du User vers Provider
if hasattr(user, 'provider_profile'):
    provider = user.provider_profile
    print(provider.nom_commercial)

# Accès du Provider vers User
user = provider.user
print(user.email)
```

### User → Group (ForeignKey)
- Un `User` peut appartenir à un `Group` Django
- Groupes typiques: `'client'`, `'provider'`, `'admin'`

### User → Role (ForeignKey)
- Un `User` peut avoir un `custom_role` pour des permissions granulaires
- Le `Role` est créé par un prestataire pour ses employés

---

## Exemples de données JSON

### User (Client)
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "jean_doe",
  "email": "jean@example.com",
  "phone": "+2250123456789",
  "phone_verified_at": "2025-11-03T10:30:00Z",
  "first_name": "Jean",
  "last_name": "Doe",
  "photo_profil": "/media/users/profils/2025/11/photo.jpg",
  "role": "",
  "group": {
    "id": 1,
    "name": "client"
  },
  "custom_role": null,
  "latitude": "5.360000",
  "longitude": "-4.008300",
  "location": {
    "type": "Point",
    "coordinates": [-4.0083, 5.3600]
  },
  "adresse": "Cocody, Angré 7ème tranche",
  "quartier": "Angré",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "date_inscription": "2025-10-15T08:00:00Z",
  "last_login": "2025-11-03T09:00:00Z"
}
```

### User (Prestataire avec profil)
```json
{
  "id": "987e6543-e21b-12d3-a456-426614174111",
  "username": "pressing_abc",
  "email": "contact@pressingabc.ci",
  "phone": "+2250709876543",
  "phone_verified_at": "2025-10-20T14:00:00Z",
  "first_name": "Mohamed",
  "last_name": "Kouassi",
  "photo_profil": "/media/users/profils/2025/10/mohamed.jpg",
  "role": "gerant",
  "group": {
    "id": 2,
    "name": "provider"
  },
  "custom_role": null,
  "latitude": null,
  "longitude": null,
  "location": null,
  "adresse": "",
  "quartier": "",
  "is_active": true,
  "is_staff": false,
  "is_superuser": false,
  "date_inscription": "2025-10-01T10:00:00Z",
  "last_login": "2025-11-03T08:30:00Z",
  "provider_profile": {
    "id": "456e7890-e12b-34d5-a678-426614174222",
    "type": "pressing",
    "nom_commercial": "Pressing ABC",
    "photo_local": "/media/providers/locaux/2025/10/local.jpg",
    "zone_couverture": "Cocody, Angré, Riviera",
    "rayon_km": "8.00",
    "latitude": "5.365000",
    "longitude": "-4.010000",
    "location": {
      "type": "Point",
      "coordinates": [-4.0100, 5.3650]
    },
    "adresse": "Boulevard Latrille, Cocody",
    "quartier": "Cocody Centre",
    "statut_kyc": "verified",
    "document_identite": "/media/providers/kyc/2025/10/cni.pdf",
    "is_active": true,
    "created": "2025-10-01T10:05:00Z",
    "updated": "2025-11-01T15:20:00Z"
  }
}
```

### Provider (Fanico)
```json
{
  "id": "789e0123-e45b-67d8-a901-426614174333",
  "user": {
    "id": "321e6789-e01b-23d4-a567-426614174444",
    "username": "fanico_express",
    "email": "fanico@example.com",
    "phone": "+2250501234567",
    "first_name": "Aya",
    "last_name": "Traoré"
  },
  "type": "fanico",
  "nom_commercial": "Fanico Express Aya",
  "photo_local": null,
  "zone_couverture": "Yopougon, Attécoubé, Plateau",
  "rayon_km": "12.00",
  "latitude": "5.345000",
  "longitude": "-4.050000",
  "location": {
    "type": "Point",
    "coordinates": [-4.0500, 5.3450]
  },
  "adresse": "Yopougon Sicogi, près du marché",
  "quartier": "Yopougon Sicogi",
  "statut_kyc": "pending",
  "document_identite": "/media/providers/kyc/2025/11/passeport.pdf",
  "is_active": true,
  "created": "2025-11-01T12:00:00Z",
  "updated": "2025-11-02T09:15:00Z"
}
```

### Recherche de prestataires proches (réponse API attendue)
```json
{
  "count": 2,
  "results": [
    {
      "id": "456e7890-e12b-34d5-a678-426614174222",
      "type": "pressing",
      "nom_commercial": "Pressing ABC",
      "photo_local": "/media/providers/locaux/2025/10/local.jpg",
      "latitude": "5.365000",
      "longitude": "-4.010000",
      "adresse": "Boulevard Latrille, Cocody",
      "quartier": "Cocody Centre",
      "rayon_km": "8.00",
      "statut_kyc": "verified",
      "is_active": true,
      "distance": 2.45
    },
    {
      "id": "789e0123-e45b-67d8-a901-426614174333",
      "type": "fanico",
      "nom_commercial": "Fanico Express Aya",
      "photo_local": null,
      "latitude": "5.345000",
      "longitude": "-4.050000",
      "adresse": "Yopougon Sicogi, près du marché",
      "quartier": "Yopougon Sicogi",
      "rayon_km": "12.00",
      "statut_kyc": "pending",
      "is_active": true,
      "distance": 5.78
    }
  ]
}
```

---

## Notes importantes pour le Frontend

### Géolocalisation
- Les champs `latitude` et `longitude` sont en décimal (format GPS standard)
- Le champ `location` est auto-généré par Django et utilise le format GeoJSON `Point`
- Coordonnées GeoJSON: `[longitude, latitude]` ⚠️ **Attention à l'ordre!**

### Authentification
- Le champ de connexion principal est `username`
- Le `phone` doit être unique et au format ivoirien
- Le `phone` peut nécessiter une vérification (champ `phone_verified_at`)

### Images et fichiers
- Les champs `ImageField` et `FileField` retournent des URL relatives (ex: `/media/users/profils/2025/11/photo.jpg`)
- Préfixer avec l'URL du backend pour obtenir l'URL complète

### Statuts
- Un prestataire doit avoir `statut_kyc='verified'` ET `is_active=True` pour recevoir des commandes
- Les clients n'ont pas de statut KYC

### Distance
- Les calculs de distance utilisent PostGIS et retournent des valeurs en kilomètres
- La propriété `rayon_km` du `Provider` détermine sa zone de couverture
- Utiliser les méthodes `find_nearby()` et `get_nearby_providers()` pour les recherches géolocalisées

### UUID
- Tous les IDs sont des UUID v4 au format string
- Ne pas envoyer d'ID lors de la création (auto-généré côté backend)

---

## Endpoints API suggérés

### Users
- `GET /api/users/me/` - Profil utilisateur connecté
- `PATCH /api/users/me/` - Mettre à jour le profil
- `POST /api/users/register/` - Inscription
- `GET /api/users/{id}/nearby-providers/` - Prestataires à proximité

### Providers
- `GET /api/providers/` - Liste des prestataires
- `GET /api/providers/{id}/` - Détail d'un prestataire
- `POST /api/providers/` - Créer un profil prestataire
- `GET /api/providers/nearby/` - Recherche géolocalisée (params: `lat`, `lng`, `distance`, `type`)
- `GET /api/providers/{id}/clients-in-coverage/` - Clients dans la zone

---

**Document généré le:** 2025-11-03  
**Version API:** Backend Django avec PostGIS  
**Contact:** Équipe Presso Dev

