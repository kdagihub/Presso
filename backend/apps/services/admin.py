from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ServiceTemplate, Service,
    ArticleTypeTemplate, ArticleType,
    MatiereTemplate, Matiere
)


# ==================== TEMPLATES (Globaux) ====================

@admin.register(ServiceTemplate)
class ServiceTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'label',
        'mode_tarif_badge',
        'duree_estimee_formatted',
        'icone_display',
        'is_active_icon',
        'instances_count',
        'created',
        'updated'
    ]
    list_filter = ['mode_tarif', 'is_active', 'created', 'updated']
    search_fields = ['label', 'description', 'icone', 'id']
    ordering = ['label']
    list_per_page = 25
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'label', 'description', 'icone', 'is_active')
        }),
        ('Tarification', {
            'fields': ('mode_tarif', 'duree_estimee')
        }),
        ('Dates', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['id', 'created', 'updated']
    
    def mode_tarif_badge(self, obj):
        colors = {
            'kg': '#3b82f6',
            'piece': '#10b981',
            'forfait': '#f59e0b',
        }
        color = colors.get(obj.mode_tarif, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_mode_tarif_display()
        )
    mode_tarif_badge.short_description = 'Mode tarif'
    
    def duree_estimee_formatted(self, obj):
        hours = obj.duree_estimee // 60
        minutes = obj.duree_estimee % 60
        if hours > 0:
            return format_html('<strong>{}h {}</strong>min', hours, minutes if minutes > 0 else '00')
        return format_html('<strong>{}</strong> min', minutes)
    duree_estimee_formatted.short_description = 'Durée'
    
    def icone_display(self, obj):
        if obj.icone:
            return format_html('<span style="color: #3b82f6;">🎨 {}</span>', obj.icone)
        return '-'
    icone_display.short_description = 'Icône'
    
    def is_active_icon(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-size: 18px;">✓</span>')
        return format_html('<span style="color: red; font-size: 18px;">✗</span>')
    is_active_icon.short_description = 'Actif'
    
    def instances_count(self, obj):
        count = obj.instances.count()
        if count > 0:
            return format_html('<span style="color: #10b981; font-weight: bold;">{}</span>', count)
        return '0'
    instances_count.short_description = 'Instances'


# ==================== INSTANCES (Par prestataire) ====================

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'label',
        'provider_name',
        'template_link',
        'mode_tarif_badge',
        'duree_estimee_formatted',
        'icone_display',
        'is_active_icon',
        'created',
        'updated'
    ]
    list_filter = ['mode_tarif', 'is_active', 'created', 'provider', 'template']
    search_fields = ['label', 'description', 'provider__nom_commercial', 'id']
    ordering = ['provider', 'label']
    list_per_page = 30
    
    fieldsets = (
        ('Prestataire', {
            'fields': ('id', 'provider', 'template')
        }),
        ('Informations', {
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
    
    readonly_fields = ['id', 'created', 'updated']
    
    def provider_name(self, obj):
        return format_html('<strong>{}</strong>', obj.provider.nom_commercial)
    provider_name.short_description = 'Prestataire'
    
    def template_link(self, obj):
        if obj.template:
            return format_html('<span style="color: #3b82f6;">📋 {}</span>', obj.template.label)
        return format_html('<span style="color: gray;">Personnalisé</span>')
    template_link.short_description = 'Template'
    
    def mode_tarif_badge(self, obj):
        colors = {'kg': '#3b82f6', 'piece': '#10b981', 'forfait': '#f59e0b'}
        color = colors.get(obj.mode_tarif, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_mode_tarif_display()
        )
    mode_tarif_badge.short_description = 'Mode'
    
    def duree_estimee_formatted(self, obj):
        hours, minutes = divmod(obj.duree_estimee, 60)
        if hours > 0:
            return format_html('<strong>{}h {}</strong>min', hours, minutes if minutes > 0 else '00')
        return format_html('<strong>{}</strong> min', minutes)
    duree_estimee_formatted.short_description = 'Durée'
    
    def icone_display(self, obj):
        if obj.icone:
            return format_html('<span style="color: #3b82f6;">{}</span>', obj.icone)
        return '-'
    icone_display.short_description = 'Icône'
    
    def is_active_icon(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-size: 18px;">✓</span>')
        return format_html('<span style="color: red; font-size: 18px;">✗</span>')
    is_active_icon.short_description = 'Actif'


# ==================== ARTICLE TEMPLATES ====================

@admin.register(ArticleTypeTemplate)
class ArticleTypeTemplateAdmin(admin.ModelAdmin):
    list_display = ['nom', 'description_short', 'instances_count', 'created']
    search_fields = ['nom', 'description', 'id']
    ordering = ['nom']
    list_per_page = 50
    readonly_fields = ['id', 'created']
    
    fieldsets = (
        ('Informations', {
            'fields': ('id', 'nom', 'description')
        }),
        ('Date', {
            'fields': ('created',),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        if obj.description and len(obj.description) > 60:
            return obj.description[:60] + '...'
        return obj.description or '-'
    description_short.short_description = 'Description'
    
    def instances_count(self, obj):
        count = obj.instances.count()
        return format_html('<span style="color: #10b981; font-weight: bold;">{}</span>', count) if count > 0 else '0'
    instances_count.short_description = 'Instances'


@admin.register(ArticleType)
class ArticleTypeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'provider_name', 'template_link', 'usage_count', 'created']
    list_filter = ['provider', 'template']
    search_fields = ['nom', 'description', 'provider__nom_commercial', 'id']
    ordering = ['provider', 'nom']
    list_per_page = 50
    readonly_fields = ['id', 'created']
    
    fieldsets = (
        ('Prestataire', {
            'fields': ('id', 'provider', 'template')
        }),
        ('Informations', {
            'fields': ('nom', 'description')
        }),
        ('Date', {
            'fields': ('created',),
            'classes': ('collapse',)
        }),
    )
    
    def provider_name(self, obj):
        return format_html('<strong>{}</strong>', obj.provider.nom_commercial)
    provider_name.short_description = 'Prestataire'
    
    def template_link(self, obj):
        if obj.template:
            return format_html('<span style="color: #3b82f6;">📋 {}</span>', obj.template.nom)
        return format_html('<span style="color: gray;">Personnalisé</span>')
    template_link.short_description = 'Template'
    
    def usage_count(self, obj):
        count = obj.order_items.count()
        return format_html('<span style="color: #10b981; font-weight: bold;">{}</span>', count) if count > 0 else '-'
    usage_count.short_description = 'Utilisations'


# ==================== MATIERE TEMPLATES ====================

@admin.register(MatiereTemplate)
class MatiereTemplateAdmin(admin.ModelAdmin):
    list_display = ['nom', 'description_short', 'instances_count', 'created']
    search_fields = ['nom', 'description', 'id']
    ordering = ['nom']
    list_per_page = 50
    readonly_fields = ['id', 'created']
    
    fieldsets = (
        ('Informations', {
            'fields': ('id', 'nom', 'description')
        }),
        ('Date', {
            'fields': ('created',),
            'classes': ('collapse',)
        }),
    )
    
    def description_short(self, obj):
        if obj.description and len(obj.description) > 60:
            return obj.description[:60] + '...'
        return obj.description or '-'
    description_short.short_description = 'Description'
    
    def instances_count(self, obj):
        count = obj.instances.count()
        return format_html('<span style="color: #10b981; font-weight: bold;">{}</span>', count) if count > 0 else '0'
    instances_count.short_description = 'Instances'


@admin.register(Matiere)
class MatiereAdmin(admin.ModelAdmin):
    list_display = ['nom', 'provider_name', 'template_link', 'usage_count', 'created']
    list_filter = ['provider', 'template']
    search_fields = ['nom', 'description', 'provider__nom_commercial', 'id']
    ordering = ['provider', 'nom']
    list_per_page = 50
    readonly_fields = ['id', 'created']
    
    fieldsets = (
        ('Prestataire', {
            'fields': ('id', 'provider', 'template')
        }),
        ('Informations', {
            'fields': ('nom', 'description')
        }),
        ('Date', {
            'fields': ('created',),
            'classes': ('collapse',)
        }),
    )
    
    def provider_name(self, obj):
        return format_html('<strong>{}</strong>', obj.provider.nom_commercial)
    provider_name.short_description = 'Prestataire'
    
    def template_link(self, obj):
        if obj.template:
            return format_html('<span style="color: #3b82f6;">📋 {}</span>', obj.template.nom)
        return format_html('<span style="color: gray;">Personnalisé</span>')
    template_link.short_description = 'Template'
    
    def usage_count(self, obj):
        count = obj.order_items.count()
        return format_html('<span style="color: #10b981; font-weight: bold;">{}</span>', count) if count > 0 else '-'
    usage_count.short_description = 'Utilisations'
