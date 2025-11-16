from django.db import models
from contextvars import ContextVar

# Context variable pour stocker le tenant actuel
_current_tenant = ContextVar('current_tenant', default=None)


def get_current_tenant():
    """Récupère le tenant actuel du contexte"""
    return _current_tenant.get()


def set_current_tenant(tenant):
    """Définit le tenant actuel dans le contexte"""
    _current_tenant.set(tenant)


def clear_current_tenant():
    """Efface le tenant du contexte"""
    _current_tenant.set(None)


class TenantManager(models.Manager):
    """
    Manager personnalisé pour filtrer automatiquement par tenant
    Utilise le contexte (ContextVar) pour déterminer le tenant actuel
    """
    
    def get_queryset(self):
        """Filtre automatiquement le queryset par tenant si disponible"""
        qs = super().get_queryset()
        tenant = get_current_tenant()
        
        if tenant:
            return qs.filter(provider=tenant)
        
        # Si pas de tenant, retourne tout (pour admin global)
        return qs
    
    def for_tenant(self, tenant):
        """Méthode explicite pour filtrer par tenant spécifique"""
        return super().get_queryset().filter(provider=tenant)
    
    def all_tenants(self):
        """Retourne tous les objets sans filtre tenant (pour admin)"""
        return super().get_queryset()


class TenantQuerySet(models.QuerySet):
    """
    QuerySet personnalisé avec méthodes tenant-aware
    """
    
    def for_tenant(self, tenant):
        """Filtre par tenant"""
        return self.filter(provider=tenant)
    
    def active(self):
        """Filtre les objets actifs"""
        return self.filter(is_active=True)


class TenantManagerWithQuerySet(models.Manager):
    """
    Manager qui combine TenantManager et TenantQuerySet
    """
    
    def get_queryset(self):
        qs = TenantQuerySet(self.model, using=self._db)
        tenant = get_current_tenant()
        
        if tenant:
            return qs.filter(provider=tenant)
        
        return qs
    
    def for_tenant(self, tenant):
        return self.get_queryset().for_tenant(tenant)
    
    def all_tenants(self):
        return TenantQuerySet(self.model, using=self._db)

