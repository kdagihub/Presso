from django.contrib import admin
from django.utils.html import format_html
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'client_name', 
        'provider_name', 
        'note_stars', 
        'order_numero',
        'is_approved', 
        'is_flagged',
        'created'
    ]
    list_filter = ['note', 'is_approved', 'is_flagged', 'created']
    search_fields = ['client__username', 'provider__nom_commercial', 'commentaire', 'order__numero']
    ordering = ['-created']
    date_hierarchy = 'created'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('client', 'provider', 'order')
        }),
        ('Évaluation', {
            'fields': ('note', 'note_qualite', 'note_delai', 'note_service', 'commentaire')
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
    
    readonly_fields = ['created', 'updated', 'date_reponse']
    
    def client_name(self, obj):
        return obj.client.get_full_name() or obj.client.username
    client_name.short_description = 'Client'
    
    def provider_name(self, obj):
        return obj.provider.nom_commercial
    provider_name.short_description = 'Prestataire'
    
    def order_numero(self, obj):
        return obj.order.numero
    order_numero.short_description = 'N° Commande'
    
    def note_stars(self, obj):
        stars = '⭐' * obj.note
        return format_html('<span style="font-size: 16px;">{}</span>', stars)
    note_stars.short_description = 'Note'
    
    actions = ['approve_reviews', 'flag_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True, is_flagged=False)
    approve_reviews.short_description = "Approuver les avis sélectionnés"
    
    def flag_reviews(self, request, queryset):
        queryset.update(is_flagged=True)
    flag_reviews.short_description = "Signaler les avis sélectionnés"
