from django.db import models
from apps.articles.models import Article


class StockMovement(models.Model):
    class Type(models.TextChoices):
        IN = 'IN', 'Entrée'
        OUT = 'OUT', 'Sortie'
        ADJUST = 'ADJUST', 'Ajustement'

    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=10, choices=Type.choices)
    quantity = models.IntegerField()
    reference = models.CharField(max_length=50, blank=True)
    at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-at']
