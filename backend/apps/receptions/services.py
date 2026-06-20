"""Logique métier partagée pour les réceptions (Reception).

Utilisé à la fois par l'API DRF (apps.receptions.views) et par le
frontend Django classique (apps.webapp.views.receptions).
"""
from django.db import transaction
from django.db.models import Q, Sum

from apps.orders.models import PurchaseOrder
from apps.stock.models import StockMovement

from .models import Reception, ReceptionLine


def create_reception_with_lines(*, po, receiver, receiver_name, notes, lines_data):
    with transaction.atomic():
        reception = Reception.objects.create(
            po=po,
            receiver=receiver,
            receiver_name=receiver_name,
            notes=notes,
        )

        for line in lines_data:
            po_line = line['po_line']
            article = line['article']
            received_quantity = line['received_quantity']

            ReceptionLine.objects.create(
                reception=reception,
                po_line=po_line,
                article=article,
                ordered_quantity=line['ordered_quantity'],
                received_quantity=received_quantity,
            )

            po_line.received_quantity += received_quantity
            po_line.save()

            article.current_stock += received_quantity
            article.save()

            StockMovement.objects.create(
                article=article,
                movement_type=StockMovement.Type.IN,
                quantity=received_quantity,
                reference=reception.code,
            )

        all_lines = po.lines.all()
        all_done = all(ln.received_quantity >= ln.quantity for ln in all_lines)
        any_received = any(ln.received_quantity > 0 for ln in all_lines)
        if all_done:
            po.status = PurchaseOrder.Status.RECUE
        elif any_received:
            po.status = PurchaseOrder.Status.PARTIELLEMENT_RECUE
        po.save()

    return reception


def compute_reception_line_gap(line):
    """Quantité qui reste à recevoir sur la ligne de BC après cette réception.

    Tient compte des réceptions précédentes sur la même ligne : 0 signifie
    que cette réception a comblé tout ce qui restait à recevoir au moment où
    elle a été enregistrée.
    """
    earlier_received = ReceptionLine.objects.filter(
        po_line_id=line.po_line_id,
    ).exclude(pk=line.pk).filter(
        Q(reception__received_at__lt=line.reception.received_at)
        | Q(reception__received_at=line.reception.received_at, reception__pk__lt=line.reception_id)
    ).aggregate(total=Sum('received_quantity'))['total'] or 0

    remaining_before = line.ordered_quantity - earlier_received
    return max(remaining_before - line.received_quantity, 0)
