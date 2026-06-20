from django.db import models
from apps.suppliers.models import Supplier


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Article(models.Model):
    reference = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=50)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='articles')
    min_threshold = models.PositiveIntegerField(default=0)
    current_stock = models.IntegerField(default=0)
    safety_stock = models.IntegerField(default=0)
    suppliers = models.ManyToManyField(Supplier, blank=True, related_name='articles')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.reference} – {self.name}'
