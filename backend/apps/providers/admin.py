from django.contrib import admin
from django.utils.html import format_html
from .models import Provider


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ['nom_commercial', 'type', 'user', 'statut_kyc', 'is_active', 'rayon_km', 'created']
    list_filter = ['type', 'statut_kyc', 'is_active', 'created']
    search_fields = ['nom_commercial', 'user__username', 'user__phone', 'zone_couverture']
    ordering = ['-created']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('user', 'type', 'nom_commercial', 'photo_local')
        }),
        ('Localisation', {
            'fields': ('adresse', 'zone_couverture', 'rayon_km', 'latitude', 'longitude')
        }),
        ('Vérification', {
            'fields': ('statut_kyc', 'document_identite', 'is_active')
        }),
        ('Dates', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created', 'updated']
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Ajouter l'utilisateur au groupe approprié
        if obj.type == 'pressing':
            group_name = 'pressing'
        else:
            group_name = 'fanico'
        
        from django.contrib.auth.models import Group
        group, _ = Group.objects.get_or_create(name=group_name)
        obj.user.groups.add(group)
