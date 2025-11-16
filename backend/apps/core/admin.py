from django.contrib import admin
from django.utils.html import format_html
from .models import Permission, Role, ProviderSettings


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'module_badge', 'is_active_icon', 'created']
    list_filter = ['module', 'is_active', 'created']
    search_fields = ['code', 'name', 'description', 'id']
    ordering = ['module', 'code']
    list_per_page = 50
    
    fieldsets = (
        ('Informations', {
            'fields': ('id', 'code', 'name', 'description', 'module', 'is_active')
        }),
        ('Date', {
            'fields': ('created',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['id', 'created']
    
    def module_badge(self, obj):
        colors = {
            'orders': '#3b82f6',
            'services': '#10b981',
            'tariffs': '#f59e0b',
            'stats': '#a78bfa',
            'staff': '#ef4444',
            'settings': '#6b7280',
            'customers': '#14b8a6',
        }
        color = colors.get(obj.module, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_module_display()
        )
    module_badge.short_description = 'Module'
    
    def is_active_icon(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-size: 18px;">✓</span>')
        return format_html('<span style="color: red; font-size: 18px;">✗</span>')
    is_active_icon.short_description = 'Actif'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_name', 'permissions_count', 'is_active_icon', 'created', 'updated']
    list_filter = ['is_active', 'created', 'provider']
    search_fields = ['name', 'description', 'provider__nom_commercial', 'id']
    ordering = ['provider', 'name']
    filter_horizontal = ['permissions']
    list_per_page = 30
    
    fieldsets = (
        ('Informations', {
            'fields': ('id', 'provider', 'name', 'description', 'is_active')
        }),
        ('Permissions', {
            'fields': ('permissions',)
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
    
    def permissions_count(self, obj):
        count = obj.permissions.count()
        if count > 0:
            return format_html('<span style="color: #3b82f6; font-weight: bold;">{}</span>', count)
        return '0'
    permissions_count.short_description = 'Permissions'
    
    def is_active_icon(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-size: 18px;">✓</span>')
        return format_html('<span style="color: red; font-size: 18px;">✗</span>')
    is_active_icon.short_description = 'Actif'


@admin.register(ProviderSettings)
class ProviderSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'business_name',
        'provider_name',
        'auto_accept',
        'require_payment',
        'min_amount',
        'delivery_fee_display',
        'notifications_status',
        'updated'
    ]
    list_filter = [
        'auto_accept_orders',
        'require_payment_before',
        'email_notifications',
        'sms_notifications',
        'created',
        'updated'
    ]
    search_fields = ['business_name', 'provider__nom_commercial', 'notification_email', 'id']
    ordering = ['provider']
    list_per_page = 25
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'provider', 'business_name', 'logo', 'primary_color')
        }),
        ('Configuration opérationnelle', {
            'fields': (
                'auto_accept_orders',
                'require_payment_before',
                'min_order_amount',
                'delivery_fee'
            )
        }),
        ('Notifications', {
            'fields': (
                'email_notifications',
                'sms_notifications',
                'notification_email',
                'notification_phone'
            )
        }),
        ('Horaires & Métadonnées', {
            'fields': ('opening_hours', 'metadata'),
            'classes': ('collapse',)
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
    
    def auto_accept(self, obj):
        if obj.auto_accept_orders:
            return format_html('<span style="color: green;">✓ Oui</span>')
        return format_html('<span style="color: gray;">Non</span>')
    auto_accept.short_description = 'Auto-accept'
    
    def require_payment(self, obj):
        if obj.require_payment_before:
            return format_html('<span style="color: orange;">✓ Oui</span>')
        return format_html('<span style="color: gray;">Non</span>')
    require_payment.short_description = 'Paiement requis'
    
    def min_amount(self, obj):
        if obj.min_order_amount > 0:
            return format_html('<strong>{}</strong> FCFA', obj.min_order_amount)
        return '-'
    min_amount.short_description = 'Montant min.'
    
    def delivery_fee_display(self, obj):
        return format_html('<strong>{}</strong> FCFA', obj.delivery_fee)
    delivery_fee_display.short_description = 'Frais livraison'
    
    def notifications_status(self, obj):
        email_icon = '📧' if obj.email_notifications else ''
        sms_icon = '📱' if obj.sms_notifications else ''
        if email_icon or sms_icon:
            return format_html('{} {}', email_icon, sms_icon)
        return '-'
    notifications_status.short_description = 'Notifications'


