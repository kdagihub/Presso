import uuid
from django.db import models
from apps.providers.models import Provider
from apps.services.models import Service, ArticleType, Matiere


class ProviderService(models.Model):
    """
    Relation entre un prestataire et les services qu'il propose
    avec tarifs et délais personnalisés
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='provider_services',
        verbose_name="Prestataire"
    )
    
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='providers',
        verbose_name="Service"
    )
    
    prix_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix de base (FCFA)",
        help_text="Prix selon le mode de tarification du service"
    )
    
    delai = models.PositiveIntegerField(
        verbose_name="Délai (heures)",
        help_text="Temps de réalisation promis par le prestataire"
    )
    
    is_available = models.BooleanField(
        default=True,
        verbose_name="Disponible",
        help_text="Le prestataire propose actuellement ce service"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Service du prestataire"
        verbose_name_plural = "Services des prestataires"
        unique_together = ['provider', 'service']
        ordering = ['provider', 'service']
    
    def __str__(self):
        return f"{self.provider.nom_commercial} - {self.service.label} ({self.prix_base} FCFA)"


class Tariff(models.Model):
    """
    Tarification personnalisée par prestataire
    Permet de définir des prix spécifiques par type d'article + matière + service
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name='tariffs',
        verbose_name="Prestataire"
    )
    
    article_type = models.ForeignKey(
        ArticleType,
        on_delete=models.CASCADE,
        related_name='tariffs',
        verbose_name="Type d'article"
    )
    
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.CASCADE,
        related_name='tariffs',
        verbose_name="Matière",
        blank=True,
        null=True,
        help_text="Laisser vide pour appliquer à toutes les matières"
    )
    
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='tariffs',
        verbose_name="Service"
    )
    
    prix = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix (FCFA)"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Tarif personnalisé"
        verbose_name_plural = "Tarifs personnalisés"
        unique_together = ['provider', 'article_type', 'matiere', 'service']
        ordering = ['provider', 'article_type', 'service']
    
    def __str__(self):
        matiere_str = f" - {self.matiere.nom}" if self.matiere else ""
        return f"{self.article_type.nom}{matiere_str} - {self.service.label}: {self.prix} FCFA"
