from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 
        'phone', 
        'email', 
        'get_full_name_display',
        'group_display',
        'role', 
        'is_active',
        'is_staff',
        'is_superuser',
        'date_inscription',
        'last_login'
    ]
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'group', 'date_inscription', 'last_login']
    search_fields = ['username', 'phone', 'email', 'first_name', 'last_name', 'id']
    ordering = ['-date_inscription']
    date_hierarchy = 'date_inscription'
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations Presso', {
            'fields': ('phone', 'photo_profil', 'group', 'role', 'date_inscription', 'id')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations Presso', {
            'fields': ('phone', 'photo_profil', 'group', 'role', 'email')
        }),
    )
    
    readonly_fields = ['date_inscription', 'last_login', 'date_joined', 'id']
    
    def get_full_name_display(self, obj):
        full_name = obj.get_full_name()
        if full_name:
            return format_html('<strong>{}</strong>', full_name)
        return '-'
    get_full_name_display.short_description = 'Nom complet'
    
    def group_display(self, obj):
        if obj.group:
            return format_html(
                '<span style="background-color: #3b82f6; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
                obj.group.name
            )
        return '-'
    group_display.short_description = 'Groupe'
