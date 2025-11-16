# =================================================================
# PRESSO - Makefile Principal
# =================================================================
# Commandes utiles pour gérer l'application Docker
# =================================================================

.PHONY: help build up down restart logs shell migrate makemigrations createsuperuser test clean

# Couleurs pour les messages
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Répertoires
BACKEND_DIR := backend
ENV_FILE := .env
ENV_EXAMPLE := .env.example

help: ## Afficher l'aide
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(GREEN)     PRESSO - Commandes Docker$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(YELLOW)%-18s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Construire les images Docker
	@echo "$(BLUE)🔨 Construction des images Docker...$(NC)"
	docker-compose build

up: ## Démarrer tous les services
	@echo "$(BLUE)🚀 Démarrage des services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)✅ Services démarrés !$(NC)"
	@echo "$(YELLOW)API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Swagger: http://localhost:8000/api/docs/$(NC)"
	@echo "$(YELLOW)Admin: http://localhost:8000/admin/$(NC)"

down: ## Arrêter tous les services
	@echo "$(BLUE)🛑 Arrêt des services...$(NC)"
	docker-compose down
	@echo "$(GREEN)✅ Services arrêtés$(NC)"

restart: down up ## Redémarrer tous les services

logs: ## Voir les logs (docker-compose logs -f)
	docker-compose logs -f

logs-backend: ## Voir les logs du backend uniquement
	docker-compose logs -f backend

logs-celery: ## Voir les logs de Celery
	docker-compose logs -f celery-worker celery-beat

shell: ## Ouvrir un shell Django
	docker-compose exec backend python manage.py shell

bash: ## Ouvrir un bash dans le conteneur backend
	docker-compose exec backend bash

migrate: ## Appliquer les migrations
	@echo "$(BLUE)📦 Application des migrations...$(NC)"
	docker-compose exec backend python manage.py migrate
	@echo "$(GREEN)✅ Migrations appliquées$(NC)"

makemigrations: ## Créer de nouvelles migrations
	@echo "$(BLUE)📝 Création des migrations...$(NC)"
	docker-compose exec backend python manage.py makemigrations
	@echo "$(GREEN)✅ Migrations créées$(NC)"

createsuperuser: ## Créer un superutilisateur
	docker-compose exec backend python manage.py createsuperuser

collectstatic: ## Collecter les fichiers statiques
	docker-compose exec backend python manage.py collectstatic --noinput

test: ## Lancer les tests
	docker-compose exec backend python manage.py test

check: ## Vérifier la configuration Django
	docker-compose exec backend python manage.py check

generate-secrets: ## Générer des secrets sécurisés (DJANGO_SECRET_KEY, JWT_SECRET_KEY, DB_PASSWORD)
	@echo "$(BLUE)🔐 Génération des secrets sécurisés...$(NC)"
	@python3 generate_secrets.py

init: ## Initialiser le projet (première installation)
	@echo "$(BLUE)🎉 Initialisation de PRESSO...$(NC)"
	@if [ ! -f $(ENV_FILE) ]; then \
		echo "$(YELLOW)📝 Création du fichier .env depuis .env.example...$(NC)"; \
		cp $(ENV_EXAMPLE) $(ENV_FILE); \
		echo ""; \
		echo "$(BLUE)🔐 Génération des secrets sécurisés...$(NC)"; \
		echo ""; \
		python3 generate_secrets.py; \
		echo ""; \
		echo "$(RED)⚠️  IMPORTANT: Copiez les secrets ci-dessus dans votre .env !$(NC)"; \
		echo ""; \
		echo "$(YELLOW)Pour éditer le fichier .env :$(NC)"; \
		echo "  nano $(ENV_FILE)"; \
		echo ""; \
		echo "$(YELLOW)Variables à modifier obligatoirement :$(NC)"; \
		echo "  - DJANGO_SECRET_KEY (copier depuis ci-dessus)"; \
		echo "  - JWT_SECRET_KEY (copier depuis ci-dessus)"; \
		echo "  - DB_PASSWORD (copier depuis ci-dessus)"; \
		echo "  - D7_API_TOKEN"; \
		echo "  - D7_ORIGINATOR"; \
		echo ""; \
		read -p "Appuyez sur Entrée pour continuer après avoir modifié .env..." dummy; \
	else \
		echo "$(GREEN)✅ Fichier .env déjà existant$(NC)"; \
	fi
	@echo "$(BLUE)🔨 Construction des images...$(NC)"
	docker-compose build
	@echo "$(BLUE)🚀 Démarrage des services...$(NC)"
	docker-compose up -d
	@echo "$(YELLOW)⏳ Attente du démarrage des services (20s)...$(NC)"
	@sleep 20
	@echo "$(BLUE)📦 Application des migrations...$(NC)"
	docker-compose exec backend python manage.py migrate
	@echo "$(BLUE)📊 Collecte des fichiers statiques...$(NC)"
	docker-compose exec backend python manage.py collectstatic --noinput
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)✅ PRESSO est prêt !$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(YELLOW)API: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Admin: http://localhost:8000/admin$(NC)"
	@echo "$(YELLOW)Swagger: http://localhost:8000/api/docs/$(NC)"
	@echo ""
	@echo "$(BLUE)Créez maintenant un superutilisateur:$(NC)"
	@echo "  $(YELLOW)make createsuperuser$(NC)"

ps: ## Voir l'état des services
	docker-compose ps

clean: ## Nettoyer les conteneurs et volumes
	@echo "$(RED)⚠️  Attention: Cette commande va supprimer tous les conteneurs et volumes !$(NC)"
	@echo "$(RED)⚠️  Les données de la base de données seront perdues !$(NC)"
	@read -p "Continuer ? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	docker-compose down -v
	@echo "$(GREEN)✅ Nettoyage terminé$(NC)"

db-shell: ## Ouvrir un shell PostgreSQL
	docker-compose exec postgres psql -U $$(grep DB_USER $(ENV_FILE) | cut -d '=' -f2) -d $$(grep DB_NAME $(ENV_FILE) | cut -d '=' -f2)

redis-cli: ## Ouvrir Redis CLI
	docker-compose exec redis redis-cli

celery-status: ## Voir le statut de Celery
	docker-compose exec celery-worker celery -A config inspect active

celery-purge: ## Purger toutes les tâches Celery en attente
	docker-compose exec celery-worker celery -A config purge

celery-tasks: ## Lister toutes les tâches Celery enregistrées
	@echo "$(BLUE)📋 Tâches Celery enregistrées :$(NC)"
	docker-compose exec celery-worker celery -A config inspect registered

backup-db: ## Sauvegarder la base de données
	@echo "$(BLUE)💾 Sauvegarde de la base de données...$(NC)"
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U $$(grep DB_USER $(ENV_FILE) | cut -d '=' -f2) $$(grep DB_NAME $(ENV_FILE) | cut -d '=' -f2) > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✅ Sauvegarde créée dans backups/$(NC)"

restore-db: ## Restaurer la base de données (usage: make restore-db FILE=backups/backup_xxx.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)❌ Erreur: Spécifiez le fichier avec FILE=backups/backup_xxx.sql$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)📦 Restauration de la base de données depuis $(FILE)...$(NC)"
	docker-compose exec -T postgres psql -U $$(grep DB_USER $(ENV_FILE) | cut -d '=' -f2) $$(grep DB_NAME $(ENV_FILE) | cut -d '=' -f2) < $(FILE)
	@echo "$(GREEN)✅ Restauration terminée$(NC)"

# =================================================================
# Commandes spécifiques au développement
# =================================================================

dev-shell: bash ## Alias pour bash

pip-install: ## Installer une nouvelle dépendance (usage: make pip-install PKG=requests)
	@if [ -z "$(PKG)" ]; then \
		echo "$(RED)❌ Erreur: Spécifiez le package avec PKG=nom_du_package$(NC)"; \
		exit 1; \
	fi
	docker-compose exec backend pip install $(PKG)
	docker-compose exec backend pip freeze > $(BACKEND_DIR)/requirements.txt
	@echo "$(GREEN)✅ Package $(PKG) installé et requirements.txt mis à jour$(NC)"

pip-freeze: ## Générer requirements.txt
	docker-compose exec backend pip freeze > $(BACKEND_DIR)/requirements.txt
	@echo "$(GREEN)✅ requirements.txt mis à jour$(NC)"

# =================================================================
# Gestion des apps Django
# =================================================================

startapp: ## Créer une nouvelle app Django (usage: make startapp APP=nom_app)
	@if [ -z "$(APP)" ]; then \
		echo "$(RED)❌ Erreur: Spécifiez le nom de l'app avec APP=nom_app$(NC)"; \
		exit 1; \
	fi
	docker-compose exec backend python manage.py startapp $(APP) apps/$(APP)
	@echo "$(GREEN)✅ App $(APP) créée dans apps/$(APP)$(NC)"
	@echo "$(YELLOW)N'oubliez pas d'ajouter 'apps.$(APP)' dans INSTALLED_APPS !$(NC)"

# =================================================================
# Monitoring et debugging
# =================================================================

stats: ## Afficher les statistiques des conteneurs
	docker stats --no-stream

inspect-backend: ## Inspecter le conteneur backend
	docker inspect presso_backend

inspect-postgres: ## Inspecter le conteneur postgres
	docker inspect presso_postgres

inspect-redis: ## Inspecter le conteneur redis
	docker inspect presso_redis

# =================================================================
# Production
# =================================================================

prod-build: ## Build pour production
	@echo "$(BLUE)🏭 Construction des images pour production...$(NC)"
	docker-compose -f docker-compose.yml build --no-cache
	@echo "$(GREEN)✅ Images construites$(NC)"

prod-up: ## Démarrer en mode production
	@echo "$(BLUE)🚀 Démarrage en mode production...$(NC)"
	docker-compose -f docker-compose.yml up -d
	@echo "$(GREEN)✅ Services démarrés en production$(NC)"

