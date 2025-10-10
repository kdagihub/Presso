from django.contrib import admin
from .models import Service, ArticleType, Matiere


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['label', 'mode_tarif', 'duree_estimee', 'is_active', 'created']
    list_filter = ['mode_tarif', 'is_active', 'created']
    search_fields = ['label', 'description']
    ordering = ['label']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('label', 'description', 'icone', 'is_active')
        }),
        ('Tarification', {
            'fields': ('mode_tarif', 'duree_estimee')
        }),
        ('Dates', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created', 'updated']


@admin.register(ArticleType)
class ArticleTypeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'created']
    search_fields = ['nom', 'description']
    ordering = ['nom']
    readonly_fields = ['created']


@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ['nom', 'created']
    search_fields = ['nom', 'description']
    ordering = ['nom']
    readonly_fields = ['created']
