from .managers import set_current_tenant, clear_current_tenant


class TenantMiddleware:
    """
    Middleware pour gérer le contexte du tenant actuel
    Identifie automatiquement le prestataire et le met dans le contexte
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Identifier le tenant
        tenant = None
        
        if request.user.is_authenticated:
            # Si l'utilisateur a un profil prestataire
            if hasattr(request.user, 'provider_profile'):
                tenant = request.user.provider_profile
            
            # Si l'utilisateur appartient à un prestataire via son groupe/rôle
            elif hasattr(request.user, 'custom_role') and request.user.custom_role:
                tenant = request.user.custom_role.provider
        
        # Stocker le tenant dans le contexte
        if tenant:
            set_current_tenant(tenant)
            request.tenant = tenant
        else:
            clear_current_tenant()
            request.tenant = None
        
        # Traiter la requête
        response = self.get_response(request)
        
        # Nettoyer le contexte après la requête
        clear_current_tenant()
        
        return response
    
    def process_exception(self, request, exception):
        """Nettoyer le contexte en cas d'exception"""
        clear_current_tenant()
        return None

