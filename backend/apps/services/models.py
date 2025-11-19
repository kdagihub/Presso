import uuid
from django.db import models  # type: ignore
from django.db.models import Q  # type: ignore
from django.utils import timezone  # type: ignore

from apps.core.managers import TenantManagerWithQuerySet


class ServiceTemplate(models.Model):
    """
    Templates de services créés par la plateforme
    Servent de base pour que les prestataires créent leurs services personnalisés
    """
    MODE_TARIF_CHOICES = [
        ('kg', 'Au kilogramme'),
        ('piece', 'Par pièce'),
        ('forfait', 'Forfait'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    label = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Libellé du service"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    mode_tarif = models.CharField(
        max_length=20,
        choices=MODE_TARIF_CHOICES,
        verbose_name="Mode de tarification"
    )
    
    duree_estimee = models.PositiveIntegerField(
        verbose_name="Durée estimée (minutes)",
        help_text="Temps moyen de réalisation"
    )
    
    icone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Icône",
        help_text="Nom de l'icône (ex: iron, washing-machine)"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    class Meta:
        verbose_name = "Template de service"
        verbose_name_plural = "Templates de services"
        ordering = ['label']
    
    def __str__(self):
        return f"{self.label} (Template)"


class Service(models.Model):
    """
    Services personnalisés par prestataire
    Chaque prestataire peut créer ses propres services ou utiliser des templates
    """
    MODE_TARIF_CHOICES = [
        ('kg', 'Au kilogramme'),
        ('piece', 'Par pièce'),
        ('forfait', 'Forfait'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='services',
        verbose_name="Prestataire"
    )
    
    template = models.ForeignKey(
        ServiceTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instances',
        verbose_name="Basé sur le template",
        help_text="Template utilisé comme base (optionnel)"
    )
    
    label = models.CharField(
        max_length=100,
        verbose_name="Libellé du service"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    mode_tarif = models.CharField(
        max_length=20,
        choices=MODE_TARIF_CHOICES,
        verbose_name="Mode de tarification"
    )
    
    duree_estimee = models.PositiveIntegerField(
        verbose_name="Durée estimée (minutes)",
        help_text="Temps moyen de réalisation"
    )
    
    icone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Icône",
        help_text="Nom de l'icône (ex: iron, washing-machine)"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    # Managers
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Supprimé",
        help_text="Indique si le service a été supprimé (soft delete)"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Supprimé le"
    )

    class ServiceManager(TenantManagerWithQuerySet):
        def get_queryset(self):
            return super().get_queryset().filter(is_deleted=False)

    objects = ServiceManager()
    all_objects = models.Manager()  # Pour admin global
    
    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['provider', 'label']
        indexes = [
            models.Index(fields=['provider', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'label'],
                condition=Q(is_deleted=False),
                name='unique_service_label_per_provider_active',
            ),
        ]
    
    def __str__(self):
        return f"{self.provider.nom_commercial} - {self.label}"

    def soft_delete(self):
        if not self.is_deleted:
            self.is_deleted = True
            self.is_active = False
            self.deleted_at = timezone.now()
            self.save(update_fields=['is_deleted', 'is_active', 'deleted_at'])


class ArticleTypeTemplate(models.Model):
    """
    Templates de types d'articles créés par la plateforme
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    nom = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom de l'article"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Template de type d'article"
        verbose_name_plural = "Templates de types d'articles"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} (Template)"


class ArticleType(models.Model):
    """
    Types d'articles personnalisés par prestataire
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='article_types',
        verbose_name="Prestataire"
    )
    
    template = models.ForeignKey(
        ArticleTypeTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instances',
        verbose_name="Basé sur le template"
    )
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom de l'article"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    # Managers
    objects = TenantManagerWithQuerySet()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = "Type d'article"
        verbose_name_plural = "Types d'articles"
        unique_together = ['provider', 'nom']
        ordering = ['provider', 'nom']
        indexes = [
            models.Index(fields=['provider']),
        ]
    
    def __str__(self):
        return f"{self.provider.nom_commercial} - {self.nom}"


class MatiereTemplate(models.Model):
    """
    Templates de matières créés par la plateforme
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    nom = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom de la matière"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Template de matière"
        verbose_name_plural = "Templates de matières"
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} (Template)"


class Matiere(models.Model):
    """
    Matières personnalisées par prestataire
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    provider = models.ForeignKey(
        'providers.Provider',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='matieres',
        verbose_name="Prestataire"
    )
    
    template = models.ForeignKey(
        MatiereTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instances',
        verbose_name="Basé sur le template"
    )
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom de la matière"
    )
    
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    # Managers
    objects = TenantManagerWithQuerySet()
    all_objects = models.Manager()
    
    class Meta:
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        unique_together = ['provider', 'nom']
        ordering = ['provider', 'nom']
        indexes = [
            models.Index(fields=['provider']),
        ]
    
    def __str__(self):
        return f"{self.provider.nom_commercial} - {self.nom}"
