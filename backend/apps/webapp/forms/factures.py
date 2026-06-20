from django import forms
from django.forms import modelformset_factory

from apps.factures.models import Facture, LigneFacture
from apps.orders.models import PurchaseOrder
from apps.suppliers.models import Supplier


class FactureForm(forms.ModelForm):
    class Meta:
        model  = Facture
        fields = ['fournisseur', 'bon_commande', 'date_facture', 'date_echeance',
                  'montant_ht', 'montant_ttc', 'commentaire']
        widgets = {
            'fournisseur':   forms.Select(attrs={'class': 'form-select'}),
            'bon_commande':  forms.Select(attrs={'class': 'form-select', 'id': 'id_bon_commande'}),
            'date_facture':  forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_echeance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'montant_ht':    forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'id': 'id_montant_ht'}),
            'montant_ttc':   forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'id': 'id_montant_ttc'}),
            'commentaire':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'fournisseur':   'Fournisseur',
            'bon_commande':  'Bon de commande lié (optionnel)',
            'date_facture':  'Date de la facture',
            'date_echeance': "Date d'échéance",
            'montant_ht':    'Montant HT (DH)',
            'montant_ttc':   'Montant TTC (DH)',
            'commentaire':   'Commentaire (optionnel)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bon_commande'].required = False
        self.fields['bon_commande'].empty_label = '— Aucun —'
        self.fields['bon_commande'].queryset = (
            PurchaseOrder.objects
            .exclude(status='ANNULEE')
            .select_related('supplier')
            .order_by('-created_at')
        )
        self.fields['commentaire'].required = False
        self.fields['fournisseur'].queryset = (
            Supplier.objects.filter(status='active').order_by('name')
        )


class LigneFactureForm(forms.ModelForm):
    class Meta:
        model  = LigneFacture
        fields = ['designation', 'quantite', 'prix_unitaire']
        widgets = {
            'designation':   forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Désignation de l\'article',
            }),
            'quantite':      forms.NumberInput(attrs={
                'class': 'form-control ligne-qte', 'min': 1, 'placeholder': 'Qté',
            }),
            'prix_unitaire': forms.NumberInput(attrs={
                'class': 'form-control ligne-prix', 'step': '0.01', 'min': '0', 'placeholder': '0.00',
            }),
        }
        labels = {
            'designation':   'Désignation',
            'quantite':      'Qté',
            'prix_unitaire': 'Prix unitaire (DH)',
        }


LigneFactureFormSet = modelformset_factory(
    LigneFacture,
    form=LigneFactureForm,
    extra=2,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class FactureRejeterForm(forms.Form):
    commentaire = forms.CharField(
        label='Motif du rejet',
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                     'placeholder': 'Décrivez le motif du rejet...'}),
    )
