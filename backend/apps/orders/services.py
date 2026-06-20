"""Logique métier partagée pour les bons de commande (PurchaseOrder).

Utilisé à la fois par l'API DRF (apps.orders.views/serializers) et par le
frontend Django classique (apps.webapp.views.orders).
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.requests_app.models import PurchaseRequest

from .models import POLine, PurchaseOrder


def create_purchase_order_with_lines(*, supplier, expected_date, total_amount, lines_data, request=None):
    if request is not None and request.status != PurchaseRequest.Status.VALIDEE:
        raise ValidationError(
            "Seule une demande au statut « Validée » peut être convertie en bon de commande."
        )
    with transaction.atomic():
        po = PurchaseOrder.objects.create(
            supplier=supplier,
            request=request,
            expected_date=expected_date,
            total_amount=total_amount,
        )
        for line in lines_data:
            POLine.objects.create(order=po, **line)
        if request is not None:
            request.status = PurchaseRequest.Status.CONVERTIE
            request.save()
    return po


def transition_purchase_order(purchase_order, new_status):
    purchase_order.status = new_status
    purchase_order.save()
    return purchase_order
