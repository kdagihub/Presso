from django.contrib import admin
from django.utils.html import format_html
from .models import ProviderService, Tariff


@admin.register(ProviderService)
class ProviderServiceAdmin(admin.ModelAdmin):
    list_display = [
        'provider_name',
        'service_name',
        'prix_base_formatted',
        'delai_formatted',
        'is_available_icon',
        'created',
        'updated'
    ]
    list_filter = ['is_available', 'created', 'updated', 'service']
    search_fields = [
        'provider__nom_commercial',
        'service__label',
        'provider__user__username',
        'id'
    ]
    ordering = ['provider', 'service']
    list_per_page = 30
    
    fieldsets = (
        ('Relation', {
            'fields': ('id', 'provider', 'service')
        }),
        ('Tarification', {
            'fields': ('prix_base', 'delai', 'is_available')
        }),
        ('Dates', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['id', 'created', 'updated']
    
    def provider_name(self, obj):
        return format_html(
            '<strong>{}</strong><br><small style="color: gray;">{}</small>',
            obj.provider.nom_commercial,
            obj.provider.get_type_display()
        )
    provider_name.short_description = 'Prestataire'
    
    def service_name(self, obj):
        return format_html(
            '<strong>{}</strong><br><small style="color: gray;">{}</small>',
            obj.service.label,
            obj.service.get_mode_tarif_display()
        )
    service_name.short_description = 'Service'
    
    def prix_base_formatted(self, obj):
        return format_html('<strong style="color: #10b981; font-size: 13px;">{} FCFA</strong>', obj.prix_base)
    prix_base_formatted.short_description = 'Prix'
    
    def delai_formatted(self, obj):
        return format_html('<strong>{}</strong> heures', obj.delai)
    delai_formatted.short_description = 'Délai'
    
    def is_available_icon(self, obj):
        if obj.is_available:
            return format_html('<span style="color: green; font-size: 18px;">✓</span>')
        return format_html('<span style="color: red; font-size: 18px;">✗</span>')
    is_available_icon.short_description = 'Disponible'


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = [
        'provider_name',
        'article_type',
        'matiere',
        'service_name',
        'prix_formatted',
        'created',
        'updated'
    ]
    list_filter = ['created', 'updated', 'article_type', 'matiere', 'service']
    search_fields = [
        'provider__nom_commercial',
        'article_type__nom',
        'matiere__nom',
        'service__label',
        'id'
    ]
    ordering = ['provider', 'article_type', 'service']
    list_per_page = 40
    
    fieldsets = (
        ('Relation', {
            'fields': ('id', 'provider', 'article_type', 'matiere', 'service')
        }),
        ('Tarification', {
            'fields': ('prix',)
        }),
        ('Dates', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['id', 'created', 'updated']
    
    def provider_name(self, obj):
        return format_html('<strong>{}</strong>', obj.provider.nom_commercial)
    provider_name.short_description = 'Prestataire'
    
    def service_name(self, obj):
        return obj.service.label
    service_name.short_description = 'Service'
    
    def prix_formatted(self, obj):
        return format_html('<strong style="color: #10b981; font-size: 13px;">{} FCFA</strong>', obj.prix)
    prix_formatted.short_description = 'Prix'
