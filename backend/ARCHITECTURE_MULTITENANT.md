# 🏗️ Architecture Multitenant - Presso

## 📋 Vue d'ensemble

Presso utilise une **architecture multitenant hybride** permettant à chaque prestataire (pressing/fanico) d'avoir son propre espace isolé avec personnalisation complète, tout en partageant une infrastructure commune.

---

## 🎯 Concepts clés

### 1. **Tenant = Prestataire**

Chaque prestataire (Provider) est un **tenant** isolé avec :
- ✅ Ses propres services personnalisés
- ✅ Ses propres types d'articles
- ✅ Ses propres matières
- ✅ Ses propres rôles et permissions
- ✅ Ses propres paramètres
- ✅ Son propre dashboard (Vue.js)

### 2. **Templates vs Instances**

```
TEMPLATES (Globaux - Plateforme)
├── ServiceTemplate      → Créés par les admins
├── ArticleTypeTemplate  → Servent de base
└── MatiereTemplate      → Pour tous les prestataires

INSTANCES (Par tenant)
├── Service             → Personnalisés par chaque prestataire
├── ArticleType         → Basés sur templates (optionnel)
└── Matiere             → Uniques par prestataire
```

### 3. **Permissions granulaires**

```python
# Système à 3 niveaux :
Permission  →  Role (par provider)  →  User
    ↓              ↓                    ↓
 Code unique   Groupe perms      Utilisateur final
```

---

## 🏛️ Structure de l'app `core`

### **Modèles principaux**

#### `Permission`
```python
# Permissions disponibles dans le système
- code: view_orders, manage_services, etc.
- module: orders, services, tariffs, stats, staff, settings, customers
- is_active: Activé/désactivé
```

#### `Role`
```python
# Rôles personnalisés créés par chaque prestataire
- provider: ForeignKey vers Provider
- name: "Manager", "Opérateur", "Comptable", etc.
- permissions: ManyToMany vers Permission
- unique_together: (provider, name)
```

#### `ProviderSettings`
```python
# Configuration par prestataire
- business_name, logo, primary_color
- auto_accept_orders, require_payment_before
- min_order_amount, delivery_fee
- email/sms notifications
- opening_hours (JSON)
- metadata (JSON extensible)
```

#### `TenantMixin`
```python
# Mixin abstrait pour modèles tenant-specific
- provider: ForeignKey
- À hériter pour tous modèles isolés par tenant
```

---

## 🔄 Architecture des Services (Multitenant)

### **Avant (problématique)**
```python
# ❌ Services globaux partagés
Service.objects.all()  # Tous les prestataires voient les mêmes
```

### **Après (multitenant)**
```python
# ✅ Templates globaux + Instances personnalisées
ServiceTemplate.objects.all()      # Templates plateforme
Service.objects.all()               # Filtrés automatiquement par tenant
Service.objects.for_tenant(provider)  # Explicite
Service.all_objects.all()          # Pour admin global
```

### **Exemple de workflow**

1. **Admin plateforme** crée un `ServiceTemplate` "Lavage + Repassage"
2. **Prestataire A** crée son instance :
   ```python
   Service.objects.create(
       provider=pressing_abc,
       template=service_template,
       label="Lavage + Repassage Premium",
       mode_tarif='kg',
       duree_estimee=1440
   )
   ```
3. **Prestataire B** crée le sien (différent) :
   ```python
   Service.objects.create(
       provider=fanico_xyz,
       template=service_template,
       label="Lavage Express",
       mode_tarif='forfait',
       duree_estimee=720
   )
   ```

---

## 🛡️ Isolation & Sécurité

### **1. TenantMiddleware**
```python
# Identifie automatiquement le tenant de chaque requête
request.tenant  # Provider du user connecté
```

### **2. TenantManager**
```python
# Filtre automatiquement les querysets
from apps.core.managers import get_current_tenant, set_current_tenant

# Dans une vue API :
tenant = request.user.get_provider()
set_current_tenant(tenant)

# Tous les querysets sont filtrés automatiquement
services = Service.objects.all()  # Seulement ceux du tenant
```

### **3. Vérification des permissions**
```python
# Dans un ViewSet DRF :
if not request.user.has_custom_permission('manage_services'):
    raise PermissionDenied("Vous n'avez pas les permissions")
```

---

## 📊 Schéma de données

```
┌─────────────────────────────────────────────────────────┐
│                     NIVEAU PLATEFORME                     │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │ Permission   │  │ ServiceTemplate│  │ ArticleType  │ │
│  │  (Global)    │  │   (Global)     │  │  Template    │ │
│  └──────────────┘  └────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    NIVEAU PRESTATAIRE                     │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │ Provider     │←─┤ ProviderSettings│←─│ Role         │ │
│  │              │  │                 │  │ (custom)     │ │
│  └──────┬───────┘  └────────────────┘  └──────────────┘ │
│         │                                                 │
│         ├─→ Service (instances)                           │
│         ├─→ ArticleType (instances)                       │
│         ├─→ Matiere (instances)                           │
│         ├─→ Order                                         │
│         └─→ Tariff                                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                      NIVEAU UTILISATEUR                   │
│  ┌──────────────┐                                        │
│  │ User         │                                        │
│  │ - group      │  (Django groups)                       │
│  │ - custom_role│  (Rôle par prestataire)                │
│  │ - provider   │  (Via custom_role ou provider_profile) │
│  └──────────────┘                                        │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Commandes d'initialisation

```bash
# 1. Créer les migrations
python manage.py makemigrations

# 2. Appliquer les migrations
python manage.py migrate

# 3. Initialiser les groupes Django (client, pressing, fanico, etc.)
python manage.py init_groups

# 4. Initialiser les permissions du système
python manage.py init_permissions

# 5. Initialiser les templates (services, articles, matières)
python manage.py init_templates

# 6. Créer un superutilisateur
python manage.py createsuperuser
```

---

## 🎨 Utilisation dans les APIs DRF

### **ViewSet avec isolation automatique**

```python
from rest_framework import viewsets
from apps.core.managers import set_current_tenant

class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()  # Filtré auto par tenant
    serializer_class = ServiceSerializer
    
    def get_queryset(self):
        # Le middleware a déjà défini request.tenant
        # Service.objects.all() est déjà filtré
        return super().get_queryset()
    
    def perform_create(self, serializer):
        # Associer automatiquement au tenant
        serializer.save(provider=self.request.tenant)
```

### **Permission personnalisée**

```python
from rest_framework.permissions import BasePermission

class HasManageServicesPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.has_custom_permission('view_services')
        return request.user.has_custom_permission('manage_services')

class ServiceViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, HasManageServicesPermission]
    # ...
```

---

## 🔑 Gestion des rôles (Exemple)

### **Créer un rôle personnalisé**

```python
from apps.core.models import Role, Permission

# Manager peut tout voir mais pas modifier les tarifs
manager_role = Role.objects.create(
    provider=my_provider,
    name="Manager",
    description="Gère les commandes et le personnel"
)

manager_role.permissions.add(
    Permission.objects.get(code='view_orders'),
    Permission.objects.get(code='manage_orders'),
    Permission.objects.get(code='view_services'),
    Permission.objects.get(code='view_stats'),
    Permission.objects.get(code='view_staff'),
)

# Opérateur voit seulement les commandes
operateur_role = Role.objects.create(
    provider=my_provider,
    name="Opérateur",
    description="Traite les commandes"
)

operateur_role.permissions.add(
    Permission.objects.get(code='view_orders'),
    Permission.objects.get(code='change_order_status'),
)
```

### **Assigner un rôle à un utilisateur**

```python
user.custom_role = manager_role
user.save()

# Vérifier les permissions
user.has_custom_permission('view_orders')  # True
user.has_custom_permission('manage_tariffs')  # False
```

---

## 📱 Intégration Frontend Vue.js

### **Récupérer les données du tenant**

```javascript
// API: /api/v1/tenant/me/
{
  "provider": {
    "id": "uuid",
    "nom_commercial": "Pressing ABC",
    "type": "pressing"
  },
  "settings": {
    "business_name": "Pressing ABC Premium",
    "logo": "/media/logos/abc.png",
    "primary_color": "#3b82f6"
  },
  "permissions": [
    "view_orders",
    "manage_orders",
    "view_stats"
  ]
}
```

### **Protéger les routes Vue.js**

```javascript
// router/index.js
{
  path: '/dashboard/services',
  component: ServicesView,
  meta: {
    requiresAuth: true,
    requiredPermission: 'view_services'
  }
}

// router/guards.js
router.beforeEach((to, from, next) => {
  if (to.meta.requiredPermission) {
    if (store.getters.hasPermission(to.meta.requiredPermission)) {
      next()
    } else {
      next('/403')
    }
  }
})
```

---

## ✅ Avantages de cette architecture

1. **Isolation totale** : Chaque prestataire ne voit que ses données
2. **Personnalisation complète** : Services, articles, rôles personnalisés
3. **Permissions granulaires** : Contrôle fin des accès
4. **Scalabilité** : Facile d'ajouter de nouveaux prestataires
5. **Maintenance** : Templates centralisés, instances distribuées
6. **API-ready** : Conçu pour DRF + Vue.js

---

## 🎓 Bonnes pratiques

### ✅ À FAIRE
- Toujours utiliser `TenantManager` pour les modèles tenant-specific
- Vérifier les permissions dans les ViewSets
- Associer automatiquement `provider` dans `perform_create()`
- Utiliser `request.tenant` plutôt que `request.user.provider_profile`

### ❌ À ÉVITER
- Ne jamais accéder directement aux données d'un autre tenant
- Ne pas bypasser les managers (utiliser `.all_objects` uniquement pour admin)
- Ne pas oublier d'ajouter `provider` lors de la création d'objets
- Ne pas mélanger templates et instances dans les mêmes vues

---

## 📚 Prochaines étapes

1. ✅ Modélisation terminée
2. 🔄 Créer les serializers DRF
3. 🔄 Créer les ViewSets avec permissions
4. 🔄 Développer les dashboards Vue.js
5. 🔄 Tests unitaires et d'intégration
6. 🔄 Documentation API (Swagger)

---

**Architecture conçue pour être robuste, évolutive et sécurisée** ✨

