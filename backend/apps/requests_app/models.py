from django.db import models, transaction
from django.conf import settings
from apps.articles.models import Article


class PurchaseRequest(models.Model):
    class Status(models.TextChoices):
        BROUILLON = 'BROUILLON', 'Brouillon'
        SOUMISE = 'SOUMISE', 'Soumise'
        VALIDEE = 'VALIDEE', 'Validée'
        REJETEE = 'REJETEE', 'Rejetée'
        CONVERTIE = 'CONVERTIE', 'Convertie'

    class Priority(models.TextChoices):
        LOW = 'low', 'Faible'
        MEDIUM = 'medium', 'Moyenne'
        URGENT = 'urgent', 'Urgente'

    code = models.CharField(max_length=30, unique=True, blank=True)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='requests')
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.BROUILLON)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.code:
            from django.utils import timezone
            year = timezone.now().year
            with transaction.atomic():
                # Lock existing rows for this year to serialize concurrent inserts
                last = (
                    PurchaseRequest.objects
                    .select_for_update()
                    .filter(code__startswith=f'DA-{year}-')
                    .order_by('code')
                    .last()
                )
                count = (int(last.code.split('-')[-1]) + 1) if last else 1
                self.code = f'DA-{year}-{str(count).zfill(3)}'
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class RequestLine(models.Model):
    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='lines')
    article = models.ForeignKey(Article, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    justification = models.TextField(blank=True)


class AuditEntry(models.Model):
    request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='audit')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    actor_name = models.CharField(max_length=150)
    action = models.CharField(max_length=100)
    comment = models.TextField(blank=True)
    at = models.DateTimeField(auto_now_add=True)
