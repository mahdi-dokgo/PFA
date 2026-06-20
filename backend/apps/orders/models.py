from django.db import models, transaction
from apps.suppliers.models import Supplier
from apps.articles.models import Article
from apps.requests_app.models import PurchaseRequest


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        BROUILLON = 'BROUILLON', 'Brouillon'
        APPROUVEE = 'APPROUVEE', 'Approuvée'
        ENVOYEE = 'ENVOYEE', 'Envoyée'
        PARTIELLEMENT_RECUE = 'PARTIELLEMENT_RECUE', 'Partiellement reçue'
        RECUE = 'RECUE', 'Reçue'
        CLOTUREE = 'CLOTUREE', 'Clôturée'
        ANNULEE = 'ANNULEE', 'Annulée'

    code = models.CharField(max_length=30, unique=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    request = models.ForeignKey(PurchaseRequest, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.BROUILLON)
    expected_date = models.DateField()
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            from django.utils import timezone
            year = timezone.now().year
            with transaction.atomic():
                last = (
                    PurchaseOrder.objects
                    .select_for_update()
                    .filter(code__startswith=f'BC-{year}-')
                    .order_by('code')
                    .last()
                )
                count = (int(last.code.split('-')[-1]) + 1) if last else 1
                self.code = f'BC-{year}-{str(count).zfill(3)}'
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class POLine(models.Model):
    order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    received_quantity = models.PositiveIntegerField(default=0)
