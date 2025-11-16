# Types TypeScript et Documentation API - Presso

> Documentation pour l'intégration frontend Vue.js avec TypeScript

## 📋 Table des matières

1. [Types TypeScript](#types-typescript)
2. [API d'Authentification](#api-dauthentification)
3. [Exemples d'utilisation Vue.js](#exemples-dutilisation-vuejs)

---

## Types TypeScript

### 1. Utilisateurs et Authentification

```typescript
// Type de base pour l'utilisateur
export interface User {
  id: string; // UUID
  username: string;
  email: string;
  phone: string; // Format: +225XXXXXXXXXX
  phone_verified: boolean;
  phone_verified_at: string | null; // ISO 8601 date string
  first_name: string;
  last_name: string;
  photo_profil: string | null; // URL de l'image
  role: string;
  role_display: string;
  custom_role: CustomRole | null;
  latitude: number | null;
  longitude: number | null;
  adresse: string;
  quartier: string;
  date_inscription: string; // ISO 8601 date string
  is_active: boolean;
  provider?: ProviderBasicInfo | null;
  permissions: string[];
}

// Informations basiques du prestataire dans le profil user
export interface ProviderBasicInfo {
  id: string;
  nom_commercial: string;
  type: 'pressing' | 'fanico';
  adresse: string;
  quartier: string;
}

// Rôle personnalisé
export interface CustomRole {
  id: string;
  provider_id: string;
  name: string;
  description: string;
  is_active: boolean;
}
```

### 2. Prestataires

```typescript
// Type complet pour un prestataire
export interface Provider {
  id: string;
  user: string; // UUID de l'utilisateur
  type: 'pressing' | 'fanico';
  nom_commercial: string;
  photo_local: string | null; // URL de l'image
  zone_couverture: string;
  rayon_km: number;
  latitude: number | null;
  longitude: number | null;
  adresse: string;
  quartier: string;
  statut_kyc: 'pending' | 'verified' | 'rejected';
  document_identite: string | null; // URL du document
  is_active: boolean;
  created: string; // ISO 8601
  updated: string; // ISO 8601
  distance?: number; // Distance en km (si recherche géolocalisée)
}

// Pour les listes simplifiées
export interface ProviderListItem {
  id: string;
  nom_commercial: string;
  type: 'pressing' | 'fanico';
  quartier: string;
  statut_kyc: 'pending' | 'verified' | 'rejected';
  is_active: boolean;
  distance?: number;
}
```

### 3. Services et Catalogue

```typescript
// Template de service (global)
export interface ServiceTemplate {
  id: string;
  label: string;
  description: string;
  mode_tarif: 'kg' | 'piece' | 'forfait';
  duree_estimee: number; // en minutes
  icone: string;
  is_active: boolean;
  created: string;
  updated: string;
}

// Service personnalisé par prestataire
export interface Service {
  id: string;
  provider: string; // UUID du prestataire
  template: string | null; // UUID du template
  label: string;
  description: string;
  mode_tarif: 'kg' | 'piece' | 'forfait';
  duree_estimee: number; // en minutes
  icone: string;
  is_active: boolean;
  created: string;
  updated: string;
}

// Type d'article
export interface ArticleType {
  id: string;
  provider: string; // UUID du prestataire
  template: string | null;
  nom: string;
  description: string;
  created: string;
}

// Matière
export interface Matiere {
  id: string;
  provider: string;
  template: string | null;
  nom: string;
  description: string;
  created: string;
}
```

### 4. Tarification

```typescript
// Service proposé par un prestataire avec prix
export interface ProviderService {
  id: string;
  provider: string; // UUID
  service: string; // UUID
  service_details?: Service; // Détails du service (si inclus)
  prix_base: number; // En FCFA
  delai: number; // En heures
  is_available: boolean;
  created: string;
  updated: string;
}

// Tarification détaillée
export interface Tariff {
  id: string;
  provider: string;
  article_type: string; // UUID
  article_type_details?: ArticleType;
  matiere: string | null; // UUID
  matiere_details?: Matiere;
  service: string; // UUID
  service_details?: Service;
  prix: number; // En FCFA
  created: string;
  updated: string;
}
```

### 5. Commandes

```typescript
// Statuts de commande
export type OrderStatus = 
  | 'pending'       // En attente
  | 'confirmed'     // Confirmée
  | 'collected'     // Collectée
  | 'in_progress'   // En cours
  | 'ready'         // Prête
  | 'delivered'     // Livrée
  | 'cancelled';    // Annulée

// Commande complète
export interface Order {
  id: string;
  numero: string; // Ex: "ORD-2025-0001"
  client: string; // UUID
  client_details?: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
    phone: string;
  };
  provider: string; // UUID
  provider_details?: ProviderBasicInfo;
  statut: OrderStatus;
  
  // Adresses
  adresse_collecte: string;
  latitude_collecte: number | null;
  longitude_collecte: number | null;
  adresse_livraison: string;
  latitude_livraison: number | null;
  longitude_livraison: number | null;
  
  // Créneaux et dates
  creneau_collecte: string; // ISO 8601
  creneau_livraison: string | null; // ISO 8601
  date_collecte: string | null; // ISO 8601
  date_livraison: string | null; // ISO 8601
  
  // Montants
  total_estime: number; // FCFA
  total_final: number | null; // FCFA
  frais_livraison: number; // FCFA
  
  // Notes
  notes_client: string;
  notes_provider: string;
  
  // Preuve
  signature_client: string | null; // URL de l'image
  
  // Métadonnées
  created: string; // ISO 8601
  updated: string; // ISO 8601
  
  // Relations (si incluses)
  items?: OrderItem[];
  payments?: Payment[];
  review?: Review;
}

// Article dans une commande
export interface OrderItem {
  id: string;
  order: string; // UUID
  article_type: string; // UUID
  article_type_details?: ArticleType;
  matiere: string | null; // UUID
  matiere_details?: Matiere;
  service: string; // UUID
  service_details?: Service;
  quantite: number;
  prix_unitaire: number; // FCFA
  total_ligne: number; // FCFA (calculé automatiquement)
  photo: string | null; // URL de l'image
  notes: string;
  created: string;
}

// Pour créer une commande
export interface CreateOrderDto {
  provider: string; // UUID du prestataire
  adresse_collecte: string;
  latitude_collecte?: number;
  longitude_collecte?: number;
  adresse_livraison: string;
  latitude_livraison?: number;
  longitude_livraison?: number;
  creneau_collecte: string; // ISO 8601
  notes_client?: string;
  items: CreateOrderItemDto[];
}

export interface CreateOrderItemDto {
  article_type: string; // UUID
  matiere?: string; // UUID
  service: string; // UUID
  quantite: number;
  prix_unitaire: number;
  photo?: File;
  notes?: string;
}
```

### 6. Paiements

```typescript
// Opérateurs Mobile Money
export type PaymentOperator = 'orange' | 'mtn' | 'moov' | 'wave';

// Statuts de paiement
export type PaymentStatus = 
  | 'pending'      // En attente
  | 'processing'   // En cours
  | 'completed'    // Complété
  | 'failed'       // Échoué
  | 'refunded'     // Remboursé
  | 'cancelled';   // Annulé

// Paiement
export interface Payment {
  id: string;
  order: string; // UUID
  reference: string; // Ex: "PAY-1234567890-ABC"
  operateur: PaymentOperator;
  numero_payeur: string;
  montant: number; // FCFA
  statut: PaymentStatus;
  transaction_id: string;
  metadata: Record<string, any>;
  error_message: string;
  date_initiation: string; // ISO 8601
  date_completion: string | null; // ISO 8601
  is_refund: boolean;
  refund_of: string | null; // UUID
  created: string;
  updated: string;
}

// Pour initier un paiement
export interface InitPaymentDto {
  order: string; // UUID
  operateur: PaymentOperator;
  numero_payeur: string;
  montant: number;
}
```

### 7. Avis et Évaluations

```typescript
// Avis client
export interface Review {
  id: string;
  client: string; // UUID
  client_details?: {
    username: string;
    first_name: string;
    last_name: string;
    photo_profil: string | null;
  };
  provider: string; // UUID
  order: string; // UUID
  note: number; // 1 à 5
  commentaire: string;
  note_qualite: number | null; // 1 à 5
  note_delai: number | null; // 1 à 5
  note_service: number | null; // 1 à 5
  is_approved: boolean;
  is_flagged: boolean;
  reponse_provider: string;
  date_reponse: string | null; // ISO 8601
  created: string;
  updated: string;
}

// Pour créer un avis
export interface CreateReviewDto {
  order: string; // UUID
  note: number; // 1 à 5
  commentaire?: string;
  note_qualite?: number;
  note_delai?: number;
  note_service?: number;
}
```

### 8. Permissions et Configuration

```typescript
// Permission
export interface Permission {
  id: string;
  code: string; // Ex: "view_orders"
  name: string;
  description: string;
  module: 'orders' | 'services' | 'tariffs' | 'stats' | 'staff' | 'settings' | 'customers';
  is_active: boolean;
  created: string;
}

// Rôle personnalisé
export interface Role {
  id: string;
  provider: string; // UUID
  name: string;
  description: string;
  permissions: Permission[];
  is_active: boolean;
  created: string;
  updated: string;
}

// Paramètres du prestataire
export interface ProviderSettings {
  id: string;
  provider: string; // UUID
  business_name: string;
  logo: string | null; // URL
  primary_color: string; // Format hex
  auto_accept_orders: boolean;
  require_payment_before: boolean;
  min_order_amount: number; // FCFA
  delivery_fee: number; // FCFA
  email_notifications: boolean;
  sms_notifications: boolean;
  notification_email: string;
  notification_phone: string;
  opening_hours: Record<string, any>; // JSON
  metadata: Record<string, any>; // JSON
  created: string;
  updated: string;
}
```

### 9. OTP

```typescript
// Objectifs OTP
export type OTPPurpose = 'signup' | 'reset_password' | 'phone_verification' | 'login_2fa';

// Code OTP
export interface OTPCode {
  id: string;
  phone: string;
  purpose: OTPPurpose;
  attempts: number;
  is_verified: boolean;
  created_at: string;
  expires_at: string;
  verified_at: string | null;
}
```

---

## API d'Authentification

### Base URL
```
http://localhost:8000/api/auth/
```

### Endpoints disponibles

#### 1. Inscription (Register)

**Endpoint**: `POST /api/auth/register/`  
**Authentification**: Non requise

**Request Body**:
```typescript
interface RegisterDto {
  username: string;           // Obligatoire, unique
  email: string;             // Obligatoire, unique
  phone: string;             // Obligatoire, unique, format: +225XXXXXXXXXX
  password: string;          // Obligatoire, min 8 caractères
  password_confirm: string;  // Doit correspondre à password
  first_name: string;        // Optionnel
  last_name: string;         // Optionnel
  latitude?: number;         // Optionnel
  longitude?: number;        // Optionnel
  adresse?: string;          // Optionnel
  quartier?: string;         // Optionnel
}
```

**Response Success (201 Created)**:
```typescript
{
  message: "Inscription réussie. Vous pouvez maintenant vous connecter.",
  user: {
    id: "550e8400-e29b-41d4-a716-446655440000",
    username: "johndoe",
    email: "john@example.com",
    phone: "+2250123456789"
  }
}
```

**Response Error (400 Bad Request)**:
```typescript
{
  username?: ["Ce nom d'utilisateur est déjà utilisé."],
  email?: ["Cet email est déjà utilisé."],
  phone?: ["Ce numéro de téléphone est déjà utilisé."],
  password?: ["Les mots de passe ne correspondent pas."]
}
```

---

#### 2. Connexion (Login)

**Endpoint**: `POST /api/auth/login/`  
**Authentification**: Non requise

**Request Body**:
```typescript
interface LoginDto {
  username: string;  // Peut être username, email ou phone
  password: string;
}
```

**Exemple de requêtes valides**:
```typescript
// Avec username
{ username: "johndoe", password: "MonMotDePasse123!" }

// Avec email
{ username: "john@example.com", password: "MonMotDePasse123!" }

// Avec téléphone
{ username: "+2250123456789", password: "MonMotDePasse123!" }
```

**Response Success (200 OK)**:
```typescript
{
  access: "eyJ0eXAiOiJKV1QiLCJhbGc...",  // Token JWT (valide 24h)
  refresh: "eyJ0eXAiOiJKV1QiLCJhbGc...", // Token de rafraîchissement
  user: {
    id: "550e8400-e29b-41d4-a716-446655440000",
    username: "johndoe",
    email: "john@example.com",
    phone: "+2250123456789",
    first_name: "John",
    last_name: "Doe",
    role: "client",
    phone_verified: false,
    phone_verified_at: null,
    provider?: {
      id: "660e8400-e29b-41d4-a716-446655440001",
      nom_commercial: "Pressing Excellence",
      type: "pressing"
    }
  },
  warning?: {
    code: "phone_not_verified",
    message: "Votre numéro de téléphone n'est pas vérifié...",
    action_required: "Vérifiez votre numéro de téléphone",
    phone: "+2250123456789"
  }
}
```

**Response Error (401 Unauthorized)**:
```typescript
{
  detail: "No active account found with the given credentials"
}
```

---

#### 3. Mon Profil (Get Profile)

**Endpoint**: `GET /api/auth/profile/`  
**Authentification**: Requise (Bearer Token)

**Headers**:
```typescript
{
  "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response Success (200 OK)**:
```typescript
{
  id: "550e8400-e29b-41d4-a716-446655440000",
  username: "johndoe",
  email: "john@example.com",
  phone: "+2250123456789",
  phone_verified: true,
  phone_verified_at: "2025-01-15T10:30:00Z",
  first_name: "John",
  last_name: "Doe",
  photo_profil: "https://api.presso.ci/media/users/profils/2025/01/photo.jpg",
  role: "client",
  role_display: "Client",
  custom_role: null,
  latitude: 5.360000,
  longitude: -3.987000,
  adresse: "Cocody Riviera 3",
  quartier: "Riviera 3",
  date_inscription: "2025-01-10T08:00:00Z",
  is_active: true,
  provider: null,
  permissions: []
}
```

---

#### 4. Modifier mon Profil (Update Profile)

**Endpoint**: `PATCH /api/auth/profile/`  
**Authentification**: Requise (Bearer Token)

**Request Body** (tous les champs sont optionnels):
```typescript
interface UpdateProfileDto {
  first_name?: string;
  last_name?: string;
  photo_profil?: File;
  latitude?: number;
  longitude?: number;
  adresse?: string;
  quartier?: string;
}
```

**Response Success (200 OK)**:
```typescript
{
  message: "Profil mis à jour avec succès",
  user: {
    // Objet User complet
  }
}
```

---

#### 5. Changer le Mot de Passe

**Endpoint**: `POST /api/auth/change-password/`  
**Authentification**: Requise (Bearer Token)

**Request Body**:
```typescript
interface ChangePasswordDto {
  old_password: string;
  new_password: string;
  new_password_confirm: string;
}
```

**Response Success (200 OK)**:
```typescript
{
  message: "Mot de passe changé avec succès"
}
```

**Response Error (400 Bad Request)**:
```typescript
{
  old_password?: ["Ancien mot de passe incorrect."],
  new_password?: ["Les nouveaux mots de passe ne correspondent pas."]
}
```

---

#### 6. Demander un Code OTP

**Endpoint**: `POST /api/auth/otp/request/`  
**Authentification**: Non requise

**Request Body**:
```typescript
interface OTPRequestDto {
  phone: string;  // Format: +225XXXXXXXXXX
  purpose: 'signup' | 'reset_password' | 'phone_verification' | 'login_2fa';
}
```

**Exemples**:
```typescript
// Pour inscription
{ phone: "+2250123456789", purpose: "signup" }

// Pour vérification téléphone
{ phone: "+2250123456789", purpose: "phone_verification" }

// Pour reset mot de passe
{ phone: "+2250123456789", purpose: "reset_password" }
```

**Response Success (200 OK)**:
```typescript
{
  phone: "+2250123456789",
  expires_at: "2025-10-22T12:15:00Z",  // Expire dans 10 minutes
  message: "Code OTP envoyé au +2250123456789"
}
```

**Response Error (400 Bad Request)**:
```typescript
{
  phone?: ["Ce numéro est déjà associé à un compte."],  // Si purpose=signup
  phone?: ["Aucun compte associé à ce numéro."],        // Si purpose=reset_password
  non_field_errors?: ["Veuillez attendre X secondes avant de redemander un code."]
}
```

---

#### 7. Vérifier un Code OTP

**Endpoint**: `POST /api/auth/otp/verify/`  
**Authentification**: Non requise

**Request Body**:
```typescript
interface OTPVerifyDto {
  phone: string;   // Format: +225XXXXXXXXXX
  code: string;    // Code à 6 chiffres
  purpose: 'signup' | 'reset_password' | 'phone_verification' | 'login_2fa';
}
```

**Exemple**:
```typescript
{
  phone: "+2250123456789",
  code: "123456",
  purpose: "phone_verification"
}
```

**Response Success (200 OK)**:
```typescript
{
  phone: "+2250123456789",
  purpose: "phone_verification",
  verified: true,
  otp_id: "770e8400-e29b-41d4-a716-446655440000",
  message: "Numéro de téléphone vérifié avec succès"
}
```

**Response Error (400 Bad Request)**:
```typescript
{
  code?: ["Code incorrect."],
  code?: ["Code expiré."],
  code?: ["Trop de tentatives. Demandez un nouveau code."]
}
```

---

#### 8. Demander une Réinitialisation de Mot de Passe

**Endpoint**: `POST /api/auth/password/reset/`  
**Authentification**: Non requise

**Request Body**:
```typescript
interface PasswordResetDto {
  phone: string;  // Format: +225XXXXXXXXXX
}
```

**Response Success (200 OK)**:
```typescript
{
  phone: "+2250123456789",
  message: "Code de réinitialisation envoyé par SMS"
}
```

---

#### 9. Confirmer la Réinitialisation de Mot de Passe

**Endpoint**: `POST /api/auth/password/reset/confirm/`  
**Authentification**: Non requise

**Request Body**:
```typescript
interface PasswordResetConfirmDto {
  phone: string;
  code: string;                // Code OTP reçu par SMS
  new_password: string;
  new_password_confirm: string;
}
```

**Response Success (200 OK)**:
```typescript
{
  message: "Mot de passe réinitialisé avec succès",
  user_id: "550e8400-e29b-41d4-a716-446655440000"
}
```

---

#### 10. Rafraîchir le Token JWT

**Endpoint**: `POST /api/auth/token/refresh/`  
**Authentification**: Non requise (mais besoin du refresh token)

**Request Body**:
```typescript
{
  refresh: "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response Success (200 OK)**:
```typescript
{
  access: "eyJ0eXAiOiJKV1QiLCJhbGc..."  // Nouveau token d'accès
}
```

---

## Exemples d'utilisation Vue.js

### Configuration Axios avec intercepteurs

```typescript
// src/plugins/axios.ts
import axios, { AxiosInstance } from 'axios';
import { useAuthStore } from '@/stores/auth';

const apiClient: AxiosInstance = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token à chaque requête
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercepteur pour gérer l'expiration du token
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const authStore = useAuthStore();
      try {
        await authStore.refreshToken();
        return apiClient(originalRequest);
      } catch (refreshError) {
        authStore.logout();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
```

### Service d'authentification

```typescript
// src/services/auth.service.ts
import apiClient from '@/plugins/axios';
import type { 
  RegisterDto, 
  LoginDto, 
  User, 
  OTPRequestDto, 
  OTPVerifyDto 
} from '@/types';

export const authService = {
  // Inscription
  async register(data: RegisterDto) {
    const response = await apiClient.post('/auth/register/', data);
    return response.data;
  },

  // Connexion
  async login(data: LoginDto) {
    const response = await apiClient.post('/auth/login/', data);
    return response.data;
  },

  // Profil
  async getProfile(): Promise<User> {
    const response = await apiClient.get('/auth/profile/');
    return response.data;
  },

  // Modifier profil
  async updateProfile(data: Partial<User>) {
    const response = await apiClient.patch('/auth/profile/', data);
    return response.data;
  },

  // OTP
  async requestOTP(data: OTPRequestDto) {
    const response = await apiClient.post('/auth/otp/request/', data);
    return response.data;
  },

  async verifyOTP(data: OTPVerifyDto) {
    const response = await apiClient.post('/auth/otp/verify/', data);
    return response.data;
  },

  // Mot de passe
  async changePassword(oldPassword: string, newPassword: string) {
    const response = await apiClient.post('/auth/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
      new_password_confirm: newPassword,
    });
    return response.data;
  },

  async resetPassword(phone: string) {
    const response = await apiClient.post('/auth/password/reset/', { phone });
    return response.data;
  },

  async confirmResetPassword(phone: string, code: string, newPassword: string) {
    const response = await apiClient.post('/auth/password/reset/confirm/', {
      phone,
      code,
      new_password: newPassword,
      new_password_confirm: newPassword,
    });
    return response.data;
  },

  // Rafraîchir token
  async refreshToken(refreshToken: string) {
    const response = await apiClient.post('/auth/token/refresh/', {
      refresh: refreshToken,
    });
    return response.data;
  },
};
```

### Store Pinia pour l'authentification

```typescript
// src/stores/auth.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { authService } from '@/services/auth.service';
import type { User, LoginDto, RegisterDto } from '@/types';

export const useAuthStore = defineStore('auth', () => {
  // État
  const user = ref<User | null>(null);
  const accessToken = ref<string | null>(localStorage.getItem('access_token'));
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'));

  // Getters
  const isAuthenticated = computed(() => !!accessToken.value);
  const isPhoneVerified = computed(() => user.value?.phone_verified ?? false);
  const userRole = computed(() => user.value?.role ?? null);

  // Actions
  async function login(credentials: LoginDto) {
    try {
      const response = await authService.login(credentials);
      
      accessToken.value = response.access;
      refreshToken.value = response.refresh;
      user.value = response.user;

      // Sauvegarder dans le localStorage
      localStorage.setItem('access_token', response.access);
      localStorage.setItem('refresh_token', response.refresh);

      return response;
    } catch (error) {
      console.error('Erreur de connexion:', error);
      throw error;
    }
  }

  async function register(data: RegisterDto) {
    try {
      const response = await authService.register(data);
      return response;
    } catch (error) {
      console.error('Erreur d\'inscription:', error);
      throw error;
    }
  }

  async function fetchProfile() {
    try {
      user.value = await authService.getProfile();
    } catch (error) {
      console.error('Erreur de récupération du profil:', error);
      throw error;
    }
  }

  async function updateProfile(data: Partial<User>) {
    try {
      const response = await authService.updateProfile(data);
      user.value = response.user;
      return response;
    } catch (error) {
      console.error('Erreur de mise à jour du profil:', error);
      throw error;
    }
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await authService.refreshToken(refreshToken.value);
      accessToken.value = response.access;
      localStorage.setItem('access_token', response.access);
    } catch (error) {
      console.error('Erreur de rafraîchissement du token:', error);
      logout();
      throw error;
    }
  }

  function logout() {
    user.value = null;
    accessToken.value = null;
    refreshToken.value = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  return {
    // État
    user,
    accessToken,
    refreshToken,
    
    // Getters
    isAuthenticated,
    isPhoneVerified,
    userRole,
    
    // Actions
    login,
    register,
    fetchProfile,
    updateProfile,
    refreshAccessToken,
    logout,
  };
});
```

### Composant de connexion

```vue
<!-- src/views/LoginView.vue -->
<template>
  <div class="min-h-screen flex items-center justify-center bg-dark">
    <div class="max-w-md w-full space-y-8 p-8 bg-dark/50 backdrop-blur-lg rounded-2xl border border-white/10">
      <div>
        <h2 class="text-3xl font-bold text-white text-center">
          Connexion
        </h2>
      </div>

      <form @submit.prevent="handleLogin" class="mt-8 space-y-6">
        <!-- Alerte d'erreur -->
        <div v-if="error" class="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded-lg">
          {{ error }}
        </div>

        <!-- Alerte de vérification téléphone -->
        <div v-if="phoneWarning" class="bg-orange-500/10 border border-orange-500 text-orange-500 px-4 py-3 rounded-lg">
          <p class="font-semibold">{{ phoneWarning.message }}</p>
          <p class="text-sm mt-1">{{ phoneWarning.action_required }}</p>
        </div>

        <!-- Champ username/email/phone -->
        <div>
          <label for="username" class="block text-sm font-medium text-white/80">
            Email, téléphone ou nom d'utilisateur
          </label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            required
            class="mt-1 block w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg 
                   text-white placeholder-white/40 focus:outline-none focus:ring-2 
                   focus:ring-orange-500 focus:border-transparent"
            placeholder="johndoe ou john@example.com"
          />
        </div>

        <!-- Champ mot de passe -->
        <div>
          <label for="password" class="block text-sm font-medium text-white/80">
            Mot de passe
          </label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            class="mt-1 block w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg 
                   text-white placeholder-white/40 focus:outline-none focus:ring-2 
                   focus:ring-orange-500 focus:border-transparent"
            placeholder="••••••••"
          />
        </div>

        <!-- Bouton de connexion -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg 
                 text-white font-semibold bg-orange-500 hover:bg-orange-600 
                 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 
                 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <span v-if="!loading">Se connecter</span>
          <span v-else>Connexion en cours...</span>
        </button>

        <!-- Liens -->
        <div class="flex items-center justify-between text-sm">
          <router-link to="/forgot-password" class="text-orange-500 hover:text-orange-400">
            Mot de passe oublié ?
          </router-link>
          <router-link to="/register" class="text-white/80 hover:text-white">
            Créer un compte
          </router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const form = ref({
  username: '',
  password: '',
});

const loading = ref(false);
const error = ref('');
const phoneWarning = ref<any>(null);

async function handleLogin() {
  loading.value = true;
  error.value = '';
  phoneWarning.value = null;

  try {
    const response = await authStore.login(form.value);

    // Vérifier s'il y a un avertissement de téléphone non vérifié
    if (response.warning) {
      phoneWarning.value = response.warning;
    }

    // Rediriger vers le dashboard
    router.push('/dashboard');
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Identifiants incorrects';
  } finally {
    loading.value = false;
  }
}
</script>
```

### Guard de navigation pour routes protégées

```typescript
// src/router/guards.ts
import { useAuthStore } from '@/stores/auth';
import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router';

export async function authGuard(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) {
  const authStore = useAuthStore();

  // Si la route nécessite l'authentification
  if (to.meta.requiresAuth) {
    if (!authStore.isAuthenticated) {
      // Rediriger vers la page de connexion
      return next({
        name: 'login',
        query: { redirect: to.fullPath },
      });
    }

    // Récupérer le profil si pas encore chargé
    if (!authStore.user) {
      try {
        await authStore.fetchProfile();
      } catch (error) {
        authStore.logout();
        return next({ name: 'login' });
      }
    }

    // Vérifier si le téléphone doit être vérifié
    if (to.meta.requiresPhoneVerified && !authStore.isPhoneVerified) {
      return next({ name: 'verify-phone' });
    }

    // Vérifier les rôles
    if (to.meta.roles && !to.meta.roles.includes(authStore.userRole)) {
      return next({ name: 'unauthorized' });
    }
  }

  next();
}
```

---

## 📝 Notes importantes

### Gestion des erreurs
- Code **400**: Erreur de validation (champs manquants ou invalides)
- Code **401**: Non authentifié ou token invalide
- Code **403**: Pas les permissions nécessaires
- Code **404**: Ressource non trouvée
- Code **500**: Erreur serveur

### Formats de dates
- Toutes les dates sont en **ISO 8601** (ex: `2025-10-22T12:00:00Z`)
- Utiliser `new Date()` en JavaScript pour les parser
- Pour l'affichage, utiliser des bibliothèques comme `date-fns` ou `dayjs`

### Numéros de téléphone
- Format accepté: `+225XXXXXXXXXX` ou `XXXXXXXXXX`
- L'API formatte automatiquement au format international

### Tokens JWT
- **Access token**: Expire après 24 heures
- **Refresh token**: Expire après 7 jours
- Stocker dans `localStorage` ou `sessionStorage`
- Utiliser les intercepteurs Axios pour gérer le rafraîchissement automatique

### Fichiers (uploads)
- Utiliser `FormData` pour envoyer des images
- Types acceptés: JPEG, PNG, GIF, WebP
- Taille maximale recommandée: 5 MB

