/**
 * EXEMPLE D'UTILISATION DES MOCK DATA
 * Service mock pour simuler les appels API pendant le développement
 */

import mockData from './MOCK_DATA';
import type { User, LoginDto, RegisterDto, Order, Provider } from './types';

/**
 * Service d'authentification simulé
 */
export class MockAuthService {
  private static storageKey = 'mock_auth_token';
  private static userKey = 'mock_user';

  /**
   * Simule une connexion
   */
  static async login(credentials: LoginDto): Promise<any> {
    // Simuler un délai réseau
    await this.delay(800);

    try {
      const result = mockData.utils.simulateLogin(
        credentials.username,
        credentials.password
      );

      // Stocker le token et l'utilisateur en localStorage
      localStorage.setItem(this.storageKey, result.access);
      localStorage.setItem(this.userKey, JSON.stringify(result.user));

      return result;
    } catch (error) {
      throw new Error('Identifiants incorrects');
    }
  }

  /**
   * Simule une inscription
   */
  static async register(data: RegisterDto): Promise<any> {
    await this.delay(1000);

    // Vérifier si l'email/phone/username existe déjà
    const existingUser = mockData.users.find(
      (u) =>
        u.email === data.email ||
        u.phone === data.phone ||
        u.username === data.username
    );

    if (existingUser) {
      if (existingUser.email === data.email) {
        throw new Error('Cet email est déjà utilisé.');
      }
      if (existingUser.phone === data.phone) {
        throw new Error('Ce numéro de téléphone est déjà utilisé.');
      }
      if (existingUser.username === data.username) {
        throw new Error('Ce nom d\'utilisateur est déjà utilisé.');
      }
    }

    // Créer un nouvel utilisateur (simulation)
    const newUser: User = {
      id: this.generateUUID(),
      username: data.username,
      email: data.email,
      phone: data.phone,
      phone_verified: false,
      phone_verified_at: null,
      first_name: data.first_name || '',
      last_name: data.last_name || '',
      photo_profil: null,
      role: 'client',
      role_display: 'Client',
      custom_role: null,
      latitude: data.latitude || null,
      longitude: data.longitude || null,
      adresse: data.adresse || '',
      quartier: data.quartier || '',
      date_inscription: new Date().toISOString(),
      is_active: true,
      provider: null,
      permissions: [],
    };

    // Ajouter à la liste mock (temporaire)
    mockData.users.push(newUser);

    return {
      message: 'Inscription réussie. Vous pouvez maintenant vous connecter.',
      user: {
        id: newUser.id,
        username: newUser.username,
        email: newUser.email,
        phone: newUser.phone,
      },
    };
  }

  /**
   * Récupère le profil de l'utilisateur connecté
   */
  static async getProfile(): Promise<User> {
    await this.delay(300);

    const userStr = localStorage.getItem(this.userKey);
    if (!userStr) {
      throw new Error('Non authentifié');
    }

    return JSON.parse(userStr);
  }

  /**
   * Demande un code OTP
   */
  static async requestOTP(phone: string, purpose: string): Promise<any> {
    await this.delay(500);

    return mockData.utils.simulateOTPRequest(phone, purpose);
  }

  /**
   * Vérifie un code OTP
   */
  static async verifyOTP(
    phone: string,
    code: string,
    purpose: string
  ): Promise<any> {
    await this.delay(600);

    return mockData.utils.simulateOTPVerify(phone, code, purpose);
  }

  /**
   * Déconnexion
   */
  static logout(): void {
    localStorage.removeItem(this.storageKey);
    localStorage.removeItem(this.userKey);
  }

  /**
   * Vérifie si l'utilisateur est connecté
   */
  static isAuthenticated(): boolean {
    return !!localStorage.getItem(this.storageKey);
  }

  // Utilitaires
  private static delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private static generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }
}

/**
 * Service de prestataires simulé
 */
export class MockProviderService {
  /**
   * Récupère tous les prestataires
   */
  static async getAll(): Promise<Provider[]> {
    await this.delay(400);
    return mockData.providers.filter((p) => p.is_active);
  }

  /**
   * Récupère un prestataire par ID
   */
  static async getById(id: string): Promise<Provider> {
    await this.delay(300);

    const provider = mockData.providers.find((p) => p.id === id);
    if (!provider) {
      throw new Error('Prestataire non trouvé');
    }

    return provider;
  }

  /**
   * Cherche les prestataires à proximité
   */
  static async findNearby(
    latitude: number,
    longitude: number,
    maxKm: number = 10,
    type?: 'pressing' | 'fanico'
  ): Promise<Provider[]> {
    await this.delay(600);

    let providers = mockData.utils.findNearbyProviders(latitude, longitude, maxKm);

    if (type) {
      providers = providers.filter((p) => p.type === type);
    }

    return providers;
  }

  /**
   * Récupère les services d'un prestataire
   */
  static async getServices(providerId: string) {
    await this.delay(300);

    return mockData.services.filter(
      (s) => s.provider === providerId && s.is_active
    );
  }

  /**
   * Récupère les tarifs d'un prestataire
   */
  static async getTariffs(providerId: string) {
    await this.delay(300);

    return mockData.tariffs.filter((t) => t.provider === providerId);
  }

  /**
   * Récupère les avis d'un prestataire
   */
  static async getReviews(providerId: string) {
    await this.delay(400);

    return mockData.utils.getReviewsByProvider(providerId);
  }

  /**
   * Récupère la note moyenne d'un prestataire
   */
  static async getAverageRating(providerId: string): Promise<number> {
    await this.delay(200);

    return Number(mockData.utils.getProviderAverageRating(providerId));
  }

  private static delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

/**
 * Service de commandes simulé
 */
export class MockOrderService {
  /**
   * Récupère toutes les commandes de l'utilisateur
   */
  static async getMyOrders(): Promise<Order[]> {
    await this.delay(500);

    const userStr = localStorage.getItem('mock_user');
    if (!userStr) {
      throw new Error('Non authentifié');
    }

    const user = JSON.parse(userStr);
    return mockData.utils.getOrdersByUser(user.id);
  }

  /**
   * Récupère une commande par ID
   */
  static async getById(orderId: string): Promise<Order> {
    await this.delay(400);

    const order = mockData.orders.find((o) => o.id === orderId);
    if (!order) {
      throw new Error('Commande non trouvée');
    }

    return order;
  }

  /**
   * Récupère les articles d'une commande
   */
  static async getOrderItems(orderId: string) {
    await this.delay(300);

    return mockData.utils.getOrderItems(orderId);
  }

  /**
   * Crée une nouvelle commande
   */
  static async create(orderData: any): Promise<Order> {
    await this.delay(800);

    const userStr = localStorage.getItem('mock_user');
    if (!userStr) {
      throw new Error('Non authentifié');
    }

    const user = JSON.parse(userStr);

    // Créer une nouvelle commande (simulation)
    const newOrder: Order = {
      id: this.generateUUID(),
      numero: `ORD-2025-${String(mockData.orders.length + 1).padStart(4, '0')}`,
      client: user.id,
      client_details: {
        id: user.id,
        username: user.username,
        first_name: user.first_name,
        last_name: user.last_name,
        phone: user.phone,
      },
      provider: orderData.provider,
      statut: 'pending',
      adresse_collecte: orderData.adresse_collecte,
      latitude_collecte: orderData.latitude_collecte,
      longitude_collecte: orderData.longitude_collecte,
      adresse_livraison: orderData.adresse_livraison,
      latitude_livraison: orderData.latitude_livraison,
      longitude_livraison: orderData.longitude_livraison,
      creneau_collecte: orderData.creneau_collecte,
      creneau_livraison: null,
      date_collecte: null,
      date_livraison: null,
      total_estime: orderData.total_estime || 0,
      total_final: null,
      frais_livraison: orderData.frais_livraison || 500,
      notes_client: orderData.notes_client || '',
      notes_provider: '',
      signature_client: null,
      created: new Date().toISOString(),
      updated: new Date().toISOString(),
    };

    mockData.orders.push(newOrder);

    return newOrder;
  }

  /**
   * Annule une commande
   */
  static async cancel(orderId: string): Promise<Order> {
    await this.delay(500);

    const order = mockData.orders.find((o) => o.id === orderId);
    if (!order) {
      throw new Error('Commande non trouvée');
    }

    order.statut = 'cancelled';
    order.updated = new Date().toISOString();

    return order;
  }

  private static delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private static generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }
}

/**
 * Service de paiements simulé
 */
export class MockPaymentService {
  /**
   * Récupère les paiements d'une commande
   */
  static async getByOrder(orderId: string) {
    await this.delay(300);

    return mockData.utils.getPaymentsByOrder(orderId);
  }

  /**
   * Initie un paiement
   */
  static async initiate(paymentData: any) {
    await this.delay(1000);

    // Simuler un succès ou échec aléatoire (80% succès)
    const success = Math.random() > 0.2;

    const payment = {
      id: this.generateUUID(),
      order: paymentData.order,
      reference: `PAY-${Date.now()}-${this.generateRandomString(8)}`,
      operateur: paymentData.operateur,
      numero_payeur: paymentData.numero_payeur,
      montant: paymentData.montant,
      statut: success ? 'completed' : 'failed',
      transaction_id: success ? `TXN-${Date.now()}` : '',
      metadata: {},
      error_message: success ? '' : 'Simulation d\'échec de paiement',
      date_initiation: new Date().toISOString(),
      date_completion: success ? new Date().toISOString() : null,
      is_refund: false,
      refund_of: null,
      created: new Date().toISOString(),
      updated: new Date().toISOString(),
    };

    mockData.payments.push(payment);

    return payment;
  }

  /**
   * Vérifie le statut d'un paiement
   */
  static async checkStatus(paymentId: string) {
    await this.delay(500);

    const payment = mockData.payments.find((p) => p.id === paymentId);
    if (!payment) {
      throw new Error('Paiement non trouvé');
    }

    return payment;
  }

  private static delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private static generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  private static generateRandomString(length: number): string {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }
}

/**
 * Exemple d'utilisation dans un composable Vue.js
 */
export function useMockAPI() {
  return {
    auth: MockAuthService,
    providers: MockProviderService,
    orders: MockOrderService,
    payments: MockPaymentService,
  };
}

// Export par défaut
export default {
  auth: MockAuthService,
  providers: MockProviderService,
  orders: MockOrderService,
  payments: MockPaymentService,
};

