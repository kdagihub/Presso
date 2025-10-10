#!/bin/bash

# 🧼 Script d'initialisation automatique - Presso Backend
# Ce script configure automatiquement la base de données et les données initiales

set -e  # Arrêter en cas d'erreur

echo "🧼 =========================================="
echo "   PRESSO - Initialisation Backend"
echo "=========================================="
echo ""

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Vérifier si le virtualenv est activé
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠️  Activation du virtualenv...${NC}"
    source venv/bin/activate
fi

# Installer Pillow si nécessaire
echo -e "${YELLOW}📦 Vérification des dépendances...${NC}"
pip install Pillow --quiet

# Demander si on veut reset la DB
echo ""
read -p "Voulez-vous réinitialiser la base de données ? (o/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[OoYy]$ ]]; then
    echo -e "${YELLOW}🗑️  Suppression de l'ancienne base de données...${NC}"
    rm -f db.sqlite3
    find apps/*/migrations/ -name "000*.py" -delete 2>/dev/null || true
    echo -e "${GREEN}✓ Base de données supprimée${NC}"
fi

# Créer les migrations
echo ""
echo -e "${YELLOW}🔨 Création des migrations...${NC}"
python manage.py makemigrations users
python manage.py makemigrations providers
python manage.py makemigrations services
python manage.py makemigrations tariffs
python manage.py makemigrations orders
python manage.py makemigrations order_items
python manage.py makemigrations payments
python manage.py makemigrations reviews
echo -e "${GREEN}✓ Migrations créées${NC}"

# Appliquer les migrations
echo ""
echo -e "${YELLOW}📊 Application des migrations...${NC}"
python manage.py migrate
echo -e "${GREEN}✓ Migrations appliquées${NC}"

# Initialiser les groupes
echo ""
echo -e "${YELLOW}👥 Initialisation des groupes Django...${NC}"
python manage.py init_groups
echo -e "${GREEN}✓ Groupes initialisés${NC}"

# Initialiser les services
echo ""
echo -e "${YELLOW}🧺 Initialisation des services de base...${NC}"
python manage.py init_services
echo -e "${GREEN}✓ Services initialisés${NC}"

# Créer le superuser
echo ""
echo -e "${YELLOW}👤 Création du superutilisateur...${NC}"
echo "Laissez les champs vides pour utiliser les valeurs par défaut"
python manage.py createsuperuser --noinput \
    --username=admin \
    --email=admin@presso.ci \
    2>/dev/null || python manage.py createsuperuser

echo ""
echo -e "${GREEN}=========================================="
echo "✅ Initialisation terminée avec succès !"
echo "==========================================${NC}"
echo ""
echo "📝 Commandes utiles :"
echo "  • Lancer le serveur : python manage.py runserver"
echo "  • Accéder à l'admin : http://127.0.0.1:8000/admin/"
echo "  • Créer un user : python manage.py createsuperuser"
echo ""
echo "📚 Documentation complète : ./SETUP.md"
echo ""

