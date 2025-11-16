from django.contrib import admin
from django.utils.html import format_html
from .models import OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_ligne', 'created']
    fields = ['article_type', 'matiere', 'service', 'quantite', 'prix_unitaire', 'total_ligne', 'photo', 'notes']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order_numero',
        'article_type',
        'matiere',
        'service',
        'quantite',
        'prix_unitaire',
        'total_ligne_formatted',
        'has_photo',
        'has_notes',
        'created'
    ]
    list_filter = ['article_type', 'matiere', 'service', 'created']
    search_fields = ['order__numero', 'article_type__nom', 'service__label', 'notes', 'id']
    ordering = ['-created']
    date_hierarchy = 'created'
    list_per_page = 50
    
    fieldsets = (
        ('Commande', {
            'fields': ('id', 'order')
        }),
        ('Article', {
            'fields': ('article_type', 'matiere', 'service', 'quantite', 'photo')
        }),
        ('Tarification', {
            'fields': ('prix_unitaire', 'total_ligne')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Date', {
            'fields': ('created',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['id', 'total_ligne', 'created']
    
    def order_numero(self, obj):
        return format_html('<a href="/admin/orders/order/{}/change/">{}</a>', obj.order.id, obj.order.numero)
    order_numero.short_description = 'N° Commande'
    
    def total_ligne_formatted(self, obj):
        return format_html('<strong style="color: #10b981;">{} FCFA</strong>', obj.total_ligne)
    total_ligne_formatted.short_description = 'Total'
    
    def has_photo(self, obj):
        if obj.photo:
            return format_html('<span style="color: green;">📷 Oui</span>')
        return format_html('<span style="color: gray;">Non</span>')
    has_photo.short_description = 'Photo'
    
    def has_notes(self, obj):
        if obj.notes:
            return format_html('<span style="color: orange;">📝</span>')
        return '-'
    has_notes.short_description = 'Notes'
