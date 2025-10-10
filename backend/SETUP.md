# 🧼 Guide d'installation - Presso Backend

## 📦 Structure des apps créées

Toutes les apps Django ont été créées dans le répertoire `apps/` :

- ✅ **users** - Gestion des utilisateurs avec authentification multi-identifiants
- ✅ **providers** - Fiches prestataires (Pressings & Fanicos)
- ✅ **services** - Types de services, articles et matières
- ✅ **tariffs** - Tarification personnalisée par prestataire
- ✅ **orders** - Gestion des commandes
- ✅ **order_items** - Articles contenus dans les commandes
- ✅ **payments** - Suivi des paiements Mobile Money
- ✅ **reviews** - Système de notation et avis

---

## 🚀 Étapes d'initialisation

### 1️⃣ Activer le virtualenv

```bash
cd /home/devfullstack/Bureau/CIACEMS\ TECHNOLOGIES/Business/presso_/Presso/backend
source venv/bin/activate
```

### 2️⃣ Installer Pillow (pour les ImageField)

```bash
pip install Pillow
```

### 3️⃣ Créer les migrations

```bash
python manage.py makemigrations
```

### 4️⃣ Appliquer les migrations

```bash
python manage.py migrate
```

### 5️⃣ Créer un superutilisateur

```bash
python manage.py createsuperuser
```

**Informations à fournir :**
- Username
- Email
- **Téléphone** (format : +225XXXXXXXXXX ou XXXXXXXXXX)
- Password

### 6️⃣ Initialiser les groupes Django

```bash
python manage.py init_groups
```

Cela créera les groupes :
- client
- pressing
- fanico
- livreur
- admin

### 7️⃣ Initialiser les données de base

```bash
python manage.py init_services
```

Cela créera :
- **Services** : Lavage simple, Lavage + Repassage, Repassage seul, Service Express, Nettoyage à sec
- **Types d'articles** : Chemise, Pantalon, Jean, Robe, Costume, etc.
- **Matières** : Coton, Lin, Soie, Laine, Polyester, Denim, Cuir, etc.

### 8️⃣ Lancer le serveur de développement

```bash
python manage.py runserver
```

Accéder à l'admin : **http://127.0.0.1:8000/admin/**

---

## 🎯 Commandes rapides (tout-en-un)

```bash
# Activer le venv
source venv/bin/activate

# Installer dépendances
pip install Pillow

# Créer et appliquer les migrations
python manage.py makemigrations
python manage.py migrate

# Créer le superuser
python manage.py createsuperuser

# Initialiser les données
python manage.py init_groups
python manage.py init_services

# Lancer le serveur
python manage.py runserver
```

---

## 📋 Modèles créés

- **User** - Utilisateur personnalisé avec téléphone et RBAC
- **Provider** - Prestataire (pressing/fanico)
- **Service** - Type de service
- **ArticleType** - Type d'article
- **Matiere** - Matière du vêtement
- **ProviderService** - Service proposé par un prestataire
- **Tariff** - Tarif personnalisé
- **Order** - Commande
- **OrderItem** - Article de commande
- **Payment** - Paiement Mobile Money
- **Review** - Avis client

---

**Stack technique :**
- Django 5.2.7
- Python 3.12
- UUID pour tous les IDs
- RBAC avec Groups + roles personnalisés

