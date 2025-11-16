# Guide d'utilisation des Mock Data - Presso

> Guide pour utiliser les données de simulation pendant le développement frontend

## 📁 Fichiers disponibles

1. **MOCK_DATA.ts** - Toutes les données mock (utilisateurs, commandes, prestataires, etc.)
2. **MOCK_SERVICE_EXAMPLE.ts** - Services simulés pour remplacer les appels API
3. **DOCUMENTATION_TYPESCRIPT_API.md** - Documentation des types TypeScript et API

---

## 🚀 Installation et Configuration

### 1. Copier les fichiers dans votre projet Vue.js

```bash
# Structure recommandée
src/
├── mocks/
│   ├── data.ts           # MOCK_DATA.ts
│   └── services.ts       # MOCK_SERVICE_EXAMPLE.ts
├── types/
│   └── index.ts          # Types TypeScript
└── stores/
    └── auth.ts           # Store Pinia pour l'authentification
```

### 2. Importer les types TypeScript

Créez un fichier `src/types/index.ts` avec tous les types (voir DOCUMENTATION_TYPESCRIPT_API.md) :

```typescript
// src/types/index.ts
export interface User {
  id: string;
  username: string;
  email: string;
  phone: string;
  // ... autres champs
}

export interface Provider {
  // ...
}

// ... tous les autres types
```

---

## 💡 Exemples d'utilisation

### Exemple 1 : Authentification (Connexion)

```vue
<!-- src/views/LoginView.vue -->
<template>
  <div class="login-container">
    <form @submit.prevent="handleLogin">
      <input v-model="form.username" type="text" placeholder="Email, téléphone ou username" />
      <input v-model="form.password" type="password" placeholder="Mot de passe" />
      <button type="submit" :disabled="loading">Se connecter</button>
      
      <p v-if="error" class="error">{{ error }}</p>
    </form>

    <!-- Aide pour les tests -->
    <div class="test-credentials" v-if="isDev">
      <h4>Comptes de test :</h4>
      <ul>
        <li><strong>Client:</strong> john_doe / Password123!</li>
        <li><strong>Pressing:</strong> pressing_excellence / PressingAdmin789!</li>
        <li><strong>Fanico:</strong> fanico_rapide / FanicoSecure321!</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { MockAuthService } from '@/mocks/services';

const router = useRouter();
const isDev = import.meta.env.DEV;

const form = ref({
  username: '',
  password: '',
});

const loading = ref(false);
const error = ref('');

async function handleLogin() {
  loading.value = true;
  error.value = '';

  try {
    const response = await MockAuthService.login(form.value);
    
    console.log('Connexion réussie:', response.user);
    
    // Rediriger selon le rôle
    if (response.user.role === 'client') {
      router.push('/client/dashboard');
    } else if (response.user.role === 'pressing' || response.user.role === 'fanico') {
      router.push('/provider/dashboard');
    } else {
      router.push('/dashboard');
    }
  } catch (err: any) {
    error.value = err.message || 'Erreur de connexion';
  } finally {
    loading.value = false;
  }
}
</script>
```

### Exemple 2 : Liste des prestataires

```vue
<!-- src/views/ProvidersView.vue -->
<template>
  <div class="providers-page">
    <h1>Prestataires disponibles</h1>

    <!-- Filtres -->
    <div class="filters">
      <button @click="filterType = null" :class="{ active: !filterType }">
        Tous
      </button>
      <button @click="filterType = 'pressing'" :class="{ active: filterType === 'pressing' }">
        Pressing
      </button>
      <button @click="filterType = 'fanico'" :class="{ active: filterType === 'fanico' }">
        Fanico
      </button>
    </div>

    <!-- Liste des prestataires -->
    <div class="providers-grid">
      <div 
        v-for="provider in filteredProviders" 
        :key="provider.id"
        class="provider-card"
        @click="goToProvider(provider.id)"
      >
        <img :src="provider.photo_local || defaultImage" alt="" />
        
        <div class="provider-info">
          <h3>{{ provider.nom_commercial }}</h3>
          <p class="type">{{ provider.type === 'pressing' ? 'Pressing' : 'Fanico' }}</p>
          <p class="location">📍 {{ provider.quartier }}</p>
          <p class="distance" v-if="provider.distance">
            🚗 {{ provider.distance.toFixed(1) }} km
          </p>
          
          <div class="rating">
            ⭐ {{ getProviderRating(provider.id) }} / 5
          </div>

          <span 
            class="status-badge" 
            :class="provider.statut_kyc"
          >
            {{ provider.statut_kyc === 'verified' ? '✓ Vérifié' : 'En attente' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { MockProviderService } from '@/mocks/services';
import mockData from '@/mocks/data';
import type { Provider } from '@/types';

const router = useRouter();
const providers = ref<Provider[]>([]);
const filterType = ref<'pressing' | 'fanico' | null>(null);
const defaultImage = 'https://via.placeholder.com/400x300?text=Pressing';

// Charger les prestataires
onMounted(async () => {
  try {
    providers.value = await MockProviderService.getAll();
  } catch (error) {
    console.error('Erreur de chargement:', error);
  }
});

// Filtrer les prestataires
const filteredProviders = computed(() => {
  if (!filterType.value) return providers.value;
  return providers.value.filter(p => p.type === filterType.value);
});

// Obtenir la note d'un prestataire
function getProviderRating(providerId: string): string {
  return mockData.utils.getProviderAverageRating(providerId);
}

// Naviguer vers le détail
function goToProvider(providerId: string) {
  router.push(`/providers/${providerId}`);
}
</script>

<style scoped>
.providers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  padding: 2rem;
}

.provider-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s;
}

.provider-card:hover {
  transform: translateY(-5px);
}

.status-badge.verified {
  background: #10b981;
  color: white;
}

.status-badge.pending {
  background: #f59e0b;
  color: white;
}
</style>
```

### Exemple 3 : Créer une commande

```vue
<!-- src/views/CreateOrderView.vue -->
<template>
  <div class="create-order">
    <h1>Nouvelle commande</h1>

    <form @submit.prevent="handleSubmit">
      <!-- Sélection du prestataire -->
      <div class="form-group">
        <label>Prestataire *</label>
        <select v-model="orderForm.provider" required>
          <option value="">-- Choisir un prestataire --</option>
          <option 
            v-for="provider in providers" 
            :key="provider.id"
            :value="provider.id"
          >
            {{ provider.nom_commercial }} ({{ provider.quartier }})
          </option>
        </select>
      </div>

      <!-- Adresse de collecte -->
      <div class="form-group">
        <label>Adresse de collecte *</label>
        <textarea 
          v-model="orderForm.adresse_collecte" 
          required
          placeholder="Ex: Cocody Riviera 3, Résidence les Lauriers"
        ></textarea>
      </div>

      <!-- Adresse de livraison -->
      <div class="form-group">
        <label>Adresse de livraison *</label>
        <textarea 
          v-model="orderForm.adresse_livraison" 
          required
        ></textarea>
        <label>
          <input type="checkbox" @change="useSameAddress" />
          Même adresse que la collecte
        </label>
      </div>

      <!-- Créneau de collecte -->
      <div class="form-group">
        <label>Date et heure de collecte souhaitée *</label>
        <input 
          type="datetime-local" 
          v-model="orderForm.creneau_collecte" 
          required
          :min="minDateTime"
        />
      </div>

      <!-- Articles -->
      <div class="articles-section">
        <h3>Articles à traiter</h3>
        
        <div 
          v-for="(item, index) in orderForm.items" 
          :key="index"
          class="article-item"
        >
          <select v-model="item.article_type" required>
            <option value="">-- Type d'article --</option>
            <option 
              v-for="type in articleTypes" 
              :key="type.id"
              :value="type.id"
            >
              {{ type.nom }}
            </option>
          </select>

          <select v-model="item.service" required>
            <option value="">-- Service --</option>
            <option 
              v-for="service in services" 
              :key="service.id"
              :value="service.id"
            >
              {{ service.label }}
            </option>
          </select>

          <input 
            type="number" 
            v-model.number="item.quantite"
            min="1"
            placeholder="Qté"
            required
          />

          <button 
            type="button" 
            @click="removeItem(index)"
            class="btn-remove"
          >
            ✕
          </button>
        </div>

        <button 
          type="button" 
          @click="addItem"
          class="btn-add-item"
        >
          + Ajouter un article
        </button>
      </div>

      <!-- Notes -->
      <div class="form-group">
        <label>Notes (optionnel)</label>
        <textarea 
          v-model="orderForm.notes_client"
          placeholder="Instructions particulières, taches à traiter, etc."
        ></textarea>
      </div>

      <!-- Total estimé -->
      <div class="order-summary">
        <h3>Récapitulatif</h3>
        <p>Articles: {{ calculatedTotal }} FCFA</p>
        <p>Frais de livraison: {{ orderForm.frais_livraison }} FCFA</p>
        <p class="total">Total: {{ calculatedTotal + orderForm.frais_livraison }} FCFA</p>
      </div>

      <!-- Boutons -->
      <div class="form-actions">
        <button type="button" @click="router.back()" class="btn-cancel">
          Annuler
        </button>
        <button type="submit" :disabled="loading" class="btn-submit">
          {{ loading ? 'Création...' : 'Créer la commande' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { MockProviderService, MockOrderService } from '@/mocks/services';
import mockData from '@/mocks/data';

const router = useRouter();

const providers = ref([]);
const articleTypes = ref([]);
const services = ref([]);
const loading = ref(false);

const orderForm = ref({
  provider: '',
  adresse_collecte: '',
  adresse_livraison: '',
  creneau_collecte: '',
  notes_client: '',
  frais_livraison: 500,
  items: [
    {
      article_type: '',
      service: '',
      quantite: 1,
      prix_unitaire: 500,
    }
  ],
});

// Date minimum (maintenant)
const minDateTime = computed(() => {
  const now = new Date();
  now.setMinutes(now.getMinutes() + 30); // Au moins 30 min à l'avance
  return now.toISOString().slice(0, 16);
});

// Total calculé
const calculatedTotal = computed(() => {
  return orderForm.value.items.reduce((sum, item) => {
    return sum + (item.prix_unitaire * item.quantite);
  }, 0);
});

onMounted(async () => {
  providers.value = await MockProviderService.getAll();
  articleTypes.value = mockData.articleTypes;
  services.value = mockData.services;
});

function useSameAddress(event: Event) {
  const checked = (event.target as HTMLInputElement).checked;
  if (checked) {
    orderForm.value.adresse_livraison = orderForm.value.adresse_collecte;
  }
}

function addItem() {
  orderForm.value.items.push({
    article_type: '',
    service: '',
    quantite: 1,
    prix_unitaire: 500,
  });
}

function removeItem(index: number) {
  if (orderForm.value.items.length > 1) {
    orderForm.value.items.splice(index, 1);
  }
}

async function handleSubmit() {
  loading.value = true;

  try {
    const orderData = {
      ...orderForm.value,
      total_estime: calculatedTotal.value,
      creneau_collecte: new Date(orderForm.value.creneau_collecte).toISOString(),
    };

    const order = await MockOrderService.create(orderData);
    
    console.log('Commande créée:', order);
    
    // Rediriger vers la page de paiement
    router.push(`/orders/${order.id}/payment`);
  } catch (error: any) {
    alert('Erreur: ' + error.message);
  } finally {
    loading.value = false;
  }
}
</script>
```

### Exemple 4 : Store Pinia avec Mock Data

```typescript
// src/stores/auth.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { MockAuthService } from '@/mocks/services';
import type { User } from '@/types';

export const useAuthStore = defineStore('auth', () => {
  // État
  const user = ref<User | null>(null);
  const isAuthenticated = ref(false);

  // Getters
  const userRole = computed(() => user.value?.role ?? null);
  const isPhoneVerified = computed(() => user.value?.phone_verified ?? false);

  // Actions
  async function login(username: string, password: string) {
    try {
      const response = await MockAuthService.login({ username, password });
      
      user.value = response.user;
      isAuthenticated.value = true;

      return response;
    } catch (error) {
      console.error('Erreur de connexion:', error);
      throw error;
    }
  }

  async function register(data: any) {
    try {
      const response = await MockAuthService.register(data);
      return response;
    } catch (error) {
      console.error('Erreur d\'inscription:', error);
      throw error;
    }
  }

  async function fetchProfile() {
    try {
      user.value = await MockAuthService.getProfile();
      isAuthenticated.value = true;
    } catch (error) {
      logout();
    }
  }

  function logout() {
    MockAuthService.logout();
    user.value = null;
    isAuthenticated.value = false;
  }

  // Initialiser au montage
  if (MockAuthService.isAuthenticated()) {
    fetchProfile();
  }

  return {
    user,
    isAuthenticated,
    userRole,
    isPhoneVerified,
    login,
    register,
    fetchProfile,
    logout,
  };
});
```

---

## 🔑 Comptes de test disponibles

### Clients

| Username | Email | Téléphone | Mot de passe |
|----------|-------|-----------|--------------|
| john_doe | john.doe@gmail.com | +2250123456789 | Password123! |
| marie_kouame | marie.kouame@yahoo.fr | +2250709876543 | SecurePass456! |

### Prestataires

| Username | Type | Email | Mot de passe |
|----------|------|-------|--------------|
| pressing_excellence | Pressing | contact@pressingexcellence.ci | PressingAdmin789! |
| fanico_rapide | Fanico | aya.traore@fanico.ci | FanicoSecure321! |

### Admin

| Username | Email | Mot de passe |
|----------|-------|--------------|
| admin_presso | admin@presso.ci | AdminPresso2025! |

---

## 📊 Données disponibles

### Statistiques des mock data :

- **5 utilisateurs** (2 clients, 2 prestataires, 1 admin)
- **4 prestataires** (2 pressings, 2 fanicos)
- **6 services** différents
- **6 types d'articles** (chemise, pantalon, robe, etc.)
- **5 matières** (coton, soie, laine, etc.)
- **7 tarifs** détaillés
- **3 commandes** avec différents statuts
- **6 articles** de commande
- **3 paiements** (completed, pending, failed)
- **2 avis** clients
- **6 permissions**
- **2 rôles** personnalisés

---

## 🎯 Fonctionnalités simulées

### ✅ Authentification
- Connexion avec username/email/phone
- Inscription
- Déconnexion
- Récupération du profil
- Demande et vérification OTP (code test: `123456`)

### ✅ Prestataires
- Liste de tous les prestataires
- Recherche par proximité
- Filtrage par type (pressing/fanico)
- Détails d'un prestataire
- Services proposés
- Tarifs
- Avis clients
- Note moyenne

### ✅ Commandes
- Liste des commandes (par utilisateur)
- Création de commande
- Détails d'une commande
- Articles de commande
- Annulation

### ✅ Paiements
- Initiation de paiement
- Vérification du statut
- Historique des paiements
- Simulation de succès/échec (80% succès)

---

## 🔄 Basculer entre Mock et API Réelle

Pour faciliter le passage des mocks à l'API réelle :

```typescript
// src/config/api.config.ts
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export const apiService = USE_MOCK 
  ? import('@/mocks/services')
  : import('@/services/api');
```

Puis dans `.env` :

```env
# Development avec mocks
VITE_USE_MOCK=true

# Production avec API réelle
VITE_USE_MOCK=false
VITE_API_URL=https://api.presso.ci
```

---

## 💡 Conseils

### 1. Utiliser les délais simulés
Les services mock incluent des délais (`await this.delay(ms)`) pour simuler la latence réseau réelle. Gardez-les pour tester les états de chargement.

### 2. Code OTP de test
Le code OTP par défaut est `123456`. Utilisez-le pour tester la vérification du téléphone.

### 3. Paiements simulés
Les paiements ont 80% de chances de réussir. Pour forcer un échec en test, modifiez le code dans `MockPaymentService.initiate()`.

### 4. Persistence locale
Les mocks utilisent `localStorage` pour persister l'authentification entre les rechargements de page.

### 5. UUID générés
Les nouveaux objets créés (commandes, utilisateurs) ont des UUID générés côté client pour la démo.

---

## 🐛 Débogage

### Voir les données en console

```typescript
import mockData from '@/mocks/data';

// Afficher toutes les données
console.log('Mock Data:', mockData);

// Afficher uniquement les utilisateurs
console.log('Users:', mockData.users);

// Afficher les commandes d'un utilisateur
const myOrders = mockData.utils.getOrdersByUser('user-id');
console.log('My Orders:', myOrders);
```

### Réinitialiser les données

Les données mock sont statiques sauf ce qui est ajouté dynamiquement. Pour réinitialiser :

```typescript
// Effacer le localStorage
localStorage.clear();

// Recharger la page
window.location.reload();
```

---

## 📝 TODO - Améliorations futures

- [ ] Ajouter plus de commandes avec différents statuts
- [ ] Simuler les notifications push
- [ ] Ajouter des images réelles pour les prestataires
- [ ] Ajouter plus d'avis clients
- [ ] Simuler le chat en temps réel
- [ ] Ajouter des statistiques pour le dashboard prestataire

---

## ❓ Questions fréquentes

### Pourquoi utiliser des mock data ?

- Développer le frontend **sans dépendre du backend**
- Tester l'UI avec des **données réalistes**
- **Démo** rapide sans serveur
- **Tests** automatisés plus faciles

### Comment ajouter mes propres données ?

Modifiez directement `MOCK_DATA.ts` :

```typescript
export const mockUsers: User[] = [
  // Ajoutez vos utilisateurs ici
  {
    id: 'mon-uuid',
    username: 'mon_user',
    // ...
  }
];
```

### Les données sont-elles sauvegardées ?

Non, les mock data sont en mémoire. Seuls les tokens d'auth sont en `localStorage`. Rechargez la page pour réinitialiser.

---

## 📞 Support

Pour toute question sur l'utilisation des mock data, consultez :
- `DOCUMENTATION_TYPESCRIPT_API.md` - Types et API
- `DOCUMENTATION_MODELES.md` - Schéma de la base de données

