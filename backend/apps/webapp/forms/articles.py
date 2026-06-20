from django import forms

from apps.articles.models import Article, Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'name': 'Nom',
            'description': 'Description',
        }


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['reference', 'name', 'unit', 'category', 'min_threshold', 'current_stock', 'safety_stock', 'suppliers']
        widgets = {
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'min_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'safety_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'suppliers': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }
        labels = {
            'reference': 'Référence',
            'name': 'Désignation',
            'unit': 'Unité',
            'category': 'Catégorie',
            'min_threshold': 'Seuil minimal',
            'current_stock': 'Stock actuel',
            'safety_stock': 'Stock de sécurité',
            'suppliers': 'Fournisseurs',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
