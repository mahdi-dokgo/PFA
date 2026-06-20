from django import forms

from apps.articles.models import Article


class StockAdjustmentForm(forms.Form):
    article = forms.ModelChoiceField(
        queryset=Article.objects.order_by('reference'),
        label='Article',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    quantity = forms.IntegerField(
        label='Quantité (positive pour une entrée, négative pour une sortie)',
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    reference = forms.CharField(
        label='Motif',
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity == 0:
            raise forms.ValidationError("La quantité d'ajustement ne peut pas être nulle.")
        return quantity
