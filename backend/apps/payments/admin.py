from django.contrib import admin
from django.utils.html import format_html
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 
        'order_numero', 
        'operateur', 
        'montant', 
        'statut_badge', 
        'date_initiation',
        'date_completion'
    ]
    list_filter = ['statut', 'operateur', 'is_refund', 'date_initiation']
    search_fields = ['reference', 'transaction_id', 'order__numero', 'numero_payeur']
    ordering = ['-date_initiation']
    date_hierarchy = 'date_initiation'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('order', 'reference', 'operateur', 'numero_payeur', 'montant')
        }),
        ('Statut', {
            'fields': ('statut', 'transaction_id', 'error_message')
        }),
        ('Remboursement', {
            'fields': ('is_refund', 'refund_of')
        }),
        ('Métadonnées', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_initiation', 'date_completion', 'created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['reference', 'date_initiation', 'created', 'updated']
    
    def order_numero(self, obj):
        return obj.order.numero
    order_numero.short_description = 'N° Commande'
    
    def statut_badge(self, obj):
        colors = {
            'pending': '#fbbf24',
            'processing': '#60a5fa',
            'completed': '#10b981',
            'failed': '#ef4444',
            'refunded': '#a78bfa',
            'cancelled': '#6b7280',
        }
        color = colors.get(obj.statut, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'
