from django.contrib import admin
from django.utils.html import format_html
from .models import Provider


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = [
        'nom_commercial',
        'type_badge',
        'user_info',
        'statut_kyc_badge',
        'is_active_icon',
        'rayon_km',
        'zone_couverture_short',
        'has_coordinates',
        'created'
    ]
    list_filter = ['type', 'statut_kyc', 'is_active', 'created', 'updated']
    search_fields = ['nom_commercial', 'user__username', 'user__phone', 'user__email', 'zone_couverture', 'adresse', 'id']
    ordering = ['-created']
    date_hierarchy = 'created'
    list_per_page = 25
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'user', 'type', 'nom_commercial', 'photo_local')
        }),
        ('Localisation', {
            'fields': ('adresse', 'quartier', 'zone_couverture', 'rayon_km', 'latitude', 'longitude', 'location')
        }),
        ('Vérification', {
            'fields': ('statut_kyc', 'document_identite', 'is_active')
        }),
        ('Dates', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['id', 'location', 'created', 'updated']
    
    def type_badge(self, obj):
        colors = {
            'pressing': '#10b981',
            'fanico': '#f59e0b',
        }
        color = colors.get(obj.type, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_type_display()
        )
    type_badge.short_description = 'Type'
    
    def user_info(self, obj):
        return f"{obj.user.username} ({obj.user.phone})"
    user_info.short_description = 'Utilisateur'
    
    def statut_kyc_badge(self, obj):
        colors = {
            'pending': '#fbbf24',
            'verified': '#10b981',
            'rejected': '#ef4444',
        }
        color = colors.get(obj.statut_kyc, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_statut_kyc_display()
        )
    statut_kyc_badge.short_description = 'KYC'
    
    def is_active_icon(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-size: 18px;">✓</span>')
        return format_html('<span style="color: red; font-size: 18px;">✗</span>')
    is_active_icon.short_description = 'Actif'
    
    def zone_couverture_short(self, obj):
        if len(obj.zone_couverture) > 50:
            return obj.zone_couverture[:50] + '...'
        return obj.zone_couverture
    zone_couverture_short.short_description = 'Zone'
    
    def has_coordinates(self, obj):
        if obj.latitude and obj.longitude:
            coords_text = f'{obj.latitude:.4f}, {obj.longitude:.4f}'
            if obj.quartier:
                coords_text = f'{obj.quartier}<br>{coords_text}'
            return format_html('📍 <span style="color: green;">{}</span>', coords_text)
        return format_html('<span style="color: red;">Non localisé</span>')
    has_coordinates.short_description = 'Localisation'
    
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
