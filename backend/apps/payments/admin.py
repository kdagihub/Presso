from django.contrib import admin
from django.utils.html import format_html
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 
        'order_numero', 
        'operateur_badge',
        'numero_payeur',
        'montant_formatted', 
        'statut_badge',
        'is_refund_icon',
        'transaction_id_short',
        'date_initiation',
        'date_completion',
        'duration'
    ]
    list_filter = ['statut', 'operateur', 'is_refund', 'date_initiation', 'date_completion']
    search_fields = [
        'reference', 
        'transaction_id', 
        'order__numero', 
        'numero_payeur',
        'id'
    ]
    ordering = ['-date_initiation']
    date_hierarchy = 'date_initiation'
    list_per_page = 30
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'order', 'reference', 'operateur', 'numero_payeur', 'montant')
        }),
        ('Statut de transaction', {
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
    
    readonly_fields = ['id', 'reference', 'date_initiation', 'created', 'updated']
    
    def order_numero(self, obj):
        return format_html('<a href="/admin/orders/order/{}/change/">{}</a>', obj.order.id, obj.order.numero)
    order_numero.short_description = 'N° Commande'
    
    def operateur_badge(self, obj):
        colors = {
            'orange': '#ff6600',
            'mtn': '#ffcc00',
            'moov': '#009900',
            'wave': '#4169e1',
        }
        color = colors.get(obj.operateur, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_operateur_display()
        )
    operateur_badge.short_description = 'Opérateur'
    
    def montant_formatted(self, obj):
        return format_html('<strong style="color: #10b981; font-size: 13px;">{} FCFA</strong>', obj.montant)
    montant_formatted.short_description = 'Montant'
    
    def is_refund_icon(self, obj):
        if obj.is_refund:
            return format_html('<span style="color: orange; font-size: 16px;">↩️</span>')
        return '-'
    is_refund_icon.short_description = 'Rembours.'
    
    def transaction_id_short(self, obj):
        if obj.transaction_id:
            if len(obj.transaction_id) > 20:
                return obj.transaction_id[:20] + '...'
            return obj.transaction_id
        return '-'
    transaction_id_short.short_description = 'Transaction ID'
    
    def duration(self, obj):
        if obj.date_completion and obj.date_initiation:
            delta = obj.date_completion - obj.date_initiation
            minutes = int(delta.total_seconds() / 60)
            if minutes < 1:
                return '< 1 min'
            elif minutes < 60:
                return f'{minutes} min'
            else:
                hours = minutes // 60
                return f'{hours}h {minutes % 60}min'
        return '-'
    duration.short_description = 'Durée'
    
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
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_statut_display()
        )
    statut_badge.short_description = 'Statut'
