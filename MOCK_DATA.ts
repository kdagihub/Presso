/**
 * MOCK DATA - Presso Application
 * Données de test pour le développement frontend
 * Basées sur les modèles Django du backend
 */

import type {
  User,
  Provider,
  Service,
  ArticleType,
  Matiere,
  ProviderService,
  Tariff,
  Order,
  OrderItem,
  Payment,
  Review,
  Permission,
  Role,
  ProviderSettings,
  OTPCode,
} from './types';

// ============================================================================
// UTILISATEURS (USERS)
// ============================================================================

export const mockUsers: User[] = [
  {
    id: '550e8400-e29b-41d4-a716-446655440001',
    username: 'john_doe',
    email: 'john.doe@gmail.com',
    phone: '+2250123456789',
    phone_verified: true,
    phone_verified_at: '2025-01-10T10:30:00Z',
    first_name: 'John',
    last_name: 'Doe',
    photo_profil: null,
    role: 'client',
    role_display: 'Client',
    custom_role: null,
    latitude: 5.360000,
    longitude: -3.987000,
    adresse: 'Cocody Riviera 3, Résidence les Lauriers',
    quartier: 'Riviera 3',
    date_inscription: '2025-01-10T08:00:00Z',
    is_active: true,
    provider: null,
    permissions: [],
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440002',
    username: 'marie_kouame',
    email: 'marie.kouame@yahoo.fr',
    phone: '+2250709876543',
    phone_verified: true,
    phone_verified_at: '2025-01-15T14:20:00Z',
    first_name: 'Marie',
    last_name: 'Kouamé',
    photo_profil: 'https://i.pravatar.cc/150?img=1',
    role: 'client',
    role_display: 'Client',
    custom_role: null,
    latitude: 5.342000,
    longitude: -4.024000,
    adresse: 'Marcory Zone 4, Cité SICOGI',
    quartier: 'Marcory Zone 4',
    date_inscription: '2025-01-15T09:00:00Z',
    is_active: true,
    provider: null,
    permissions: [],
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440003',
    username: 'pressing_excellence',
    email: 'contact@pressingexcellence.ci',
    phone: '+2250778123456',
    phone_verified: true,
    phone_verified_at: '2025-01-05T12:00:00Z',
    first_name: 'Kouassi',
    last_name: 'Yao',
    photo_profil: 'https://i.pravatar.cc/150?img=12',
    role: 'pressing',
    role_display: 'Prestataire - Pressing',
    custom_role: null,
    latitude: 5.358000,
    longitude: -3.992000,
    adresse: 'Cocody Angré 8ème Tranche',
    quartier: 'Angré',
    date_inscription: '2025-01-05T10:00:00Z',
    is_active: true,
    provider: {
      id: '660e8400-e29b-41d4-a716-446655440001',
      nom_commercial: 'Pressing Excellence',
      type: 'pressing',
      adresse: 'Cocody Angré 8ème Tranche, près du carrefour Stella',
      quartier: 'Angré',
    },
    permissions: ['view_orders', 'manage_orders', 'view_stats'],
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440004',
    username: 'fanico_rapide',
    email: 'aya.traore@fanico.ci',
    phone: '+2250501234567',
    phone_verified: true,
    phone_verified_at: '2025-01-08T16:45:00Z',
    first_name: 'Aya',
    last_name: 'Traoré',
    photo_profil: 'https://i.pravatar.cc/150?img=5',
    role: 'fanico',
    role_display: 'Prestataire - Fanico',
    custom_role: null,
    latitude: 5.351000,
    longitude: -4.001000,
    adresse: 'Plateau, Rue du Commerce',
    quartier: 'Plateau',
    date_inscription: '2025-01-08T11:00:00Z',
    is_active: true,
    provider: {
      id: '660e8400-e29b-41d4-a716-446655440002',
      nom_commercial: 'Fanico Rapide Express',
      type: 'fanico',
      adresse: 'Plateau, Rue du Commerce',
      quartier: 'Plateau',
    },
    permissions: ['view_orders', 'manage_orders'],
  },
  {
    id: '550e8400-e29b-41d4-a716-446655440005',
    username: 'admin_presso',
    email: 'admin@presso.ci',
    phone: '+2250777888999',
    phone_verified: true,
    phone_verified_at: '2025-01-01T00:00:00Z',
    first_name: 'Admin',
    last_name: 'Presso',
    photo_profil: null,
    role: 'admin',
    role_display: 'Administrateur',
    custom_role: null,
    latitude: null,
    longitude: null,
    adresse: '',
    quartier: '',
    date_inscription: '2025-01-01T00:00:00Z',
    is_active: true,
    provider: null,
    permissions: ['all'],
  },
];

// ============================================================================
// PRESTATAIRES (PROVIDERS)
// ============================================================================

export const mockProviders: Provider[] = [
  {
    id: '660e8400-e29b-41d4-a716-446655440001',
    user: '550e8400-e29b-41d4-a716-446655440003',
    type: 'pressing',
    nom_commercial: 'Pressing Excellence',
    photo_local: 'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=800',
    zone_couverture: 'Cocody, Angré, Riviera, Deux-Plateaux',
    rayon_km: 8.00,
    latitude: 5.358000,
    longitude: -3.992000,
    adresse: 'Cocody Angré 8ème Tranche, près du carrefour Stella',
    quartier: 'Angré',
    statut_kyc: 'verified',
    document_identite: 'https://example.com/docs/pressing-excellence-cni.pdf',
    is_active: true,
    created: '2025-01-05T10:00:00Z',
    updated: '2025-01-20T15:30:00Z',
    distance: 2.5,
  },
  {
    id: '660e8400-e29b-41d4-a716-446655440002',
    user: '550e8400-e29b-41d4-a716-446655440004',
    type: 'fanico',
    nom_commercial: 'Fanico Rapide Express',
    photo_local: null,
    zone_couverture: 'Plateau, Marcory, Treichville, Koumassi',
    rayon_km: 10.00,
    latitude: 5.351000,
    longitude: -4.001000,
    adresse: 'Plateau, Rue du Commerce',
    quartier: 'Plateau',
    statut_kyc: 'verified',
    document_identite: 'https://example.com/docs/fanico-rapide-cni.pdf',
    is_active: true,
    created: '2025-01-08T11:00:00Z',
    updated: '2025-01-22T09:15:00Z',
    distance: 5.2,
  },
  {
    id: '660e8400-e29b-41d4-a716-446655440003',
    user: '550e8400-e29b-41d4-a716-446655440006',
    type: 'pressing',
    nom_commercial: 'Pressing Royal',
    photo_local: 'https://images.unsplash.com/photo-1604335399105-a0c585fd81a1?w=800',
    zone_couverture: 'Yopougon, Abobo, Adjamé',
    rayon_km: 12.00,
    latitude: 5.345000,
    longitude: -4.085000,
    adresse: 'Yopougon Siporex, face à la station Shell',
    quartier: 'Yopougon',
    statut_kyc: 'pending',
    document_identite: null,
    is_active: true,
    created: '2025-01-18T14:00:00Z',
    updated: '2025-01-18T14:00:00Z',
    distance: 8.7,
  },
  {
    id: '660e8400-e29b-41d4-a716-446655440004',
    user: '550e8400-e29b-41d4-a716-446655440007',
    type: 'pressing',
    nom_commercial: 'Clean & Fresh',
    photo_local: 'https://images.unsplash.com/photo-1517677208171-0bc6725a3e60?w=800',
    zone_couverture: 'Marcory, Port-Bouët, Vridi',
    rayon_km: 6.50,
    latitude: 5.285000,
    longitude: -3.976000,
    adresse: 'Marcory Résidentiel, Boulevard VGE',
    quartier: 'Marcory',
    statut_kyc: 'verified',
    document_identite: 'https://example.com/docs/clean-fresh-cni.pdf',
    is_active: true,
    created: '2025-01-12T08:30:00Z',
    updated: '2025-01-25T11:20:00Z',
    distance: 3.1,
  },
];

// ============================================================================
// SERVICES
// ============================================================================

export const mockServices: Service[] = [
  {
    id: '770e8400-e29b-41d4-a716-446655440001',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    label: 'Lavage Simple',
    description: 'Lavage standard de vos vêtements',
    mode_tarif: 'kg',
    duree_estimee: 1440, // 24 heures
    icone: 'washing-machine',
    is_active: true,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  {
    id: '770e8400-e29b-41d4-a716-446655440002',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    label: 'Lavage + Repassage',
    description: 'Lavage complet avec repassage professionnel',
    mode_tarif: 'piece',
    duree_estimee: 2880, // 48 heures
    icone: 'iron',
    is_active: true,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  {
    id: '770e8400-e29b-41d4-a716-446655440003',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    label: 'Nettoyage à sec',
    description: 'Nettoyage à sec pour tissus délicats',
    mode_tarif: 'piece',
    duree_estimee: 4320, // 72 heures
    icone: 'sparkles',
    is_active: true,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  {
    id: '770e8400-e29b-41d4-a716-446655440004',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    label: 'Repassage uniquement',
    description: 'Service de repassage seul',
    mode_tarif: 'piece',
    duree_estimee: 720, // 12 heures
    icone: 'iron',
    is_active: true,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  {
    id: '770e8400-e29b-41d4-a716-446655440005',
    provider: '660e8400-e29b-41d4-a716-446655440002',
    template: null,
    label: 'Repassage Express',
    description: 'Repassage rapide en moins de 3 heures',
    mode_tarif: 'piece',
    duree_estimee: 180, // 3 heures
    icone: 'zap',
    is_active: true,
    created: '2025-01-08T11:30:00Z',
    updated: '2025-01-08T11:30:00Z',
  },
  {
    id: '770e8400-e29b-41d4-a716-446655440006',
    provider: '660e8400-e29b-41d4-a716-446655440002',
    template: null,
    label: 'Forfait Bureau',
    description: 'Forfait mensuel pour professionnels (10 chemises + 5 pantalons)',
    mode_tarif: 'forfait',
    duree_estimee: 1440,
    icone: 'briefcase',
    is_active: true,
    created: '2025-01-08T11:30:00Z',
    updated: '2025-01-08T11:30:00Z',
  },
];

// ============================================================================
// TYPES D'ARTICLES
// ============================================================================

export const mockArticleTypes: ArticleType[] = [
  {
    id: '880e8400-e29b-41d4-a716-446655440001',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    nom: 'Chemise',
    description: 'Chemise homme ou femme',
    created: '2025-01-05T10:30:00Z',
  },
  {
    id: '880e8400-e29b-41d4-a716-446655440002',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    nom: 'Pantalon',
    description: 'Pantalon classique ou jean',
    created: '2025-01-05T10:30:00Z',
  },
  {
    id: '880e8400-e29b-41d4-a716-446655440003',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    nom: 'Robe',
    description: 'Robe de soirée ou casual',
    created: '2025-01-05T10:30:00Z',
  },
  {
    id: '880e8400-e29b-41d4-a716-446655440004',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    nom: 'Costume',
    description: 'Costume complet (veste + pantalon)',
    created: '2025-01-05T10:30:00Z',
  },
  {
    id: '880e8400-e29b-41d4-a716-446655440005',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    nom: 'Pagne',
    description: 'Pagne traditionnel',
    created: '2025-01-05T10:30:00Z',
  },
  {
    id: '880e8400-e29b-41d4-a716-446655440006',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    nom: 'Drap/Couverture',
    description: 'Linge de lit',
    created: '2025-01-05T10:30:00Z',
  },
];

// ============================================================================
// MATIÈRES
// ============================================================================

export const mockMatieres: Matiere[] = [
  {
    id: '990e8400-e29b-41d4-a716-446655440001',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    nom: 'Coton',
    description: 'Tissu en coton naturel',
    created: '2025-01-05T10:30:00Z',
  },
  {
    id: '990e8400-e29b-41d4-a716-446655440002',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    nom: 'Soie',
    description: 'Tissu en soie délicate',
    created: '2025-01-05T10:30:00Z',
  },
  {
    id: '990e8400-e29b-41d4-a716-446655440003',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    nom: 'Laine',
    description: 'Tissu en laine',
    created: '2025-01-05T10:30:00Z',
  },
  {
    id: '990e8400-e29b-41d4-a716-446655440004',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    nom: 'Synthétique',
    description: 'Tissu synthétique (polyester, etc.)',
    created: '2025-01-05T10:30:00Z',
  },
  {
    id: '990e8400-e29b-41d4-a716-446655440005',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    template: null,
    nom: 'Wax',
    description: 'Tissu wax africain',
    created: '2025-01-05T10:30:00Z',
  },
];

// ============================================================================
// SERVICES PROPOSÉS PAR PRESTATAIRES (avec prix)
// ============================================================================

export const mockProviderServices: ProviderService[] = [
  {
    id: 'aa0e8400-e29b-41d4-a716-446655440001',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    service: '770e8400-e29b-41d4-a716-446655440001',
    service_details: {
      id: '770e8400-e29b-41d4-a716-446655440001',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      label: 'Lavage Simple',
      description: 'Lavage standard de vos vêtements',
      mode_tarif: 'kg',
      duree_estimee: 1440,
      icone: 'washing-machine',
      is_active: true,
      created: '2025-01-05T10:30:00Z',
      updated: '2025-01-05T10:30:00Z',
    },
    prix_base: 1500.00,
    delai: 24,
    is_available: true,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  {
    id: 'aa0e8400-e29b-41d4-a716-446655440002',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    service: '770e8400-e29b-41d4-a716-446655440002',
    service_details: {
      id: '770e8400-e29b-41d4-a716-446655440002',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      label: 'Lavage + Repassage',
      description: 'Lavage complet avec repassage professionnel',
      mode_tarif: 'piece',
      duree_estimee: 2880,
      icone: 'iron',
      is_active: true,
      created: '2025-01-05T10:30:00Z',
      updated: '2025-01-05T10:30:00Z',
    },
    prix_base: 500.00,
    delai: 48,
    is_available: true,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  {
    id: 'aa0e8400-e29b-41d4-a716-446655440003',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    service: '770e8400-e29b-41d4-a716-446655440003',
    service_details: {
      id: '770e8400-e29b-41d4-a716-446655440003',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      label: 'Nettoyage à sec',
      description: 'Nettoyage à sec pour tissus délicats',
      mode_tarif: 'piece',
      duree_estimee: 4320,
      icone: 'sparkles',
      is_active: true,
      created: '2025-01-05T10:30:00Z',
      updated: '2025-01-05T10:30:00Z',
    },
    prix_base: 1000.00,
    delai: 72,
    is_available: true,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  {
    id: 'aa0e8400-e29b-41d4-a716-446655440004',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    service: '770e8400-e29b-41d4-a716-446655440004',
    service_details: {
      id: '770e8400-e29b-41d4-a716-446655440004',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      label: 'Repassage uniquement',
      description: 'Service de repassage seul',
      mode_tarif: 'piece',
      duree_estimee: 720,
      icone: 'iron',
      is_active: true,
      created: '2025-01-05T10:30:00Z',
      updated: '2025-01-05T10:30:00Z',
    },
    prix_base: 200.00,
    delai: 12,
    is_available: true,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  {
    id: 'aa0e8400-e29b-41d4-a716-446655440005',
    provider: '660e8400-e29b-41d4-a716-446655440002',
    service: '770e8400-e29b-41d4-a716-446655440005',
    service_details: {
      id: '770e8400-e29b-41d4-a716-446655440005',
      provider: '660e8400-e29b-41d4-a716-446655440002',
      template: null,
      label: 'Repassage Express',
      description: 'Repassage rapide en moins de 3 heures',
      mode_tarif: 'piece',
      duree_estimee: 180,
      icone: 'zap',
      is_active: true,
      created: '2025-01-08T11:30:00Z',
      updated: '2025-01-08T11:30:00Z',
    },
    prix_base: 300.00,
    delai: 3,
    is_available: true,
    created: '2025-01-08T11:30:00Z',
    updated: '2025-01-08T11:30:00Z',
  },
  {
    id: 'aa0e8400-e29b-41d4-a716-446655440006',
    provider: '660e8400-e29b-41d4-a716-446655440002',
    service: '770e8400-e29b-41d4-a716-446655440006',
    service_details: {
      id: '770e8400-e29b-41d4-a716-446655440006',
      provider: '660e8400-e29b-41d4-a716-446655440002',
      template: null,
      label: 'Forfait Bureau',
      description: 'Forfait mensuel pour professionnels (10 chemises + 5 pantalons)',
      mode_tarif: 'forfait',
      duree_estimee: 1440,
      icone: 'briefcase',
      is_active: true,
      created: '2025-01-08T11:30:00Z',
      updated: '2025-01-08T11:30:00Z',
    },
    prix_base: 15000.00,
    delai: 24,
    is_available: true,
    created: '2025-01-08T11:30:00Z',
    updated: '2025-01-08T11:30:00Z',
  },
];

// ============================================================================
// TARIFS DÉTAILLÉS
// ============================================================================

export const mockTariffs: Tariff[] = [
  // Pressing Excellence - Chemise
  {
    id: 'bb0e8400-e29b-41d4-a716-446655440001',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    article_type: '880e8400-e29b-41d4-a716-446655440001',
    matiere: '990e8400-e29b-41d4-a716-446655440001', // Coton
    service: '770e8400-e29b-41d4-a716-446655440002', // Lavage + Repassage
    prix: 500.00,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  {
    id: 'bb0e8400-e29b-41d4-a716-446655440002',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    article_type: '880e8400-e29b-41d4-a716-446655440001',
    matiere: '990e8400-e29b-41d4-a716-446655440002', // Soie
    service: '770e8400-e29b-41d4-a716-446655440003', // Nettoyage à sec
    prix: 1500.00,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  // Pantalon
  {
    id: 'bb0e8400-e29b-41d4-a716-446655440003',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    article_type: '880e8400-e29b-41d4-a716-446655440002',
    matiere: '990e8400-e29b-41d4-a716-446655440001', // Coton
    service: '770e8400-e29b-41d4-a716-446655440002', // Lavage + Repassage
    prix: 700.00,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  // Costume
  {
    id: 'bb0e8400-e29b-41d4-a716-446655440004',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    article_type: '880e8400-e29b-41d4-a716-446655440004',
    matiere: '990e8400-e29b-41d4-a716-446655440003', // Laine
    service: '770e8400-e29b-41d4-a716-446655440003', // Nettoyage à sec
    prix: 3500.00,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  // Pagne
  {
    id: 'bb0e8400-e29b-41d4-a716-446655440005',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    article_type: '880e8400-e29b-41d4-a716-446655440005',
    matiere: '990e8400-e29b-41d4-a716-446655440005', // Wax
    service: '770e8400-e29b-41d4-a716-446655440002', // Lavage + Repassage
    prix: 1000.00,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  // Fanico - Repassage express
  {
    id: 'bb0e8400-e29b-41d4-a716-446655440006',
    provider: '660e8400-e29b-41d4-a716-446655440002',
    article_type: '880e8400-e29b-41d4-a716-446655440001',
    matiere: null,
    service: '770e8400-e29b-41d4-a716-446655440005',
    prix: 300.00,
    created: '2025-01-08T11:30:00Z',
    updated: '2025-01-08T11:30:00Z',
  },
];

// ============================================================================
// COMMANDES (ORDERS)
// ============================================================================

export const mockOrders: Order[] = [
  {
    id: 'cc0e8400-e29b-41d4-a716-446655440001',
    numero: 'ORD-2025-0001',
    client: '550e8400-e29b-41d4-a716-446655440001',
    client_details: {
      id: '550e8400-e29b-41d4-a716-446655440001',
      username: 'john_doe',
      first_name: 'John',
      last_name: 'Doe',
      phone: '+2250123456789',
    },
    provider: '660e8400-e29b-41d4-a716-446655440001',
    provider_details: {
      id: '660e8400-e29b-41d4-a716-446655440001',
      nom_commercial: 'Pressing Excellence',
      type: 'pressing',
      adresse: 'Cocody Angré 8ème Tranche, près du carrefour Stella',
      quartier: 'Angré',
    },
    statut: 'delivered',
    adresse_collecte: 'Cocody Riviera 3, Résidence les Lauriers, Bât. B, Appt 12',
    latitude_collecte: 5.360000,
    longitude_collecte: -3.987000,
    adresse_livraison: 'Cocody Riviera 3, Résidence les Lauriers, Bât. B, Appt 12',
    latitude_livraison: 5.360000,
    longitude_livraison: -3.987000,
    creneau_collecte: '2025-01-20T10:00:00Z',
    creneau_livraison: '2025-01-22T15:00:00Z',
    date_collecte: '2025-01-20T10:30:00Z',
    date_livraison: '2025-01-22T14:45:00Z',
    total_estime: 3200.00,
    total_final: 3200.00,
    frais_livraison: 500.00,
    notes_client: 'Attention taches de café sur la chemise blanche',
    notes_provider: 'Taches traitées avec succès',
    signature_client: 'https://example.com/signatures/sign-001.png',
    created: '2025-01-19T15:30:00Z',
    updated: '2025-01-22T14:45:00Z',
  },
  {
    id: 'cc0e8400-e29b-41d4-a716-446655440002',
    numero: 'ORD-2025-0002',
    client: '550e8400-e29b-41d4-a716-446655440002',
    client_details: {
      id: '550e8400-e29b-41d4-a716-446655440002',
      username: 'marie_kouame',
      first_name: 'Marie',
      last_name: 'Kouamé',
      phone: '+2250709876543',
    },
    provider: '660e8400-e29b-41d4-a716-446655440001',
    provider_details: {
      id: '660e8400-e29b-41d4-a716-446655440001',
      nom_commercial: 'Pressing Excellence',
      type: 'pressing',
      adresse: 'Cocody Angré 8ème Tranche',
      quartier: 'Angré',
    },
    statut: 'in_progress',
    adresse_collecte: 'Marcory Zone 4, Cité SICOGI, Villa 45',
    latitude_collecte: 5.342000,
    longitude_collecte: -4.024000,
    adresse_livraison: 'Marcory Zone 4, Cité SICOGI, Villa 45',
    latitude_livraison: 5.342000,
    longitude_livraison: -4.024000,
    creneau_collecte: '2025-01-28T14:00:00Z',
    creneau_livraison: '2025-01-30T16:00:00Z',
    date_collecte: '2025-01-28T14:15:00Z',
    date_livraison: null,
    total_estime: 4500.00,
    total_final: null,
    frais_livraison: 800.00,
    notes_client: 'Nettoyage délicat pour robe de soirée',
    notes_provider: 'En cours de traitement au nettoyage à sec',
    signature_client: null,
    created: '2025-01-27T11:20:00Z',
    updated: '2025-01-28T14:15:00Z',
  },
  {
    id: 'cc0e8400-e29b-41d4-a716-446655440003',
    numero: 'ORD-2025-0003',
    client: '550e8400-e29b-41d4-a716-446655440001',
    client_details: {
      id: '550e8400-e29b-41d4-a716-446655440001',
      username: 'john_doe',
      first_name: 'John',
      last_name: 'Doe',
      phone: '+2250123456789',
    },
    provider: '660e8400-e29b-41d4-a716-446655440002',
    provider_details: {
      id: '660e8400-e29b-41d4-a716-446655440002',
      nom_commercial: 'Fanico Rapide Express',
      type: 'fanico',
      adresse: 'Plateau, Rue du Commerce',
      quartier: 'Plateau',
    },
    statut: 'pending',
    adresse_collecte: 'Cocody Riviera 3, Résidence les Lauriers',
    latitude_collecte: 5.360000,
    longitude_collecte: -3.987000,
    adresse_livraison: 'Cocody Riviera 3, Résidence les Lauriers',
    latitude_livraison: 5.360000,
    longitude_livraison: -3.987000,
    creneau_collecte: '2025-01-31T09:00:00Z',
    creneau_livraison: null,
    date_collecte: null,
    date_livraison: null,
    total_estime: 1500.00,
    total_final: null,
    frais_livraison: 500.00,
    notes_client: 'Repassage rapide de 5 chemises pour lundi matin',
    notes_provider: '',
    signature_client: null,
    created: '2025-01-30T18:45:00Z',
    updated: '2025-01-30T18:45:00Z',
  },
];

// ============================================================================
// ARTICLES DE COMMANDE (ORDER ITEMS)
// ============================================================================

export const mockOrderItems: OrderItem[] = [
  // Commande 1
  {
    id: 'dd0e8400-e29b-41d4-a716-446655440001',
    order: 'cc0e8400-e29b-41d4-a716-446655440001',
    article_type: '880e8400-e29b-41d4-a716-446655440001',
    article_type_details: {
      id: '880e8400-e29b-41d4-a716-446655440001',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      nom: 'Chemise',
      description: 'Chemise homme ou femme',
      created: '2025-01-05T10:30:00Z',
    },
    matiere: '990e8400-e29b-41d4-a716-446655440001',
    matiere_details: {
      id: '990e8400-e29b-41d4-a716-446655440001',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      nom: 'Coton',
      description: 'Tissu en coton naturel',
      created: '2025-01-05T10:30:00Z',
    },
    service: '770e8400-e29b-41d4-a716-446655440002',
    service_details: {
      id: '770e8400-e29b-41d4-a716-446655440002',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      label: 'Lavage + Repassage',
      description: 'Lavage complet avec repassage professionnel',
      mode_tarif: 'piece',
      duree_estimee: 2880,
      icone: 'iron',
      is_active: true,
      created: '2025-01-05T10:30:00Z',
      updated: '2025-01-05T10:30:00Z',
    },
    quantite: 3,
    prix_unitaire: 500.00,
    total_ligne: 1500.00,
    photo: null,
    notes: 'Tache de café sur la chemise blanche',
    created: '2025-01-19T15:30:00Z',
  },
  {
    id: 'dd0e8400-e29b-41d4-a716-446655440002',
    order: 'cc0e8400-e29b-41d4-a716-446655440001',
    article_type: '880e8400-e29b-41d4-a716-446655440002',
    article_type_details: {
      id: '880e8400-e29b-41d4-a716-446655440002',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      nom: 'Pantalon',
      description: 'Pantalon classique ou jean',
      created: '2025-01-05T10:30:00Z',
    },
    matiere: '990e8400-e29b-41d4-a716-446655440001',
    matiere_details: {
      id: '990e8400-e29b-41d4-a716-446655440001',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      nom: 'Coton',
      description: 'Tissu en coton naturel',
      created: '2025-01-05T10:30:00Z',
    },
    service: '770e8400-e29b-41d4-a716-446655440002',
    service_details: {
      id: '770e8400-e29b-41d4-a716-446655440002',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      label: 'Lavage + Repassage',
      description: 'Lavage complet avec repassage professionnel',
      mode_tarif: 'piece',
      duree_estimee: 2880,
      icone: 'iron',
      is_active: true,
      created: '2025-01-05T10:30:00Z',
      updated: '2025-01-05T10:30:00Z',
    },
    quantite: 2,
    prix_unitaire: 700.00,
    total_ligne: 1400.00,
    photo: null,
    notes: '',
    created: '2025-01-19T15:30:00Z',
  },
  // Commande 2
  {
    id: 'dd0e8400-e29b-41d4-a716-446655440003',
    order: 'cc0e8400-e29b-41d4-a716-446655440002',
    article_type: '880e8400-e29b-41d4-a716-446655440003',
    article_type_details: {
      id: '880e8400-e29b-41d4-a716-446655440003',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      nom: 'Robe',
      description: 'Robe de soirée ou casual',
      created: '2025-01-05T10:30:00Z',
    },
    matiere: '990e8400-e29b-41d4-a716-446655440002',
    matiere_details: {
      id: '990e8400-e29b-41d4-a716-446655440002',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      nom: 'Soie',
      description: 'Tissu en soie délicate',
      created: '2025-01-05T10:30:00Z',
    },
    service: '770e8400-e29b-41d4-a716-446655440003',
    service_details: {
      id: '770e8400-e29b-41d4-a716-446655440003',
      provider: '660e8400-e29b-41d4-a716-446655440001',
      template: null,
      label: 'Nettoyage à sec',
      description: 'Nettoyage à sec pour tissus délicats',
      mode_tarif: 'piece',
      duree_estimee: 4320,
      icone: 'sparkles',
      is_active: true,
      created: '2025-01-05T10:30:00Z',
      updated: '2025-01-05T10:30:00Z',
    },
    quantite: 1,
    prix_unitaire: 3500.00,
    total_ligne: 3500.00,
    photo: 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=400',
    notes: 'Robe de soirée en soie précieuse - traitement délicat requis',
    created: '2025-01-27T11:20:00Z',
  },
];

// ============================================================================
// PAIEMENTS (PAYMENTS)
// ============================================================================

export const mockPayments: Payment[] = [
  {
    id: 'ee0e8400-e29b-41d4-a716-446655440001',
    order: 'cc0e8400-e29b-41d4-a716-446655440001',
    reference: 'PAY-1706012400-ABC12345',
    operateur: 'orange',
    numero_payeur: '+2250123456789',
    montant: 3700.00,
    statut: 'completed',
    transaction_id: 'OM-2025-012345678',
    metadata: {
      operator_name: 'Orange Money',
      payment_method: 'mobile_money',
    },
    error_message: '',
    date_initiation: '2025-01-22T14:50:00Z',
    date_completion: '2025-01-22T14:51:30Z',
    is_refund: false,
    refund_of: null,
    created: '2025-01-22T14:50:00Z',
    updated: '2025-01-22T14:51:30Z',
  },
  {
    id: 'ee0e8400-e29b-41d4-a716-446655440002',
    order: 'cc0e8400-e29b-41d4-a716-446655440002',
    reference: 'PAY-1706875200-DEF67890',
    operateur: 'mtn',
    numero_payeur: '+2250709876543',
    montant: 5300.00,
    statut: 'pending',
    transaction_id: '',
    metadata: {
      operator_name: 'MTN Mobile Money',
      payment_method: 'mobile_money',
    },
    error_message: '',
    date_initiation: '2025-01-28T14:20:00Z',
    date_completion: null,
    is_refund: false,
    refund_of: null,
    created: '2025-01-28T14:20:00Z',
    updated: '2025-01-28T14:20:00Z',
  },
  {
    id: 'ee0e8400-e29b-41d4-a716-446655440003',
    order: 'cc0e8400-e29b-41d4-a716-446655440003',
    reference: 'PAY-1706989800-GHI11223',
    operateur: 'wave',
    numero_payeur: '+2250123456789',
    montant: 2000.00,
    statut: 'failed',
    transaction_id: '',
    metadata: {
      operator_name: 'Wave',
      payment_method: 'mobile_money',
    },
    error_message: 'Solde insuffisant',
    date_initiation: '2025-01-30T19:00:00Z',
    date_completion: null,
    is_refund: false,
    refund_of: null,
    created: '2025-01-30T19:00:00Z',
    updated: '2025-01-30T19:02:00Z',
  },
];

// ============================================================================
// AVIS (REVIEWS)
// ============================================================================

export const mockReviews: Review[] = [
  {
    id: 'ff0e8400-e29b-41d4-a716-446655440001',
    client: '550e8400-e29b-41d4-a716-446655440001',
    client_details: {
      username: 'john_doe',
      first_name: 'John',
      last_name: 'Doe',
      photo_profil: null,
    },
    provider: '660e8400-e29b-41d4-a716-446655440001',
    order: 'cc0e8400-e29b-41d4-a716-446655440001',
    note: 5,
    commentaire: 'Excellent service ! Mes vêtements sont impeccables et la livraison était à l\'heure. Je recommande vivement Pressing Excellence.',
    note_qualite: 5,
    note_delai: 5,
    note_service: 5,
    is_approved: true,
    is_flagged: false,
    reponse_provider: 'Merci beaucoup pour votre confiance ! Nous sommes ravis de vous avoir satisfait.',
    date_reponse: '2025-01-23T09:00:00Z',
    created: '2025-01-22T16:30:00Z',
    updated: '2025-01-23T09:00:00Z',
  },
  {
    id: 'ff0e8400-e29b-41d4-a716-446655440002',
    client: '550e8400-e29b-41d4-a716-446655440002',
    client_details: {
      username: 'marie_kouame',
      first_name: 'Marie',
      last_name: 'Kouamé',
      photo_profil: 'https://i.pravatar.cc/150?img=1',
    },
    provider: '660e8400-e29b-41d4-a716-446655440004',
    order: 'cc0e8400-e29b-41d4-a716-446655440004',
    note: 4,
    commentaire: 'Bon service dans l\'ensemble. Le nettoyage était parfait mais la livraison avait 30 minutes de retard.',
    note_qualite: 5,
    note_delai: 3,
    note_service: 4,
    is_approved: true,
    is_flagged: false,
    reponse_provider: '',
    date_reponse: null,
    created: '2025-01-25T17:00:00Z',
    updated: '2025-01-25T17:00:00Z',
  },
];

// ============================================================================
// PERMISSIONS
// ============================================================================

export const mockPermissions: Permission[] = [
  {
    id: 'gg0e8400-e29b-41d4-a716-446655440001',
    code: 'view_orders',
    name: 'Voir les commandes',
    description: 'Permet de consulter la liste des commandes',
    module: 'orders',
    is_active: true,
    created: '2025-01-01T00:00:00Z',
  },
  {
    id: 'gg0e8400-e29b-41d4-a716-446655440002',
    code: 'manage_orders',
    name: 'Gérer les commandes',
    description: 'Permet de créer, modifier et supprimer des commandes',
    module: 'orders',
    is_active: true,
    created: '2025-01-01T00:00:00Z',
  },
  {
    id: 'gg0e8400-e29b-41d4-a716-446655440003',
    code: 'view_stats',
    name: 'Voir les statistiques',
    description: 'Permet de consulter les statistiques et rapports',
    module: 'stats',
    is_active: true,
    created: '2025-01-01T00:00:00Z',
  },
  {
    id: 'gg0e8400-e29b-41d4-a716-446655440004',
    code: 'manage_services',
    name: 'Gérer les services',
    description: 'Permet de créer et modifier les services proposés',
    module: 'services',
    is_active: true,
    created: '2025-01-01T00:00:00Z',
  },
  {
    id: 'gg0e8400-e29b-41d4-a716-446655440005',
    code: 'manage_tariffs',
    name: 'Gérer les tarifs',
    description: 'Permet de définir et modifier les tarifs',
    module: 'tariffs',
    is_active: true,
    created: '2025-01-01T00:00:00Z',
  },
  {
    id: 'gg0e8400-e29b-41d4-a716-446655440006',
    code: 'manage_staff',
    name: 'Gérer le personnel',
    description: 'Permet de gérer les employés et leurs rôles',
    module: 'staff',
    is_active: true,
    created: '2025-01-01T00:00:00Z',
  },
];

// ============================================================================
// RÔLES PERSONNALISÉS
// ============================================================================

export const mockRoles: Role[] = [
  {
    id: 'hh0e8400-e29b-41d4-a716-446655440001',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    name: 'Manager',
    description: 'Responsable du pressing avec accès complet',
    permissions: mockPermissions.slice(0, 5),
    is_active: true,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
  {
    id: 'hh0e8400-e29b-41d4-a716-446655440002',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    name: 'Opérateur',
    description: 'Employé en charge du traitement des commandes',
    permissions: mockPermissions.slice(0, 2),
    is_active: true,
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-05T10:30:00Z',
  },
];

// ============================================================================
// PARAMÈTRES PRESTATAIRES
// ============================================================================

export const mockProviderSettings: ProviderSettings[] = [
  {
    id: 'ii0e8400-e29b-41d4-a716-446655440001',
    provider: '660e8400-e29b-41d4-a716-446655440001',
    business_name: 'Pressing Excellence - Cocody',
    logo: 'https://ui-avatars.com/api/?name=Pressing+Excellence&background=f97316&color=fff&size=200',
    primary_color: '#f97316',
    auto_accept_orders: false,
    require_payment_before: true,
    min_order_amount: 1000.00,
    delivery_fee: 500.00,
    email_notifications: true,
    sms_notifications: true,
    notification_email: 'contact@pressingexcellence.ci',
    notification_phone: '+2250778123456',
    opening_hours: {
      lundi: { ouvert: true, heures: '08:00-18:00' },
      mardi: { ouvert: true, heures: '08:00-18:00' },
      mercredi: { ouvert: true, heures: '08:00-18:00' },
      jeudi: { ouvert: true, heures: '08:00-18:00' },
      vendredi: { ouvert: true, heures: '08:00-18:00' },
      samedi: { ouvert: true, heures: '09:00-15:00' },
      dimanche: { ouvert: false, heures: '' },
    },
    metadata: {
      slogan: 'Votre satisfaction, notre priorité',
      description_longue: 'Service de pressing haut de gamme à Cocody',
    },
    created: '2025-01-05T10:30:00Z',
    updated: '2025-01-20T15:30:00Z',
  },
  {
    id: 'ii0e8400-e29b-41d4-a716-446655440002',
    provider: '660e8400-e29b-41d4-a716-446655440002',
    business_name: 'Fanico Rapide Express',
    logo: 'https://ui-avatars.com/api/?name=Fanico+Rapide&background=10b981&color=fff&size=200',
    primary_color: '#10b981',
    auto_accept_orders: true,
    require_payment_before: false,
    min_order_amount: 500.00,
    delivery_fee: 300.00,
    email_notifications: true,
    sms_notifications: false,
    notification_email: 'aya.traore@fanico.ci',
    notification_phone: '+2250501234567',
    opening_hours: {
      lundi: { ouvert: true, heures: '07:00-20:00' },
      mardi: { ouvert: true, heures: '07:00-20:00' },
      mercredi: { ouvert: true, heures: '07:00-20:00' },
      jeudi: { ouvert: true, heures: '07:00-20:00' },
      vendredi: { ouvert: true, heures: '07:00-20:00' },
      samedi: { ouvert: true, heures: '08:00-18:00' },
      dimanche: { ouvert: true, heures: '10:00-16:00' },
    },
    metadata: {
      slogan: 'Repassage express en 3 heures',
      disponibilite: '7j/7',
    },
    created: '2025-01-08T11:30:00Z',
    updated: '2025-01-22T09:15:00Z',
  },
];

// ============================================================================
// CODES OTP
// ============================================================================

export const mockOTPCodes: OTPCode[] = [
  {
    id: 'jj0e8400-e29b-41d4-a716-446655440001',
    phone: '+2250123456789',
    purpose: 'phone_verification',
    attempts: 1,
    is_verified: true,
    created_at: '2025-01-30T20:00:00Z',
    expires_at: '2025-01-30T20:10:00Z',
    verified_at: '2025-01-30T20:02:00Z',
  },
  {
    id: 'jj0e8400-e29b-41d4-a716-446655440002',
    phone: '+2250709876543',
    purpose: 'reset_password',
    attempts: 0,
    is_verified: false,
    created_at: '2025-01-30T20:15:00Z',
    expires_at: '2025-01-30T20:25:00Z',
    verified_at: null,
  },
];

// ============================================================================
// DONNÉES D'AUTHENTIFICATION POUR SIMULATION
// ============================================================================

export const mockAuthData = {
  // Utilisateurs avec mots de passe (pour simulation de connexion)
  credentials: [
    {
      username: 'john_doe',
      email: 'john.doe@gmail.com',
      phone: '+2250123456789',
      password: 'Password123!',
      user: mockUsers[0],
    },
    {
      username: 'marie_kouame',
      email: 'marie.kouame@yahoo.fr',
      phone: '+2250709876543',
      password: 'SecurePass456!',
      user: mockUsers[1],
    },
    {
      username: 'pressing_excellence',
      email: 'contact@pressingexcellence.ci',
      phone: '+2250778123456',
      password: 'PressingAdmin789!',
      user: mockUsers[2],
    },
    {
      username: 'fanico_rapide',
      email: 'aya.traore@fanico.ci',
      phone: '+2250501234567',
      password: 'FanicoSecure321!',
      user: mockUsers[3],
    },
    {
      username: 'admin_presso',
      email: 'admin@presso.ci',
      phone: '+2250777888999',
      password: 'AdminPresso2025!',
      user: mockUsers[4],
    },
  ],

  // Tokens JWT simulés
  tokens: {
    access_sample: 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAtZTI5Yi00MWQ0LWE3MTYtNDQ2NjU1NDQwMDAxIiwidXNlcm5hbWUiOiJqb2huX2RvZSIsImVtYWlsIjoiam9obi5kb2VAZ21haWwuY29tIiwicGhvbmUiOiIrMjI1MDEyMzQ1Njc4OSIsInJvbGUiOiJjbGllbnQifQ.mock_signature',
    refresh_sample: 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiNTUwZTg0MDAtZTI5Yi00MWQ0LWE3MTYtNDQ2NjU1NDQwMDAxIiwidG9rZW5fdHlwZSI6InJlZnJlc2gifQ.mock_refresh_signature',
  },

  // Réponses API simulées pour l'inscription
  registerResponse: {
    message: 'Inscription réussie. Vous pouvez maintenant vous connecter.',
    user: {
      id: 'nouveau-uuid-genere',
      username: 'nouveau_user',
      email: 'nouveau@example.com',
      phone: '+2250123456789',
    },
  },

  // Réponse OTP
  otpResponse: {
    phone: '+2250123456789',
    expires_at: new Date(Date.now() + 10 * 60 * 1000).toISOString(), // Expire dans 10 minutes
    message: 'Code OTP envoyé au +2250123456789',
  },

  // Code OTP de test (pour dev uniquement)
  testOTP: '123456',
};

// ============================================================================
// FONCTIONS UTILITAIRES POUR SIMULATION
// ============================================================================

/**
 * Simule une authentification
 */
export function simulateLogin(usernameOrEmailOrPhone: string, password: string) {
  const user = mockAuthData.credentials.find(
    (cred) =>
      cred.username === usernameOrEmailOrPhone ||
      cred.email === usernameOrEmailOrPhone ||
      cred.phone === usernameOrEmailOrPhone
  );

  if (user && user.password === password) {
    return {
      access: mockAuthData.tokens.access_sample,
      refresh: mockAuthData.tokens.refresh_sample,
      user: user.user,
    };
  }

  throw new Error('Identifiants incorrects');
}

/**
 * Simule l'envoi d'un code OTP
 */
export function simulateOTPRequest(phone: string, purpose: string) {
  return {
    phone,
    expires_at: new Date(Date.now() + 10 * 60 * 1000).toISOString(),
    message: `Code OTP envoyé au ${phone}`,
  };
}

/**
 * Simule la vérification d'un code OTP
 */
export function simulateOTPVerify(phone: string, code: string, purpose: string) {
  if (code === mockAuthData.testOTP) {
    return {
      phone,
      purpose,
      verified: true,
      otp_id: 'otp-uuid-verified',
      message: 'Numéro de téléphone vérifié avec succès',
    };
  }

  throw new Error('Code incorrect');
}

/**
 * Trouve les prestataires proches d'une position
 */
export function findNearbyProviders(latitude: number, longitude: number, maxKm: number = 10) {
  // Simulation simple de distance (en réalité il faudrait calculer la vraie distance)
  return mockProviders
    .filter((p) => p.is_active && p.statut_kyc === 'verified')
    .map((p) => ({
      ...p,
      distance: Math.random() * maxKm, // Distance simulée
    }))
    .sort((a, b) => a.distance - b.distance);
}

/**
 * Filtre les commandes par utilisateur
 */
export function getOrdersByUser(userId: string) {
  return mockOrders.filter((order) => order.client === userId);
}

/**
 * Filtre les commandes par prestataire
 */
export function getOrdersByProvider(providerId: string) {
  return mockOrders.filter((order) => order.provider === providerId);
}

/**
 * Récupère les articles d'une commande
 */
export function getOrderItems(orderId: string) {
  return mockOrderItems.filter((item) => item.order === orderId);
}

/**
 * Récupère les paiements d'une commande
 */
export function getPaymentsByOrder(orderId: string) {
  return mockPayments.filter((payment) => payment.order === orderId);
}

/**
 * Récupère les avis d'un prestataire
 */
export function getReviewsByProvider(providerId: string) {
  return mockReviews.filter((review) => review.provider === providerId);
}

/**
 * Calcule la note moyenne d'un prestataire
 */
export function getProviderAverageRating(providerId: string) {
  const reviews = getReviewsByProvider(providerId);
  if (reviews.length === 0) return 0;

  const sum = reviews.reduce((acc, review) => acc + review.note, 0);
  return (sum / reviews.length).toFixed(1);
}

// Export par défaut de toutes les données
export default {
  users: mockUsers,
  providers: mockProviders,
  services: mockServices,
  articleTypes: mockArticleTypes,
  matieres: mockMatieres,
  providerServices: mockProviderServices,
  tariffs: mockTariffs,
  orders: mockOrders,
  orderItems: mockOrderItems,
  payments: mockPayments,
  reviews: mockReviews,
  permissions: mockPermissions,
  roles: mockRoles,
  providerSettings: mockProviderSettings,
  otpCodes: mockOTPCodes,
  auth: mockAuthData,
  
  // Fonctions utilitaires
  utils: {
    simulateLogin,
    simulateOTPRequest,
    simulateOTPVerify,
    findNearbyProviders,
    getOrdersByUser,
    getOrdersByProvider,
    getOrderItems,
    getPaymentsByOrder,
    getReviewsByProvider,
    getProviderAverageRating,
  },
};

