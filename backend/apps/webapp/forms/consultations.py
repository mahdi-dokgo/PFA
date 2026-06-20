from django import forms

from apps.consultations.models import Consultation, Proposition
from apps.requests_app.models import PurchaseRequest


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['titre', 'description', 'date_limite', 'demande_achat']
        widgets = {
            'titre':         forms.TextInput(attrs={'class': 'form-control'}),
            'description':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_limite':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'demande_achat': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'titre':         'Titre',
            'description':   'Description',
            'date_limite':   'Date limite',
            'demande_achat': "Demande d'achat liée (optionnelle)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['demande_achat'].required = False
        self.fields['demande_achat'].queryset = (
            PurchaseRequest.objects.filter(status='CONVERTIE').order_by('-created_at')
        )
        self.fields['demande_achat'].empty_label = '— Aucune —'


class PropositionForm(forms.ModelForm):
    class Meta:
        model = Proposition
        fields = ['prix_unitaire', 'delai_livraison', 'commentaire']
        widgets = {
            'prix_unitaire':   forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'delai_livraison': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'commentaire':     forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'prix_unitaire':   'Prix unitaire (DH)',
            'delai_livraison': 'Délai de livraison (jours)',
            'commentaire':     'Commentaire',
        }
