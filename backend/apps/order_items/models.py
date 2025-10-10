import uuid
from django.db import models
from apps.orders.models import Order
from apps.services.models import Service, ArticleType, Matiere


class OrderItem(models.Model):
    """
    Ligne de commande - représente un article dans une commande
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Commande"
    )
    
    article_type = models.ForeignKey(
        ArticleType,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name="Type d'article"
    )
    
    matiere = models.ForeignKey(
        Matiere,
        on_delete=models.PROTECT,
        related_name='order_items',
        blank=True,
        null=True,
        verbose_name="Matière"
    )
    
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name="Service"
    )
    
    quantite = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=1.00,
        verbose_name="Quantité",
        help_text="Nombre de pièces ou poids en kg selon le service"
    )
    
    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Prix unitaire (FCFA)"
    )
    
    total_ligne = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total ligne (FCFA)"
    )
    
    photo = models.ImageField(
        upload_to='order_items/photos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Photo de l'article",
        help_text="Photo facultative du vêtement"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="État, taches particulières, etc."
    )
    
    created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"
        ordering = ['order', 'created']
    
    def __str__(self):
        return f"{self.article_type.nom} - {self.service.label} (x{self.quantite})"
    
    def save(self, *args, **kwargs):
        # Calculer automatiquement le total de la ligne
        self.total_ligne = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)
        
        # Mettre à jour le total de la commande
        self.order.total_estime = sum(
            item.total_ligne for item in self.order.items.all()
        )
        self.order.save(update_fields=['total_estime'])
