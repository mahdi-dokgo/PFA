from django import forms

from apps.orders.models import PurchaseOrder

RECEIVABLE_STATUSES = [
    PurchaseOrder.Status.APPROUVEE,
    PurchaseOrder.Status.ENVOYEE,
    PurchaseOrder.Status.PARTIELLEMENT_RECUE,
]


class ReceptionPOSelectForm(forms.Form):
    po = forms.ModelChoiceField(
        queryset=PurchaseOrder.objects.filter(status__in=RECEIVABLE_STATUSES).select_related('supplier'),
        label='Bon de commande',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


class ReceptionNotesForm(forms.Form):
    notes = forms.CharField(
        label='Notes',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    )


class ReceptionLineForm(forms.Form):
    po_line_id = forms.IntegerField(widget=forms.HiddenInput())
    remaining_quantity = forms.IntegerField(widget=forms.HiddenInput())
    received_quantity = forms.IntegerField(
        label='Quantité reçue',
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
    )

    def clean(self):
        cleaned_data = super().clean()
        received = cleaned_data.get('received_quantity') or 0
        remaining = cleaned_data.get('remaining_quantity') or 0
        if received > remaining:
            raise forms.ValidationError(
                f"La quantité reçue ne peut pas dépasser la quantité restante ({remaining})."
            )
        return cleaned_data


ReceptionLineFormSet = forms.formset_factory(ReceptionLineForm, extra=0)
