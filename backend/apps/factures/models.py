from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from apps.orders.models import PurchaseOrder
from apps.suppliers.models import Supplier


class Facture(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        VALIDEE    = 'VALIDEE',    'Validée'
        PAYEE      = 'PAYEE',      'Payée'
        REJETEE    = 'REJETEE',    'Rejetée'

    reference     = models.CharField(max_length=30, unique=True, blank=True)
    bon_commande  = models.ForeignKey(
        PurchaseOrder, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='factures',
    )
    fournisseur   = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name='factures',
    )
    date_facture  = models.DateField()
    date_echeance = models.DateField()
    montant_ht    = models.DecimalField(max_digits=14, decimal_places=2)
    montant_ttc   = models.DecimalField(max_digits=14, decimal_places=2)
    statut        = models.CharField(
        max_length=10, choices=Statut.choices, default=Statut.EN_ATTENTE,
    )
    commentaire   = models.TextField(blank=True)
    ecart_detected = models.BooleanField(default=False)
    created_by    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='factures_created',
    )
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.reference

    def _compute_ecart(self):
        if not self.bon_commande_id or not self.montant_ttc:
            return False
        try:
            bc_amount = PurchaseOrder.objects.values_list(
                'total_amount', flat=True
            ).get(pk=self.bon_commande_id)
            if bc_amount and bc_amount > 0:
                diff_pct = abs(float(self.montant_ttc) - float(bc_amount)) / float(bc_amount) * 100
                return diff_pct > 1
        except PurchaseOrder.DoesNotExist:
            pass
        return False

    def save(self, *args, **kwargs):
        self.ecart_detected = self._compute_ecart()
        if not self.reference:
            year = timezone.now().year
            with transaction.atomic():
                last = (
                    Facture.objects
                    .select_for_update()
                    .filter(reference__startswith=f'FAC-{year}-')
                    .order_by('reference')
                    .last()
                )
                count = (int(last.reference.split('-')[-1]) + 1) if last else 1
                self.reference = f'FAC-{year}-{str(count).zfill(3)}'
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


class LigneFacture(models.Model):
    facture       = models.ForeignKey(
        Facture, on_delete=models.CASCADE, related_name='lignes',
    )
    designation   = models.CharField(max_length=300)
    quantite      = models.PositiveIntegerField()
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2)
    montant_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.montant_total = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.facture.reference} — {self.designation}'
