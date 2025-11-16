from django.contrib import admin
from django.utils.html import format_html
from .models import Order
from apps.order_items.admin import OrderItemInline


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'numero', 
        'client_name', 
        'provider_name', 
        'statut_badge',
        'items_count',
        'total_estime',
        'total_final',
        'frais_livraison',
        'creneau_collecte', 
        'date_collecte',
        'date_livraison',
        'created'
    ]
    list_filter = ['statut', 'created', 'updated', 'creneau_collecte', 'date_collecte', 'date_livraison']
    search_fields = [
        'numero', 
        'id',
        'client__username', 
        'client__phone', 
        'client__email',
        'provider__nom_commercial',
        'adresse_collecte',
        'adresse_livraison'
    ]
    ordering = ['-created']
    date_hierarchy = 'created'
    list_per_page = 25
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'numero', 'client', 'provider', 'statut')
        }),
        ('Adresses de collecte', {
            'fields': ('adresse_collecte', 'latitude_collecte', 'longitude_collecte')
        }),
        ('Adresses de livraison', {
            'fields': ('adresse_livraison', 'latitude_livraison', 'longitude_livraison')
        }),
        ('Créneaux et dates', {
            'fields': (
                'creneau_collecte', 
                'creneau_livraison', 
                'date_collecte', 
                'date_livraison'
            )
        }),
        ('Montants', {
            'fields': ('total_estime', 'total_final', 'frais_livraison')
        }),
        ('Notes', {
            'fields': ('notes_client', 'notes_provider')
        }),
        ('Preuve de livraison', {
            'fields': ('preuve_livraison_url', 'signature_client')
        }),
        ('Dates système', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['id', 'numero', 'created', 'updated']
    
    def client_name(self, obj):
        name = obj.client.get_full_name() or obj.client.username
        return format_html('<strong>{}</strong><br><small>{}</small>', name, obj.client.phone)
    client_name.short_description = 'Client'
    
    def provider_name(self, obj):
        return format_html(
            '<strong>{}</strong><br><small>{}</small>',
            obj.provider.nom_commercial,
            obj.provider.get_type_display()
        )
    provider_name.short_description = 'Prestataire'
    
    def items_count(self, obj):
        count = obj.items.count()
        return format_html('<span style="font-weight: bold; color: #3b82f6;">{}</span>', count)
    items_count.short_description = 'Articles'
    
    def statut_badge(self, obj):
        colors = {
            'pending': '#fbbf24',
            'confirmed': '#60a5fa',
            'collected': '#a78bfa',
            'in_progress': '#34d399',
            'ready': '#10b981',
            'delivered': '#059669',
            'cancelled': '#ef4444',
        }
        color = colors.get(obj.statut, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'
