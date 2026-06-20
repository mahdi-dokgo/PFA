from django import forms
from django.forms import inlineformset_factory

from apps.requests_app.models import PurchaseRequest, RequestLine


class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['priority']
        widgets = {
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'priority': 'Priorité',
        }


class RequestLineForm(forms.ModelForm):
    class Meta:
        model = RequestLine
        fields = ['article', 'quantity', 'justification']
        widgets = {
            'article': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'justification': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'article': 'Article',
            'quantity': 'Quantité',
            'justification': 'Justification',
        }


RequestLineFormSet = inlineformset_factory(
    PurchaseRequest,
    RequestLine,
    form=RequestLineForm,
    extra=5,
    can_delete=False,
    min_num=1,
    validate_min=True,
)


class ApprovalCommentForm(forms.Form):
    comment = forms.CharField(
        label='Commentaire',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    )
