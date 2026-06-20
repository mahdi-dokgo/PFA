from django import forms
from django.forms import inlineformset_factory

from apps.orders.models import POLine, PurchaseOrder
from apps.requests_app.models import PurchaseRequest


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['supplier', 'request', 'expected_date']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'request': forms.Select(attrs={'class': 'form-select'}),
            'expected_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
        labels = {
            'supplier': 'Fournisseur',
            'request': "Demande d'achat liée",
            'expected_date': 'Date de livraison prévue',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['request'].queryset = PurchaseRequest.objects.filter(
            status=PurchaseRequest.Status.VALIDEE
        )
        self.fields['request'].required = False


class POLineForm(forms.ModelForm):
    class Meta:
        model = POLine
        fields = ['article', 'quantity', 'unit_price']
        widgets = {
            'article': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': '0.01'}),
        }
        labels = {
            'article': 'Article',
            'quantity': 'Quantité',
            'unit_price': 'Prix unitaire',
        }


POLineFormSet = inlineformset_factory(
    PurchaseOrder,
    POLine,
    form=POLineForm,
    extra=8,
    can_delete=False,
    min_num=1,
    validate_min=True,
)


class POStatusTransitionForm(forms.Form):
    status = forms.ChoiceField(
        label='Nouveau statut',
        choices=PurchaseOrder.Status.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
