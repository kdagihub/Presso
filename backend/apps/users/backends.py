"""
Backend d'authentification personnalisé pour Presso
Permet la connexion avec username, email ou numéro de téléphone
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailPhoneUsernameBackend(ModelBackend):
    """
    Backend d'authentification personnalisé qui permet de se connecter avec :
    - username
    - email
    - numéro de téléphone
    
    Utilisé automatiquement par Django lors de l'appel à authenticate()
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authentifier un utilisateur avec username, email ou téléphone
        
        Args:
            request: Requête HTTP
            username: Peut être un username, email ou téléphone
            password: Mot de passe
        
        Returns:
            User object si authentification réussie, None sinon
        """
        if username is None or password is None:
            return None
        
        try:
            # Chercher l'utilisateur par username, email ou téléphone
            # Normaliser le téléphone si nécessaire
            phone = self._normalize_phone(username)
            
            user = User.objects.filter(
                Q(username__iexact=username) |
                Q(email__iexact=username) |
                Q(phone=phone)
            ).first()
            
            # Vérifier le mot de passe
            if user and user.check_password(password):
                return user
            
        except User.DoesNotExist:
            # Exécuter le hash de password par défaut pour éviter timing attacks
            User().set_password(password)
            return None
        
        return None
    
    def _normalize_phone(self, value):
        """
        Normaliser un numéro de téléphone au format international
        
        Args:
            value: Numéro potentiel (peut être email/username)
        
        Returns:
            Numéro formaté ou valeur d'origine
        """
        # Si la valeur ne ressemble pas à un numéro, la retourner telle quelle
        if '@' in value or not any(char.isdigit() for char in value):
            return value
        
        # Retirer les espaces et caractères spéciaux
        phone = ''.join(char for char in value if char.isdigit() or char == '+')
        
        # Si commence par 0, remplacer par +225 (Côte d'Ivoire)
        if phone.startswith('0'):
            phone = '+225' + phone[1:]
        
        # Si pas de +, ajouter +225
        elif not phone.startswith('+'):
            phone = '+225' + phone
        
        return phone
    
    def get_user(self, user_id):
        """
        Récupérer un utilisateur par son ID
        Méthode requise par le backend
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

