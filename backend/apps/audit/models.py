from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Module(models.TextChoices):
        DA        = 'DA',        "Demande d'achat"
        BC        = 'BC',        'Bon de commande'
        RECEPTION = 'RECEPTION', 'Réception'
        FACTURE   = 'FACTURE',   'Facture'
        STOCK     = 'STOCK',     'Stock'
        USER      = 'USER',      'Utilisateur'

    module      = models.CharField(max_length=15, choices=Module.choices)
    object_ref  = models.CharField(max_length=50)
    action      = models.CharField(max_length=100)
    detail      = models.TextField(blank=True)
    actor       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs',
    )
    actor_name  = models.CharField(max_length=150, blank=True)
    at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-at']

    def __str__(self):
        return f'[{self.module}] {self.object_ref} — {self.action}'
