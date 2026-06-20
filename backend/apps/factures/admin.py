from django.contrib import admin

from .models import Facture, LigneFacture


class LigneFactureInline(admin.TabularInline):
    model = LigneFacture
    extra = 0
    readonly_fields = ['montant_total']


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ['reference', 'fournisseur', 'bon_commande', 'statut', 'montant_ttc', 'ecart_detected', 'created_at']
    list_filter  = ['statut', 'ecart_detected']
    search_fields = ['reference', 'fournisseur__name']
    inlines      = [LigneFactureInline]
