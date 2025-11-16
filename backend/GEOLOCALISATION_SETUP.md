# 🗺️ Setup Géolocalisation - Presso

## 🚀 Installation rapide

### **1. Installation des dépendances système**

#### **Ubuntu/Debian (Développement avec SpatiaLite)**
```bash
sudo apt-get update
sudo apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libsqlite3-mod-spatialite \
    spatialite-bin
```

#### **macOS (Développement avec SpatiaLite)**
```bash
brew install gdal
brew install geos
brew install proj
brew install spatialite-tools
brew install libspatialite
```

#### **Ubuntu/Debian (Production avec PostGIS)**
```bash
sudo apt-get install -y \
    postgresql \
    postgresql-contrib \
    postgis \
    postgresql-14-postgis-3
```

### **2. Installation des packages Python**

```bash
# Activer le venv
cd /home/devfullstack/Bureau/CIACEMS\ TECHNOLOGIES/Business/presso_/Presso/backend
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### **3. Configuration PostGIS (Production)**

```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Créer la base de données
CREATE DATABASE presso_db;

# Se connecter à la base
\c presso_db

# Activer PostGIS
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;

# Vérifier l'installation
SELECT PostGIS_version();

# Quitter
\q
```

### **4. Configuration Django**

**backend/.env**
```env
# Pour PostGIS
DB_ENGINE=postgis
DB_NAME=presso_db
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432

# Autres configs
DJANGO_SECRET_KEY=votre_secret_key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

### **5. Migrations**

```bash
# Créer les migrations
python manage.py makemigrations

# Appliquer
python manage.py migrate

# Vérifier que les champs location sont créés
python manage.py dbshell
\d+ users_user  # Devrait montrer le champ "location"
\d+ providers_provider
\q
```

### **6. Initialisation des données de test**

```bash
# Initialiser groupes, permissions, templates
python manage.py init_groups
python manage.py init_permissions
python manage.py init_templates

# Initialiser les données géolocalisées
python manage.py init_geotest

# Ou tout en une fois
./init_multitenant.sh
python manage.py init_geotest
```

---

## 🧪 Tester la géolocalisation

### **Dans le shell Django**

```bash
python manage.py shell
```

```python
from apps.users.models import User
from apps.providers.models import Provider
from django.contrib.gis.geos import Point

# 1. Récupérer un client
client = User.objects.get(username='client_cocody')
print(f"Client: {client.get_full_name()}")
print(f"Position: {client.latitude}, {client.longitude}")
print(f"Location (Point): {client.location}")

# 2. Trouver les prestataires proches
nearby = client.get_nearby_providers(max_distance_km=10)
print(f"\n{nearby.count()} prestataires dans 10km:")

for provider in nearby:
    print(f"  - {provider.nom_commercial}: {provider.distance.km:.2f} km")

# 3. Filtrer par type
pressings = client.get_nearby_providers(
    max_distance_km=5,
    provider_type='pressing'
)
print(f"\n{pressings.count()} pressings dans 5km:")
for p in pressings:
    print(f"  - {p.nom_commercial}: {p.distance.km:.2f} km")

# 4. Vérifier la couverture
provider = Provider.objects.first()
print(f"\n{provider.nom_commercial}:")
print(f"  Rayon: {provider.rayon_km} km")
print(f"  Peut servir ce client: {provider.is_within_range(client)}")

# 5. Recherche par coordonnées
providers = Provider.find_nearby(
    latitude=5.3599517,
    longitude=-3.9598355,
    max_distance_km=10
)
print(f"\n{providers.count()} prestataires trouvés")
```

---

## 🔧 Troubleshooting

### **Erreur: "No module named 'django.contrib.gis'"**

GeoDjango n'est pas installé correctement.

```bash
# Vérifier GDAL
python -c "from osgeo import gdal; print(gdal.__version__)"

# Si erreur, réinstaller
sudo apt-get install --reinstall gdal-bin libgdal-dev
pip install GDAL==$(gdal-config --version) --global-option=build_ext --global-option="-I/usr/include/gdal"
```

### **Erreur: "Could not find the GDAL library"**

```bash
# Ubuntu/Debian
export GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
export GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# Ajouter au .bashrc ou .zshrc
echo 'export GDAL_LIBRARY_PATH=/usr/lib/libgdal.so' >> ~/.bashrc
echo 'export GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so' >> ~/.bashrc
source ~/.bashrc
```

### **Erreur SpatiaLite: "Unable to load the SpatiaLite library"**

```bash
# Ubuntu
sudo apt-get install libsqlite3-mod-spatialite

# Vérifier
python manage.py shell
>>> from django.contrib.gis.db.backends.spatialite.base import DatabaseWrapper
>>> print("SpatiaLite OK")
```

### **Erreur PostGIS: "type 'geometry' does not exist"**

```bash
# PostGIS n'est pas activé
sudo -u postgres psql presso_db
CREATE EXTENSION postgis;
\q

# Relancer les migrations
python manage.py migrate
```

### **Erreur: "distance() is not available"**

Le champ `location` n'est pas un PointField GeoDjango.

```bash
# Vérifier le modèle
python manage.py shell
>>> from apps.users.models import User
>>> u = User.objects.first()
>>> print(type(u.location))  # Devrait être Point
>>> print(u.location.geom_type)  # Devrait être "Point"
```

---

## 📊 Données de test créées

### **Prestataires (8)**

| Nom | Type | Quartier | Coordonnées |
|-----|------|----------|-------------|
| Pressing Riviera Premium | Pressing | Cocody Riviera 3 | 5.3599, -3.9598 |
| Fanico Plateau Express | Fanico | Plateau | 5.3238, -4.0084 |
| Pressing Marcory Zone 4 | Pressing | Marcory Zone 4 | 5.2897, -3.9866 |
| Fanico Yop City | Fanico | Yopougon | 5.3364, -4.0839 |
| Pressing Abobo Gare | Pressing | Abobo Gare | 5.4242, -4.0159 |
| Fanico Treichville | Fanico | Treichville | 5.2846, -4.0042 |
| Pressing 2 Plateaux | Pressing | Cocody 2 Plateaux | 5.3698, -3.9912 |
| Fanico Adjamé | Fanico | Adjamé | 5.3507, -4.0216 |

### **Clients (3)**

| Username | Nom | Quartier | Coordonnées |
|----------|-----|----------|-------------|
| client_cocody | Jean Kouassi | Cocody Riviera | 5.3599, -3.9598 |
| client_plateau | Marie Bamba | Plateau | 5.3238, -4.0084 |
| client_marcory | Koffi Yao | Marcory | 5.2897, -3.9866 |

**Mot de passe:** `presso2025`

---

## ✅ Checklist de vérification

- [ ] GDAL installé : `gdal-config --version`
- [ ] GEOS installé : `geos-config --version`
- [ ] SpatiaLite installé (dev) : `spatialite --version`
- [ ] PostGIS installé (prod) : `psql -c "SELECT PostGIS_version();"`
- [ ] Migrations appliquées : `python manage.py migrate`
- [ ] Champs location créés : Vérifier dans admin
- [ ] Données de test chargées : `python manage.py init_geotest`
- [ ] Recherche fonctionne : Tester dans shell

---

## 🎯 Prochaines étapes

1. ✅ Géolocalisation configurée
2. 🔄 Créer les APIs DRF pour recherche géolocalisée
3. 🔄 Intégrer une carte (Leaflet/Google Maps) dans Vue.js
4. 🔄 Implémenter la géolocalisation HTML5 côté client
5. 🔄 Ajouter le reverse geocoding (adresse → coordonnées)

---

**Votre système de géolocalisation est prêt ! 🗺️✨**

