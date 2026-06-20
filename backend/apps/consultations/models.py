from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from apps.requests_app.models import PurchaseRequest
from apps.suppliers.models import Supplier


class Consultation(models.Model):
    class Statut(models.TextChoices):
        OUVERTE  = 'OUVERTE',  'Ouverte'
        CLOTUREE = 'CLOTUREE', 'Clôturée'
        ANNULEE  = 'ANNULEE',  'Annulée'

    code          = models.CharField(max_length=30, unique=True, blank=True)
    titre         = models.CharField(max_length=200)
    description   = models.TextField(blank=True)
    date_limite   = models.DateField()
    statut        = models.CharField(max_length=10, choices=Statut.choices, default=Statut.OUVERTE)
    demande_achat = models.ForeignKey(
        PurchaseRequest, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='consultations',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='consultations_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.code:
            year = timezone.now().year
            with transaction.atomic():
                last = (
                    Consultation.objects
                    .select_for_update()
                    .filter(code__startswith=f'CON-{year}-')
                    .order_by('code')
                    .last()
                )
                count = (int(last.code.split('-')[-1]) + 1) if last else 1
                self.code = f'CON-{year}-{str(count).zfill(3)}'
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class ConsultationFournisseur(models.Model):
    class Statut(models.TextChoices):
        INVITE            = 'INVITE',            'Invité'
        PROPOSITION_RECUE = 'PROPOSITION_RECUE', 'Proposition reçue'
        RETENU            = 'RETENU',            'Retenu'
        ELIMINE           = 'ELIMINE',           'Éliminé'

    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, related_name='fournisseurs',
    )
    fournisseur = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name='consultations_fournisseur',
    )
    statut = models.CharField(
        max_length=20, choices=Statut.choices, default=Statut.INVITE,
    )

    class Meta:
        unique_together = ('consultation', 'fournisseur')

    def __str__(self):
        return f'{self.consultation.code} — {self.fournisseur.name}'


class Proposition(models.Model):
    consultation_fournisseur = models.OneToOneField(
        ConsultationFournisseur, on_delete=models.CASCADE, related_name='proposition',
    )
    prix_unitaire    = models.DecimalField(max_digits=14, decimal_places=2)
    delai_livraison  = models.PositiveIntegerField(help_text='Délai en jours')
    commentaire      = models.TextField(blank=True)
    date_reception   = models.DateTimeField(auto_now_add=True)
    retenue          = models.BooleanField(default=False)

    def __str__(self):
        return f'Proposition {self.consultation_fournisseur}'
