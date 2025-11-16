from django.contrib import admin
from django.utils.html import format_html
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'client_name', 
        'provider_name', 
        'order_numero',
        'note_stars',
        'note_qualite_display',
        'note_delai_display',
        'note_service_display',
        'has_comment',
        'moderation_status',
        'has_response',
        'created'
    ]
    list_filter = [
        'note', 
        'note_qualite',
        'note_delai',
        'note_service',
        'is_approved', 
        'is_flagged', 
        'created',
        'provider'
    ]
    search_fields = [
        'client__username', 
        'client__phone',
        'provider__nom_commercial', 
        'commentaire', 
        'reponse_provider',
        'order__numero',
        'id'
    ]
    ordering = ['-created']
    date_hierarchy = 'created'
    list_per_page = 30
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'client', 'provider', 'order')
        }),
        ('Évaluation globale', {
            'fields': ('note', 'commentaire')
        }),
        ('Évaluation détaillée', {
            'fields': ('note_qualite', 'note_delai', 'note_service')
        }),
        ('Modération', {
            'fields': ('is_approved', 'is_flagged')
        }),
        ('Réponse du prestataire', {
            'fields': ('reponse_provider', 'date_reponse')
        }),
        ('Dates', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['id', 'created', 'updated', 'date_reponse']
    
    def client_name(self, obj):
        name = obj.client.get_full_name() or obj.client.username
        return format_html('<strong>{}</strong><br><small>{}</small>', name, obj.client.phone)
    client_name.short_description = 'Client'
    
    def provider_name(self, obj):
        return format_html('<strong>{}</strong>', obj.provider.nom_commercial)
    provider_name.short_description = 'Prestataire'
    
    def order_numero(self, obj):
        return format_html('<a href="/admin/orders/order/{}/change/">{}</a>', obj.order.id, obj.order.numero)
    order_numero.short_description = 'N° Commande'
    
    def note_stars(self, obj):
        stars = '⭐' * obj.note
        return format_html('<span style="font-size: 16px;">{}</span>', stars)
    note_stars.short_description = 'Note globale'
    
    def note_qualite_display(self, obj):
        if obj.note_qualite:
            stars = '⭐' * obj.note_qualite
            return format_html('<span style="font-size: 12px;">{}</span>', stars)
        return '-'
    note_qualite_display.short_description = 'Qualité'
    
    def note_delai_display(self, obj):
        if obj.note_delai:
            stars = '⭐' * obj.note_delai
            return format_html('<span style="font-size: 12px;">{}</span>', stars)
        return '-'
    note_delai_display.short_description = 'Délai'
    
    def note_service_display(self, obj):
        if obj.note_service:
            stars = '⭐' * obj.note_service
            return format_html('<span style="font-size: 12px;">{}</span>', stars)
        return '-'
    note_service_display.short_description = 'Service'
    
    def has_comment(self, obj):
        if obj.commentaire:
            return format_html('<span style="color: green;">📝 Oui</span>')
        return '-'
    has_comment.short_description = 'Commentaire'
    
    def moderation_status(self, obj):
        if obj.is_flagged:
            return format_html('<span style="background-color: #ef4444; color: white; padding: 2px 8px; border-radius: 3px;">🚩 Signalé</span>')
        elif obj.is_approved:
            return format_html('<span style="background-color: #10b981; color: white; padding: 2px 8px; border-radius: 3px;">✓ Approuvé</span>')
        else:
            return format_html('<span style="background-color: #fbbf24; color: white; padding: 2px 8px; border-radius: 3px;">⏳ En attente</span>')
    moderation_status.short_description = 'Modération'
    
    def has_response(self, obj):
        if obj.reponse_provider:
            return format_html('<span style="color: green;">💬 Oui</span>')
        return '-'
    has_response.short_description = 'Réponse'
    
    actions = ['approve_reviews', 'flag_reviews', 'unflag_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True, is_flagged=False)
        self.message_user(request, f'{updated} avis approuvé(s).')
    approve_reviews.short_description = "✓ Approuver les avis sélectionnés"
    
    def flag_reviews(self, request, queryset):
        updated = queryset.update(is_flagged=True)
        self.message_user(request, f'{updated} avis signalé(s).')
    flag_reviews.short_description = "🚩 Signaler les avis sélectionnés"
    
    def unflag_reviews(self, request, queryset):
        updated = queryset.update(is_flagged=False)
        self.message_user(request, f'{updated} avis dé-signalé(s).')
    unflag_reviews.short_description = "✓ Retirer le signalement"
