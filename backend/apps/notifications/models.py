from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    class Type(models.TextChoices):
        STOCK_CRITIQUE = 'STOCK_CRITIQUE', 'Stock critique'
        DA_EN_ATTENTE  = 'DA_EN_ATTENTE',  'DA en attente'
        FACTURE_ECART  = 'FACTURE_ECART',  'Facture avec écart'
        BC_NON_RECU    = 'BC_NON_RECU',    'BC non réceptionné'
        INFO           = 'INFO',           'Information'

    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type        = models.CharField(max_length=20, choices=Type.choices, default=Type.INFO)
    titre       = models.CharField(max_length=100)
    message     = models.TextField()
    url         = models.CharField(max_length=300, blank=True)
    lu          = models.BooleanField(default=False)   # vue/lue → retire le highlight
    resolue     = models.BooleanField(default=False)   # problème résolu → retire du dropdown
    resolue_at  = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.type}] {self.titre} → {self.user}'

    def resolve(self):
        self.resolue    = True
        self.resolue_at = timezone.now()
        self.save(update_fields=['resolue', 'resolue_at'])

    @classmethod
    def create(cls, user, type, titre, message, url=''):
        return cls.objects.create(
            user=user, type=type,
            titre=titre, message=message, url=url,
        )
