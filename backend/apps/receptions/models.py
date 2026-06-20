from django.db import models, transaction
from apps.orders.models import PurchaseOrder, POLine
from apps.articles.models import Article
from django.conf import settings


class Reception(models.Model):
    code = models.CharField(max_length=30, unique=True, blank=True)
    po = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name='receptions')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    receiver_name = models.CharField(max_length=150)
    notes = models.TextField(blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.code:
            from django.utils import timezone
            year = timezone.now().year
            with transaction.atomic():
                last = (
                    Reception.objects
                    .select_for_update()
                    .filter(code__startswith=f'REC-{year}-')
                    .order_by('code')
                    .last()
                )
                count = (int(last.code.split('-')[-1]) + 1) if last else 1
                self.code = f'REC-{year}-{str(count).zfill(3)}'
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


class ReceptionLine(models.Model):
    reception = models.ForeignKey(Reception, on_delete=models.CASCADE, related_name='lines')
    po_line = models.ForeignKey(POLine, on_delete=models.PROTECT)
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    ordered_quantity = models.PositiveIntegerField()
    received_quantity = models.PositiveIntegerField()
