Voici ce qui reste côté prestataire, en suivant l’architecture multi-tenant déjà posée :

### 1. Tarification & catalogue avancé
- **ProviderService + Tariff** : exposer lier `Service` ↔ `ProviderService` (prix/délai de base) puis `Tariff` (article/matière/service).  
- **Endpoints** :
  - CRUD sur `ProviderService` enrichi (actuellement seulement service “description/inactive”). Ajouter prix, délais, disponibilité.
  - Gestion des `ArticleType`/`Matiere` personnalisés (déjà modélisés) et tarifs par combinaison.  
- **Permissions** : `services.manage`, `tariffs.manage`.  
- **Public API** : GET catalogue pour clients (par prestataire, filtrage par agence, etc.).

### 2. Commandes / Order Management
- **Workflow** : création, affectation agence/staff, statuts (reçu, en traitement, prêt, livré), pick-up/delivery.  
- **Endpoints** :
  - CRUD tenant-aware sur `Order`, `OrderItem`, `Payment` (selon modèles existants).  
  - Actions : changement de statut, assignation livreur, historique.  
- **Permissions** : `orders.view`/`orders.manage` selon rôles.

### 3. Paiements & facturation
- **Modules existants** (`apps/payments`) à exposer : intégration passerelles, suivi encaissements, factures.  
- **Endpoints** : listing des paiements par provider, création de transactions (ex. marquer un paiement comme reçu), rapports financiers.  
- **Sécurité** : `payments.view/manage`, conformité (justifs, logs).

### 4. Reviews & satisfaction
- **Modèles** (`apps/reviews`) => API pour que les clients soumettent des avis, et pour que les providers consultent/modèrent.  
- **Fonctions** :
  - GET/POST côté client (sans auth provider).
  - GET/patch (modération) côté provider (permissions `reviews.manage`).

### 5. Notifications & staff
- Déjà amorcé, mais il faudra brancher les actions (nouvelle commande, review, etc.) sur email/SMS/push.
- Invites staff : ajout d’envoi e-mail/sms réel, ré-invitations, audit.

### 6. Paramétrage avancé
- `ProviderSettings` : compléter (adresse de facturation, TVA, préférences livraison, intégrations externes).  
- `ProviderAgency` : associer horaires spécifiques, disponibilité.

### 7. Public API / marketplace
- Endpoints pour que les clients consultent :
  - liste des providers filtrés (ville, type).
  - catalogue des services + tarifs (agrégation `ProviderService` + `Tariff`).
  - disponibilité/agences.

### 8. Observabilité / audit
- Logs d’activité staff (création service, changement prix).
- Rapports multi-agences (stats, CA par agence/service).
