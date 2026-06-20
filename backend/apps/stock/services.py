"""Logique métier partagée pour les mouvements de stock (StockMovement).

Utilisé par le frontend Django classique (apps.webapp.views.stock) pour les
ajustements manuels de stock (entrées/sorties hors réception).
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import StockMovement


def create_stock_adjustment(*, article, quantity, reference=''):
    if article.current_stock + quantity < 0:
        raise ValidationError(
            f"Stock insuffisant : le stock actuel de « {article.reference} » est de "
            f"{article.current_stock}, cet ajustement le rendrait négatif."
        )

    with transaction.atomic():
        article.current_stock += quantity
        article.save()
        movement = StockMovement.objects.create(
            article=article,
            movement_type=StockMovement.Type.ADJUST,
            quantity=quantity,
            reference=reference,
        )

    return movement
