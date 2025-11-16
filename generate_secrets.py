#!/usr/bin/env python3
"""
Script pour générer des secrets sécurisés pour PRESSO
Usage: python generate_secrets.py
"""
import secrets
import string


def generate_django_secret_key(length=64):
    """
    Génère une clé secrète Django (64 caractères)
    Format: Alphanumériques + caractères spéciaux Django-safe
    """
    chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_jwt_secret_key(length=64):
    """
    Génère une clé secrète JWT (64 caractères)
    Format: Alphanumériques + quelques caractères spéciaux
    """
    chars = string.ascii_letters + string.digits + '-_!@#$%^&*()'
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_db_password(length=32):
    """
    Génère un mot de passe DB sécurisé (32 caractères)
    Format: Alphanumériques + quelques caractères spéciaux sûrs
    """
    # Caractères safe pour PostgreSQL
    chars = string.ascii_letters + string.digits + '-_@#$%'
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_all_secrets():
    """
    Génère tous les secrets nécessaires pour PRESSO
    """
    print("=" * 70)
    print("🔐 PRESSO - GÉNÉRATEUR DE SECRETS SÉCURISÉS")
    print("=" * 70)
    print()
    
    # Django Secret Key
    django_secret = generate_django_secret_key()
    print("📝 DJANGO_SECRET_KEY")
    print("-" * 70)
    print(django_secret)
    print()
    
    # JWT Secret Key
    jwt_secret = generate_jwt_secret_key()
    print("🔑 JWT_SECRET_KEY")
    print("-" * 70)
    print(jwt_secret)
    print()
    
    # DB Password
    db_password = generate_db_password()
    print("🗄️  DB_PASSWORD")
    print("-" * 70)
    print(db_password)
    print()
    
    print("=" * 70)
    print("✅ Secrets générés avec succès !")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT :")
    print("   1. Copiez ces valeurs dans votre fichier .env")
    print("   2. Ne partagez JAMAIS ces secrets")
    print("   3. Ne les commitez JAMAIS sur Git")
    print("   4. Régénérez-les pour chaque environnement (dev, prod)")
    print()
    
    # Format pour copier directement dans .env
    print("📋 FORMAT .ENV (Copier-Coller):")
    print("-" * 70)
    print(f"DJANGO_SECRET_KEY={django_secret}")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print(f"DB_PASSWORD={db_password}")
    print()


if __name__ == "__main__":
    generate_all_secrets()

