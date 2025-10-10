import uuid
from django.db import models


class Service(models.Model):
    """
    Modèle représentant les types de services proposés
    (Lavage, Repassage, Express, etc.)
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
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['label']
    
    def __str__(self):
        return f"{self.label} ({self.get_mode_tarif_display()})"


class ArticleType(models.Model):
    """
    Types d'articles (chemise, pantalon, robe, etc.)
    Utilisé pour la tarification personnalisée
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
        verbose_name = "Type d'article"
        verbose_name_plural = "Types d'articles"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class Matiere(models.Model):
    """
    Matières des vêtements (coton, soie, laine, etc.)
    Utilisé pour la tarification personnalisée
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
        verbose_name = "Matière"
        verbose_name_plural = "Matières"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom
