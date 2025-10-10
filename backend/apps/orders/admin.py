from django.contrib import admin
from django.utils.html import format_html
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'numero', 
        'client_name', 
        'provider_name', 
        'statut_badge', 
        'total_estime', 
        'creneau_collecte', 
        'created'
    ]
    list_filter = ['statut', 'created', 'creneau_collecte']
    search_fields = ['numero', 'client__username', 'client__phone', 'provider__nom_commercial']
    ordering = ['-created']
    date_hierarchy = 'created'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('numero', 'client', 'provider', 'statut')
        }),
        ('Adresses', {
            'fields': (
                'adresse_collecte', 'latitude_collecte', 'longitude_collecte',
                'adresse_livraison', 'latitude_livraison', 'longitude_livraison'
            )
        }),
        ('Créneaux', {
            'fields': ('creneau_collecte', 'creneau_livraison', 'date_collecte', 'date_livraison')
        }),
        ('Montants', {
            'fields': ('total_estime', 'total_final', 'frais_livraison')
        }),
        ('Notes', {
            'fields': ('notes_client', 'notes_provider')
        }),
        ('Livraison', {
            'fields': ('preuve_livraison_url', 'signature_client')
        }),
        ('Dates', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['numero', 'created', 'updated']
    
    def client_name(self, obj):
        return obj.client.get_full_name() or obj.client.username
    client_name.short_description = 'Client'
    
    def provider_name(self, obj):
        return obj.provider.nom_commercial
    provider_name.short_description = 'Prestataire'
    
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
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'
