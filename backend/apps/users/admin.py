from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'phone', 'email', 'get_full_name', 'group', 'role', 'is_active', 'date_inscription']
    list_filter = ['is_active', 'is_staff', 'group', 'date_inscription']
    search_fields = ['username', 'phone', 'email', 'first_name', 'last_name']
    ordering = ['-date_inscription']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations Presso', {
            'fields': ('phone', 'photo_profil', 'group', 'role', 'date_inscription')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations Presso', {
            'fields': ('phone', 'photo_profil', 'group', 'role')
        }),
    )
    
    readonly_fields = ['date_inscription']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or '-'
    get_full_name.short_description = 'Nom complet'
