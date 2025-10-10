from django.contrib import admin
from .models import ProviderService, Tariff


@admin.register(ProviderService)
class ProviderServiceAdmin(admin.ModelAdmin):
    list_display = ['provider', 'service', 'prix_base', 'delai', 'is_available', 'created']
    list_filter = ['is_available', 'created']
    search_fields = ['provider__nom_commercial', 'service__label']
    ordering = ['provider', 'service']
    
    fieldsets = (
        ('Relation', {
            'fields': ('provider', 'service')
        }),
        ('Tarification', {
            'fields': ('prix_base', 'delai', 'is_available')
        }),
        ('Dates', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created', 'updated']


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ['provider', 'article_type', 'matiere', 'service', 'prix', 'created']
    list_filter = ['created']
    search_fields = ['provider__nom_commercial', 'article_type__nom', 'service__label']
    ordering = ['provider', 'article_type', 'service']
    
    fieldsets = (
        ('Relation', {
            'fields': ('provider', 'article_type', 'matiere', 'service')
        }),
        ('Tarification', {
            'fields': ('prix',)
        }),
        ('Dates', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created', 'updated']
