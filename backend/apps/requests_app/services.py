"""Logique métier partagée pour les demandes d'achat (PurchaseRequest).

Utilisé à la fois par l'API DRF (apps.requests_app.views) et par le
frontend Django classique (apps.webapp.views.purchase_requests).
"""
from apps.audit.utils import log_action
from .models import AuditEntry, PurchaseRequest


def add_audit_entry(purchase_request, user, action, comment=''):
    return AuditEntry.objects.create(
        request=purchase_request,
        actor=user,
        actor_name=user.full_name,
        action=action,
        comment=comment or '',
    )


def submit_purchase_request(purchase_request, user):
    purchase_request.status = PurchaseRequest.Status.SOUMISE
    purchase_request.save()
    add_audit_entry(purchase_request, user, 'Soumission')
    log_action('DA', purchase_request.code, 'Soumission', user=user)
    return purchase_request


def approve_purchase_request(purchase_request, user, comment=''):
    purchase_request.status = PurchaseRequest.Status.VALIDEE
    purchase_request.comment = comment
    purchase_request.save()
    add_audit_entry(purchase_request, user, 'Validation', comment)
    log_action('DA', purchase_request.code, 'Validation', user=user, detail=comment)
    return purchase_request


def reject_purchase_request(purchase_request, user, comment=''):
    purchase_request.status = PurchaseRequest.Status.REJETEE
    purchase_request.comment = comment
    purchase_request.save()
    add_audit_entry(purchase_request, user, 'Rejet', comment)
    log_action('DA', purchase_request.code, 'Rejet', user=user, detail=comment)
    return purchase_request
