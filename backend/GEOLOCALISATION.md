# 🗺️ Géolocalisation - Presso

## 📋 Vue d'ensemble

Presso intègre un système de **géolocalisation complet** basé sur **GeoDjango** et **PostGIS** permettant de :
- 📍 Localiser les clients et prestataires
- 🔍 Rechercher les prestataires les plus proches
- 📏 Calculer des distances précises
- 🗺️ Afficher sur une carte (Leaflet, Google Maps, etc.)
- 🎯 Filtrer par rayon de couverture

---

## 🏗️ Architecture

### **Technologies utilisées**

- **GeoDjango** : Extension Django pour données géospatiales
- **PostGIS** : Extension PostgreSQL pour géométrie (production)
- **SpatiaLite** : Extension SQLite pour développement
- **SRID 4326** : Standard mondial GPS (WGS84)

### **Modèles avec géolocalisation**

```python
# User (Client)
- latitude, longitude : DecimalField
- location : PointField (GeoDjango)
- adresse, quartier : TextField

# Provider (Prestataire)
- latitude, longitude : DecimalField
- location : PointField (GeoDjango)
- adresse, quartier : TextField
- rayon_km : Rayon de couverture
```

---

## 🚀 Configuration

### **1. Installation des dépendances**

#### **Pour développement (SQLite + SpatiaLite)**

```bash
# Ubuntu/Debian
sudo apt-get install gdal-bin libgdal-dev
sudo apt-get install libsqlite3-mod-spatialite

# macOS
brew install gdal
brew install spatialite-tools
```

#### **Pour production (PostgreSQL + PostGIS)**

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgis

# Créer la base avec PostGIS
sudo -u postgres psql
CREATE DATABASE presso_db;
\c presso_db
CREATE EXTENSION postgis;
\q
```

### **2. Configuration settings.py**

**Développement (SpatiaLite - déjà configuré)**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.spatialite',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**Production (PostGIS)**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'presso_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### **3. Variables d'environnement (.env)**

```env
# Pour PostGIS
DB_ENGINE=postgis
DB_NAME=presso_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

---

## 💻 Utilisation

### **1. Enregistrer la position d'un utilisateur**

```python
from apps.users.models import User
from django.contrib.gis.geos import Point

# Méthode 1 : Lat/Lng (automatique)
user = User.objects.get(username='client1')
user.latitude = 5.3599517  # Abidjan, Cocody
user.longitude = -3.9598355
user.adresse = "Cocody, Riviera 3"
user.quartier = "Cocody"
user.save()  # location est créé automatiquement

# Méthode 2 : Point direct
user.location = Point(-3.9598355, 5.3599517)  # (lng, lat) !
user.save()
```

### **2. Trouver les prestataires les plus proches**

```python
# Depuis un client
client = User.objects.get(username='client1')

# Tous les prestataires dans 10km
nearby = client.get_nearby_providers(max_distance_km=10)

# Seulement les pressings dans 5km
pressings = client.get_nearby_providers(
    max_distance_km=5,
    provider_type='pressing'
)

# Afficher avec distances
for provider in pressings:
    print(f"{provider.nom_commercial} - {provider.distance.km:.2f} km")
```

### **3. Recherche par coordonnées GPS**

```python
from apps.providers.models import Provider

# Trouver prestataires proches d'une position
latitude = 5.3599517
longitude = -3.9598355

providers = Provider.find_nearby(
    latitude=latitude,
    longitude=longitude,
    max_distance_km=10,
    provider_type='pressing'
)

for p in providers:
    print(f"{p.nom_commercial} - {p.distance.km:.2f} km")
```

### **4. Vérifier si un client est dans la zone de couverture**

```python
provider = Provider.objects.get(nom_commercial='Pressing ABC')
client = User.objects.get(username='client1')

# Vérifier si le client est dans le rayon
if provider.is_within_range(client):
    print("✅ Le prestataire peut servir ce client")
else:
    print("❌ Client hors zone de couverture")

# Avec tolérance supplémentaire
if provider.is_within_range(client, tolerance_km=2):
    print("✅ Dans la zone (avec 2km de tolérance)")
```

### **5. Calculer une distance**

```python
client = User.objects.get(username='client1')
provider = Provider.objects.get(nom_commercial='Pressing ABC')

distance_km = client.calculate_distance_to(provider)
print(f"Distance : {distance_km} km")
```

### **6. Obtenir les clients dans la zone d'un prestataire**

```python
provider = Provider.objects.get(nom_commercial='Pressing ABC')

# Tous les clients dans le rayon de couverture
clients = provider.get_clients_in_coverage()

for client in clients:
    print(f"{client.get_full_name()} - {client.distance.km:.2f} km")
```

---

## 🎨 API DRF - Endpoints suggérés

### **Recherche de prestataires**

```python
# views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.geos import Point

class ProviderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Provider.objects.filter(is_active=True, statut_kyc='verified')
    serializer_class = ProviderSerializer
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """
        GET /api/providers/nearby/?lat=5.3599517&lng=-3.9598355&radius=10&type=pressing
        """
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 10))
        provider_type = request.query_params.get('type')
        
        if not lat or not lng:
            return Response({'error': 'lat et lng requis'}, status=400)
        
        providers = Provider.find_nearby(
            latitude=float(lat),
            longitude=float(lng),
            max_distance_km=radius,
            provider_type=provider_type
        )
        
        # Ajouter la distance au serializer
        data = []
        for provider in providers:
            serialized = ProviderSerializer(provider).data
            serialized['distance_km'] = round(provider.distance.km, 2)
            data.append(serialized)
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def check_coverage(self, request, pk=None):
        """
        POST /api/providers/{id}/check_coverage/
        Body: {"latitude": 5.3599517, "longitude": -3.9598355}
        """
        provider = self.get_object()
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        
        if not lat or not lng:
            return Response({'error': 'latitude et longitude requis'}, status=400)
        
        point = Point(float(lng), float(lat))
        in_range = provider.is_within_range(point)
        
        return Response({
            'in_coverage': in_range,
            'provider': provider.nom_commercial,
            'rayon_km': float(provider.rayon_km)
        })
```

### **Serializer avec distance**

```python
# serializers.py
from rest_framework import serializers

class ProviderSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()
    
    class Meta:
        model = Provider
        fields = [
            'id', 'nom_commercial', 'type', 
            'latitude', 'longitude', 'adresse', 'quartier',
            'rayon_km', 'photo_local', 'distance_km'
        ]
    
    def get_distance_km(self, obj):
        # Si distance est annotée dans le queryset
        if hasattr(obj, 'distance'):
            return round(obj.distance.km, 2)
        return None
```

---

## 🗺️ Intégration Frontend (Vue.js)

### **Afficher une carte Leaflet**

```vue
<template>
  <div>
    <div id="map" style="height: 500px;"></div>
  </div>
</template>

<script>
import L from 'leaflet';

export default {
  mounted() {
    this.initMap();
    this.loadNearbyProviders();
  },
  
  methods: {
    initMap() {
      // Initialiser la carte centrée sur Abidjan
      this.map = L.map('map').setView([5.3599517, -3.9598355], 13);
      
      // Ajouter le tile layer (OpenStreetMap)
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
      }).addTo(this.map);
      
      // Marqueur de l'utilisateur
      this.userMarker = L.marker([5.3599517, -3.9598355], {
        icon: L.icon({
          iconUrl: '/icons/user-marker.png',
          iconSize: [32, 32]
        })
      }).addTo(this.map)
        .bindPopup('Votre position');
    },
    
    async loadNearbyProviders() {
      const userLat = 5.3599517;
      const userLng = -3.9598355;
      
      const response = await fetch(
        `/api/providers/nearby/?lat=${userLat}&lng=${userLng}&radius=10`
      );
      const providers = await response.json();
      
      // Ajouter les marqueurs des prestataires
      providers.forEach(provider => {
        const marker = L.marker([provider.latitude, provider.longitude], {
          icon: L.icon({
            iconUrl: provider.type === 'pressing' 
              ? '/icons/pressing-marker.png' 
              : '/icons/fanico-marker.png',
            iconSize: [32, 32]
          })
        }).addTo(this.map);
        
        marker.bindPopup(`
          <strong>${provider.nom_commercial}</strong><br>
          Type: ${provider.type}<br>
          Distance: ${provider.distance_km} km<br>
          <a href="/provider/${provider.id}">Voir le profil</a>
        `);
      });
    }
  }
}
</script>
```

### **Obtenir la position GPS du navigateur**

```javascript
// composables/useGeolocation.js
export function useGeolocation() {
  const getUserPosition = () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject('Géolocalisation non supportée');
        return;
      }
      
      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy
          });
        },
        (error) => reject(error),
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    });
  };
  
  return { getUserPosition };
}

// Dans un composant Vue
import { useGeolocation } from '@/composables/useGeolocation';

const { getUserPosition } = useGeolocation();

async function findNearbyProviders() {
  try {
    const position = await getUserPosition();
    
    // Sauvegarder la position du user
    await api.patch('/api/users/me/', {
      latitude: position.latitude,
      longitude: position.longitude
    });
    
    // Charger les prestataires proches
    const providers = await api.get('/api/providers/nearby/', {
      params: {
        lat: position.latitude,
        lng: position.longitude,
        radius: 10
      }
    });
    
    console.log(`${providers.length} prestataires trouvés`);
  } catch (error) {
    console.error('Erreur géolocalisation:', error);
  }
}
```

---

## 📊 Exemples de positions (Abidjan, Côte d'Ivoire)

```python
# Coordonnées de référence pour tests

ABIDJAN_POSITIONS = {
    'cocody': {
        'latitude': 5.3599517,
        'longitude': -3.9598355,
        'quartier': 'Cocody Riviera'
    },
    'plateau': {
        'latitude': 5.3238665,
        'longitude': -4.0084323,
        'quartier': 'Plateau'
    },
    'yopougon': {
        'latitude': 5.3364208,
        'longitude': -4.0839411,
        'quartier': 'Yopougon'
    },
    'abobo': {
        'latitude': 5.4242082,
        'longitude': -4.0159683,
        'quartier': 'Abobo'
    },
    'marcory': {
        'latitude': 5.2897848,
        'longitude': -3.9866547,
        'quartier': 'Marcory'
    },
    'treichville': {
        'latitude': 5.2846284,
        'longitude': -4.0042634,
        'quartier': 'Treichville'
    }
}
```

---

## 🧪 Tests

### **Management command de test**

```python
# apps/core/management/commands/init_geolocations.py
from django.core.management.base import BaseCommand
from apps.providers.models import Provider
from apps.users.models import User

class Command(BaseCommand):
    help = 'Initialise des données de test avec géolocalisation'
    
    def handle(self, *args, **options):
        # Créer des prestataires à différents endroits
        positions = [
            ('Pressing Cocody', 'pressing', 5.3599517, -3.9598355, 'Cocody'),
            ('Fanico Plateau', 'fanico', 5.3238665, -4.0084323, 'Plateau'),
            ('Pressing Marcory', 'pressing', 5.2897848, -3.9866547, 'Marcory'),
        ]
        
        for nom, type_p, lat, lng, quartier in positions:
            provider, created = Provider.objects.get_or_create(
                nom_commercial=nom,
                defaults={
                    'type': type_p,
                    'latitude': lat,
                    'longitude': lng,
                    'quartier': quartier,
                    'adresse': f'Abidjan, {quartier}',
                    'rayon_km': 5.0,
                    'statut_kyc': 'verified',
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ {nom} créé'))
```

---

## ✅ Bonnes pratiques

1. **Toujours stocker lat/lng ET location** - Le PointField est créé automatiquement
2. **Utiliser SRID 4326** - Standard GPS mondial
3. **Indexer les champs location** - Pour performances
4. **Vérifier KYC** - Seulement les prestataires vérifiés
5. **Gérer les permissions** - Protéger les positions sensibles
6. **Fallback** - Prévoir un mode sans géoloc (saisie manuelle)

---

## 🚨 Troubleshooting

### **Erreur: "No module named 'django.contrib.gis'"**
```bash
# Installer les dépendances système
sudo apt-get install gdal-bin libgdal-dev libgeos-dev
pip install psycopg2-binary
```

### **Erreur SpatiaLite**
```bash
sudo apt-get install libsqlite3-mod-spatialite
# Ou sur macOS
brew install spatialite-tools
```

### **PostGIS non trouvé**
```bash
sudo apt-get install postgresql postgis
sudo -u postgres psql -c "CREATE EXTENSION postgis;"
```

---

**Votre plateforme est maintenant prête pour la géolocalisation ! 🗺️🚀**

