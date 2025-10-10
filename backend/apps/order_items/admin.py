from django.contrib import admin
from .models import OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_ligne', 'created']
    fields = ['article_type', 'matiere', 'service', 'quantite', 'prix_unitaire', 'total_ligne', 'photo']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'article_type', 'matiere', 'service', 'quantite', 'prix_unitaire', 'total_ligne', 'created']
    list_filter = ['article_type', 'service', 'created']
    search_fields = ['order__numero', 'article_type__nom', 'notes']
    ordering = ['-created']
    
    fieldsets = (
        ('Commande', {
            'fields': ('order',)
        }),
        ('Article', {
            'fields': ('article_type', 'matiere', 'service', 'quantite', 'photo')
        }),
        ('Tarification', {
            'fields': ('prix_unitaire', 'total_ligne')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Date', {
            'fields': ('created',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['total_ligne', 'created']
