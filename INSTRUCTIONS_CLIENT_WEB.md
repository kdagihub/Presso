# Instructions pour Agent Cursor - Application Client Web Pressow

## Contexte du Projet

**Pressow** est une marketplace de services de pressing/blanchisserie en Côte d'Ivoire. L'application backend Django REST est déjà développée. Le frontend prestataire (Vue.js 3) est terminé. Tu dois développer l'**interface client web** pour permettre aux clients de passer des commandes.

## Stack Technique

- **Frontend**: Vue.js 3 (Composition API + `<script setup>`)
- **State Management**: Pinia
- **Router**: Vue Router 4
- **HTTP Client**: Axios (déjà configuré dans `/src/services/api.ts`)
- **Styling**: CSS vanilla (pas de framework CSS)
- **Build Tool**: Vite

## Charte Graphique Obligatoire

```css
/* Couleurs principales */
--color-primary: #37A1EF;     /* Bleu Pressow - Boutons, liens, accents */
--color-accent: #F9A13B;      /* Orange Pressow - Badges, alertes */
--color-success: #10b981;     /* Vert - Validations, succès */
--color-white: #FFFFFF;       /* Fonds, textes sur couleur */
--color-background: #E3F2FB;  /* Fond pages auth */

/* Design tokens */
border-radius: 12px;          /* Cartes */
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);  /* Ombres légères */
font-family: system-ui, -apple-system, sans-serif;
```

**Principes UI/UX:**
- Design épuré et minimaliste
- Beaucoup d'espace blanc
- Icônes SVG inline (pas de FontAwesome)
- Responsive mobile-first
- Animations subtiles (transitions 0.2s)

## Architecture des Fichiers

Créer les fichiers dans la structure existante:

```
frontend/Pressow/Pressow/src/
├── Views/
│   └── DashboardClient/          # À CRÉER
│       ├── ClientDashboard.vue   # Page d'accueil client
│       ├── SearchPressings.vue   # Recherche de pressings par localisation
│       ├── PressingDetail.vue    # Détail d'un pressing + catalogue
│       ├── Cart.vue              # Panier
│       ├── Checkout.vue          # Paiement
│       ├── ClientOrders.vue      # Mes commandes
│       ├── OrderTracking.vue     # Suivi d'une commande
│       └── ClientProfile.vue     # Profil client
├── stores/
│   └── client.ts                 # À CRÉER - Store Pinia client
├── Components/
│   └── ComponentsClient/         # À CRÉER
│       ├── ClientLayout.vue      # Layout avec header/footer
│       ├── PressingCard.vue      # Carte pressing dans liste
│       ├── ServiceItem.vue       # Item de service dans panier
│       └── OrderCard.vue         # Carte commande dans historique
```

## API Backend Disponibles

### Authentification (déjà fonctionnel)
```
POST /api/auth/register/client/     - Inscription client
POST /api/auth/otp/verify/          - Vérification OTP
POST /api/auth/login/               - Connexion
POST /api/auth/refresh/             - Refresh token
GET  /api/auth/profile/             - Profil utilisateur
```

### Catalogue Public
```
GET /api/catalog/providers/<provider_id>/services/
    - Liste des services d'un pressing

GET /api/catalog/providers/<provider_id>/services/<offer_id>/details/
    - Détail d'un service avec tarifs
```

### Commandes Client
```
GET  /api/orders/                   - Mes commandes
POST /api/orders/                   - Créer une commande
GET  /api/orders/<order_id>/        - Détail commande
GET  /api/orders/<order_id>/delivery-code/  - Code OTP livraison
```

### Format de création de commande
```json
POST /api/orders/
{
  "provider_id": "uuid",
  "items": [
    {
      "provider_service_id": "uuid",
      "article_type_id": "uuid",
      "matiere_id": "uuid",  // optionnel
      "quantity": 2
    }
  ],
  "adresse_collecte": "Adresse complète",
  "latitude_collecte": 5.3600,
  "longitude_collecte": -4.0083,
  "adresse_livraison": "Adresse livraison",
  "creneau_collecte": "2026-01-25T10:00:00Z",
  "notes_client": "Instructions spéciales"
}
```

## Endpoints à implémenter côté Backend (si manquants)

### Recherche de pressings par localisation
```
GET /api/catalog/providers/nearby/?lat=5.36&lng=-4.00&radius=10
```

Tu devras peut-être créer cet endpoint si il n'existe pas. Voici le ViewSet à ajouter dans `backend/apps/api/viewsets/providers.py`:

```python
class NearbyProvidersView(APIView):
    """
    GET /api/catalog/providers/nearby/?lat=X&lng=Y&radius=10
    Liste les pressings proches avec leurs services
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = int(request.query_params.get('radius', 10))  # km
        
        # Filtrer par is_open=True et onboarding_completed=True
        providers = Provider.objects.filter(
            is_open=True,
            onboarding_completed=True
        )
        
        # TODO: Ajouter filtre géographique avec PostGIS
        # point = Point(float(lng), float(lat), srid=4326)
        # providers = providers.filter(location__distance_lte=(point, D(km=radius)))
        
        return Response([
            {
                'id': str(p.id),
                'nom_commercial': p.nom_commercial,
                'photo': p.photo.url if p.photo else None,
                'ville': p.ville,
                'adresse': p.adresse,
                'latitude': p.latitude,
                'longitude': p.longitude,
                'note_moyenne': 4.5,  # TODO: calculer
                'services_count': p.provider_services.count(),
            }
            for p in providers[:20]
        ])
```

## Pages à Développer (par priorité)

### 1. ClientDashboard.vue (Page d'accueil)
- Barre de recherche d'adresse/localisation
- Bouton "Me localiser" (GPS)
- Liste des pressings proches (cartes)
- Filtres: distance, services, note

### 2. PressingDetail.vue (Catalogue)
- Header avec photo, nom, note, adresse
- Liste des services avec prix
- Sélection d'articles + quantité
- Bouton "Ajouter au panier"

### 3. Cart.vue (Panier)
- Liste des articles sélectionnés
- Modifier quantité / supprimer
- Sous-total par pressing
- Bouton "Commander"

### 4. Checkout.vue (Finalisation)
- Résumé de commande
- Formulaire adresse collecte/livraison
- Sélection créneau
- **Paiement Mobile Money** (CinetPay simulation)
- Bouton "Payer X FCFA"

### 5. ClientOrders.vue (Mes commandes)
- Liste des commandes avec statut
- Filtres: en cours, terminées
- Click → OrderTracking

### 6. OrderTracking.vue (Suivi)
- Timeline du statut
- Infos pressing
- Code OTP quand statut = "ready"
- Bouton "Appeler le pressing"

## Store Pinia Client (stores/client.ts)

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

interface CartItem {
  providerId: string
  providerName: string
  providerServiceId: string
  serviceName: string
  articleTypeId?: string
  articleTypeName?: string
  matiereId?: string
  matiereName?: string
  prix: number
  quantity: number
}

interface NearbyProvider {
  id: string
  nom_commercial: string
  photo: string | null
  ville: string
  adresse: string
  latitude: number
  longitude: number
  note_moyenne: number
  services_count: number
}

export const useClientStore = defineStore('client', () => {
  // State
  const cart = ref<CartItem[]>([])
  const nearbyProviders = ref<NearbyProvider[]>([])
  const clientOrders = ref<any[]>([])
  const isLoading = ref(false)
  const currentLocation = ref<{lat: number, lng: number} | null>(null)

  // Computed
  const cartTotal = computed(() => 
    cart.value.reduce((sum, item) => sum + (item.prix * item.quantity), 0)
  )
  
  const cartItemsCount = computed(() => 
    cart.value.reduce((sum, item) => sum + item.quantity, 0)
  )

  // Actions
  async function fetchNearbyProviders(lat: number, lng: number, radius: number = 10) {
    isLoading.value = true
    try {
      const response = await api.get('/catalog/providers/nearby/', {
        params: { lat, lng, radius }
      })
      nearbyProviders.value = response.data
    } finally {
      isLoading.value = false
    }
  }

  function addToCart(item: CartItem) {
    const existing = cart.value.find(
      i => i.providerServiceId === item.providerServiceId 
        && i.articleTypeId === item.articleTypeId
    )
    if (existing) {
      existing.quantity += item.quantity
    } else {
      cart.value.push(item)
    }
    saveCart()
  }

  function removeFromCart(index: number) {
    cart.value.splice(index, 1)
    saveCart()
  }

  function clearCart() {
    cart.value = []
    saveCart()
  }

  function saveCart() {
    localStorage.setItem('presso_client_cart', JSON.stringify(cart.value))
  }

  function loadCart() {
    const saved = localStorage.getItem('presso_client_cart')
    if (saved) cart.value = JSON.parse(saved)
  }

  async function createOrder(orderData: any) {
    const response = await api.post('/orders/', orderData)
    clearCart()
    return response.data
  }

  async function fetchClientOrders() {
    const response = await api.get('/orders/')
    clientOrders.value = response.data
  }

  async function fetchOrderDeliveryCode(orderId: string) {
    const response = await api.get(`/orders/${orderId}/delivery-code/`)
    return response.data
  }

  return {
    cart,
    nearbyProviders,
    clientOrders,
    isLoading,
    currentLocation,
    cartTotal,
    cartItemsCount,
    fetchNearbyProviders,
    addToCart,
    removeFromCart,
    clearCart,
    loadCart,
    createOrder,
    fetchClientOrders,
    fetchOrderDeliveryCode,
  }
})
```

## Routes à ajouter (router/index.ts)

```typescript
// Routes Client
{
  path: '/client',
  component: () => import('@/Components/ComponentsClient/ClientLayout.vue'),
  meta: { requiresAuth: true, role: 'client' },
  children: [
    {
      path: '',
      name: 'ClientDashboard',
      component: () => import('@/Views/DashboardClient/ClientDashboard.vue'),
    },
    {
      path: 'search',
      name: 'SearchPressings',
      component: () => import('@/Views/DashboardClient/SearchPressings.vue'),
    },
    {
      path: 'pressing/:id',
      name: 'PressingDetail',
      component: () => import('@/Views/DashboardClient/PressingDetail.vue'),
    },
    {
      path: 'cart',
      name: 'Cart',
      component: () => import('@/Views/DashboardClient/Cart.vue'),
    },
    {
      path: 'checkout',
      name: 'Checkout',
      component: () => import('@/Views/DashboardClient/Checkout.vue'),
    },
    {
      path: 'orders',
      name: 'ClientOrders',
      component: () => import('@/Views/DashboardClient/ClientOrders.vue'),
    },
    {
      path: 'orders/:id',
      name: 'OrderTracking',
      component: () => import('@/Views/DashboardClient/OrderTracking.vue'),
    },
    {
      path: 'profile',
      name: 'ClientProfile',
      component: () => import('@/Views/DashboardClient/ClientProfile.vue'),
    },
  ],
},
```

## Navigation Guard à modifier

Dans le navigation guard, ajouter la logique pour rediriger les clients vers `/client` et les prestataires vers `/dashboard`:

```typescript
if (user.role === 'client') {
  if (!to.path.startsWith('/client')) {
    return { path: '/client' }
  }
} else if (user.role === 'provider_owner' || user.role === 'provider_staff') {
  if (!to.path.startsWith('/dashboard') && !to.path.startsWith('/onboarding')) {
    return { path: '/dashboard' }
  }
}
```

## Paiement (Simulation)

Pour le MVP, le paiement sera simulé:

1. L'utilisateur clique "Payer X FCFA"
2. Afficher un modal "Simulation de paiement"
3. Après 2 secondes, marquer comme payé
4. Créer la commande avec `payment_status: 'escrow'`

Plus tard, intégrer CinetPay avec leur SDK JavaScript.

## Tests à effectuer

1. **Inscription client** → Vérifier OTP → Connexion
2. **Recherche pressing** → Sélectionner un pressing
3. **Ajouter au panier** → Vérifier le total
4. **Checkout** → Remplir adresses → Simuler paiement
5. **Voir commande** → Vérifier le statut
6. **Code OTP livraison** → Quand statut "ready"

## Configuration Production

Dans `src/services/api.ts`, la baseURL doit être configurable:

```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  withCredentials: true,
})
```

Créer `.env.production`:
```
VITE_API_URL=https://api.pressow.com/api
```

## Commandes pour démarrer

```bash
cd frontend/Pressow/Pressow
npm install
npm run dev
```

Le serveur de développement tourne sur `http://localhost:5173`

## Questions fréquentes

**Q: Où est la documentation de l'API?**
R: Pas de Swagger, mais tu peux voir les serializers dans `backend/apps/api/serializers/` et les viewsets dans `backend/apps/api/viewsets/`.

**Q: Comment tester sans backend?**
R: Utilise les données mock dans les stores. Le backend doit tourner via Docker (`docker compose up -d`).

**Q: Leaflet pour les cartes?**
R: Oui, Leaflet est déjà installé. Voir l'exemple dans `OnboardingSetup.vue`.

---

**Bonne chance ! N'hésite pas à poser des questions si quelque chose n'est pas clair.**
