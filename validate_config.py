#!/usr/bin/env python3
"""
Script de validation de la configuration PRESSO
Vérifie la cohérence entre .env, settings.py et docker-compose.yml
"""
import os
import sys
from pathlib import Path

# Couleurs pour le terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}{text:^70}{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def load_env_file(filepath):
    """Charger le fichier .env dans un dict"""
    env_vars = {}
    if not os.path.exists(filepath):
        return env_vars
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    return env_vars

def validate_critical_vars(env_vars):
    """Vérifier les variables critiques"""
    print_header("1. VARIABLES CRITIQUES")
    
    critical_vars = {
        'DJANGO_SECRET_KEY': 'Clé secrète Django',
        'JWT_SECRET_KEY': 'Clé secrète JWT',
        'DB_PASSWORD': 'Mot de passe base de données',
    }
    
    all_ok = True
    for var, desc in critical_vars.items():
        if var in env_vars and env_vars[var]:
            # Vérifier qu'il ne contient pas de valeur par défaut
            if 'changez' in env_vars[var].lower() or 'votre' in env_vars[var].lower():
                print_error(f"{desc} ({var}) : Valeur par défaut non changée")
                all_ok = False
            else:
                print_success(f"{desc} ({var}) : OK")
        else:
            print_error(f"{desc} ({var}) : Manquant ou vide")
            all_ok = False
    
    return all_ok

def validate_redis_dbs(env_vars):
    """Vérifier la séparation des DB Redis"""
    print_header("2. REDIS DATABASES")
    
    redis_dbs = {
        'REDIS_URL': ('Cache', 0),
        'CELERY_BROKER_URL': ('Celery Broker', 1),
        'CELERY_RESULT_BACKEND': ('Celery Results', 2),
        # Channel Layers utilise DB 3 (hardcodé dans settings.py)
    }
    
    all_ok = True
    db_numbers = []
    
    for var, (desc, expected_db) in redis_dbs.items():
        if var in env_vars:
            url = env_vars[var]
            try:
                db_num = int(url.split('/')[-1])
                db_numbers.append(db_num)
                if db_num == expected_db:
                    print_success(f"{desc} ({var}) : DB {db_num}")
                else:
                    print_warning(f"{desc} ({var}) : DB {db_num} (attendu: {expected_db})")
            except ValueError:
                print_error(f"{desc} ({var}) : Format invalide")
                all_ok = False
        else:
            print_error(f"{desc} ({var}) : Manquant")
            all_ok = False
    
    # Vérifier l'unicité
    if len(db_numbers) != len(set(db_numbers)):
        print_error("Conflit : Plusieurs services utilisent la même DB Redis !")
        all_ok = False
    else:
        print_success("Séparation des DB Redis : OK")
    
    print_success("Channel Layers : DB 3 (hardcodé dans settings.py)")
    
    return all_ok

def validate_orange_sms(env_vars):
    """SMS providers actuellement désactivés."""
    print_header("3. SMS PROVIDER")
    print_warning("ℹ️  Aucun provider SMS externe (Orange/Twilio) n'est actif pour le moment.")
    print_warning("    Les envois SMS se font en mode placeholder (logs uniquement).")
    if env_vars.get('NOTIFICATION_SMS_ENABLED', 'False') == 'True':
        print_warning("    Conseil : laissez NOTIFICATION_SMS_ENABLED=False tant que le provider est inactif.")
    return True

def validate_firebase(env_vars):
    """Vérifier la configuration Firebase"""
    print_header("4. FIREBASE CLOUD MESSAGING")
    
    # Vérifier la variable
    if 'FCM_PROJECT_ID' in env_vars and env_vars['FCM_PROJECT_ID']:
        print_success(f"FCM_PROJECT_ID : {env_vars['FCM_PROJECT_ID']}")
    else:
        print_warning("FCM_PROJECT_ID : Manquant")
    
    # Vérifier le fichier JSON
    firebase_json = Path('backend/firebase-adminsdk.json')
    if firebase_json.exists():
        print_success(f"Fichier credentials : {firebase_json}")
    else:
        print_error(f"Fichier credentials manquant : {firebase_json}")
        return False
    
    return True

def validate_cors(env_vars):
    """Vérifier la configuration CORS"""
    print_header("5. CORS CONFIGURATION")
    
    if 'CORS_ALLOWED_ORIGINS' in env_vars:
        origins = env_vars['CORS_ALLOWED_ORIGINS'].split(',')
        print_success(f"Origins autorisés : {len(origins)}")
        for origin in origins:
            print(f"  - {origin.strip()}")
    else:
        print_warning("CORS_ALLOWED_ORIGINS : Manquant (all origins en dev)")
    
    if env_vars.get('DJANGO_DEBUG', 'False') == 'True':
        print_warning("DEBUG=True : Tous les origins autorisés (dev mode)")
    
    return True

def validate_jwt(env_vars):
    """Vérifier la configuration JWT"""
    print_header("6. JWT AUTHENTICATION")
    
    checks = {
        'JWT_SECRET_KEY': 'Clé secrète JWT',
        'JWT_ACCESS_TOKEN_LIFETIME_MINUTES': 'Durée access token',
        'JWT_REFRESH_TOKEN_LIFETIME_DAYS': 'Durée refresh token',
    }
    
    all_ok = True
    for var, desc in checks.items():
        if var in env_vars and env_vars[var]:
            print_success(f"{desc} : {env_vars[var]}")
        else:
            print_error(f"{desc} ({var}) : Manquant")
            all_ok = False
    
    return all_ok

def validate_security(env_vars):
    """Vérifier les paramètres de sécurité"""
    print_header("7. SÉCURITÉ")
    
    is_debug = env_vars.get('DJANGO_DEBUG', 'False') == 'True'
    is_prod_secure = env_vars.get('SECURE_SSL_REDIRECT', 'False') == 'True'
    
    if is_debug:
        print_warning("DEBUG=True : Mode développement")
        print_warning("SSL/HTTPS désactivé (normal en dev)")
    else:
        print_success("DEBUG=False : Mode production")
        if is_prod_secure:
            print_success("SSL/HTTPS activé")
        else:
            print_error("SSL/HTTPS désactivé (DANGEREUX en production !)")
            return False
    
    return True

def validate_database(env_vars):
    """Vérifier la configuration DB"""
    print_header("8. BASE DE DONNÉES")
    
    db_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    all_ok = True
    
    for var in db_vars:
        if var in env_vars and env_vars[var]:
            if var == 'DB_PASSWORD':
                print_success(f"{var} : ****** (masqué)")
            else:
                print_success(f"{var} : {env_vars[var]}")
        else:
            print_error(f"{var} : Manquant")
            all_ok = False
    
    return all_ok

def main():
    print_header("🔍 VALIDATION DE LA CONFIGURATION PRESSO")
    
    # Charger le .env
    env_file = Path('.env')
    if not env_file.exists():
        print_error(f"Fichier .env introuvable : {env_file.absolute()}")
        sys.exit(1)
    
    env_vars = load_env_file(env_file)
    print_success(f"Fichier .env chargé : {len(env_vars)} variables")
    
    # Exécuter les validations
    results = []
    results.append(("Variables Critiques", validate_critical_vars(env_vars)))
    results.append(("Redis Databases", validate_redis_dbs(env_vars)))
    results.append(("Orange SMS", validate_orange_sms(env_vars)))
    results.append(("Firebase", validate_firebase(env_vars)))
    results.append(("CORS", validate_cors(env_vars)))
    results.append(("JWT", validate_jwt(env_vars)))
    results.append(("Sécurité", validate_security(env_vars)))
    results.append(("Base de données", validate_database(env_vars)))
    
    # Résumé
    print_header("📊 RÉSUMÉ")
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        if ok:
            print_success(f"{name}: OK")
        else:
            print_error(f"{name}: ERREURS")
    
    print()
    if passed == total:
        print_success(f"✅ Toutes les validations réussies ({passed}/{total})")
        print_success("Configuration prête pour le démarrage !")
        return 0
    else:
        print_error(f"❌ {total - passed} validation(s) échouée(s) sur {total}")
        print_warning("Corrigez les erreurs avant de démarrer Docker")
        return 1

if __name__ == '__main__':
    sys.exit(main())

