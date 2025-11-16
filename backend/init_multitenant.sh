#!/bin/bash

# 🏗️ Script d'initialisation multitenant - Presso
# Initialise l'architecture multitenant complète

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "  PRESSO - Init Architecture Multitenant"
echo "==========================================${NC}"
echo ""

# 1. Migrations
echo -e "${YELLOW}📦 Création des migrations...${NC}"
python manage.py makemigrations core
python manage.py makemigrations users
python manage.py makemigrations providers
python manage.py makemigrations services
python manage.py makemigrations tariffs
python manage.py makemigrations orders
python manage.py makemigrations order_items
python manage.py makemigrations payments
python manage.py makemigrations reviews

echo -e "${GREEN}✓ Migrations créées${NC}"
echo ""

# 2. Application des migrations
echo -e "${YELLOW}🔨 Application des migrations...${NC}"
python manage.py migrate
echo -e "${GREEN}✓ Migrations appliquées${NC}"
echo ""

# 3. Groupes Django
echo -e "${YELLOW}👥 Initialisation des groupes Django...${NC}"
python manage.py init_groups
echo ""

# 4. Permissions
echo -e "${YELLOW}🔐 Initialisation des permissions...${NC}"
python manage.py init_permissions
echo ""

# 5. Templates
echo -e "${YELLOW}📋 Initialisation des templates...${NC}"
python manage.py init_templates
echo ""

echo -e "${GREEN}=========================================="
echo "✅ Architecture multitenant initialisée !"
echo "==========================================${NC}"
echo ""
echo "📝 Prochaines étapes :"
echo "  1. Créer un superutilisateur : python manage.py createsuperuser"
echo "  2. Lancer le serveur : python manage.py runserver"
echo "  3. Accéder à l'admin : http://127.0.0.1:8000/admin/"
echo ""
echo "📚 Documentation : ./ARCHITECTURE_MULTITENANT.md"
echo ""

