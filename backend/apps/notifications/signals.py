from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.articles.models import Article
from apps.factures.models import Facture
from apps.orders.models import PurchaseOrder
from apps.requests_app.models import PurchaseRequest
from apps.stock.models import StockMovement


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _notify_users(roles, type_, titre, message, url):
    from apps.users.models import User
    from .models import Notification

    for user in User.objects.filter(role__in=roles, is_active=True):
        if not Notification.objects.filter(
            user=user, type=type_, titre=titre, resolue=False
        ).exists():
            Notification.create(user=user, type=type_, titre=titre, message=message, url=url)


def _resolve_notifications(type_, titre_contains):
    from .models import Notification

    Notification.objects.filter(
        type=type_, titre__contains=titre_contains, resolue=False
    ).update(resolue=True, resolue_at=timezone.now())


# ──────────────────────────────────────────────
# Stock critique
# ──────────────────────────────────────────────

def _check_stock(article):
    if article.min_threshold > 0 and article.current_stock <= article.min_threshold:
        _notify_users(
            roles=['MAGASINIER', 'ADMIN'],
            type_='STOCK_CRITIQUE',
            titre=f"Stock critique : {article.name}",
            message=(
                f"La quantité de {article.name} est de {article.current_stock}"
                f" (seuil min : {article.min_threshold})"
            ),
            url='/stock/?alert=1',
        )
    else:
        # Stock replenished — resolve any open critical notifications for this article
        _resolve_notifications('STOCK_CRITIQUE', article.name)


@receiver(post_save, sender=Article)
def on_article_save(sender, instance, **kwargs):
    if kwargs.get('raw'):
        return
    _check_stock(instance)


@receiver(post_save, sender=StockMovement)
def on_stock_movement_save(sender, instance, **kwargs):
    if kwargs.get('raw'):
        return
    # Force a fresh DB read — instance.article may be a cached pre-update object
    article = Article.objects.get(pk=instance.article_id)
    _check_stock(article)


# ──────────────────────────────────────────────
# Demandes d'achat
# ──────────────────────────────────────────────

@receiver(post_save, sender=PurchaseRequest)
def on_da_save(sender, instance, **kwargs):
    if kwargs.get('raw'):
        return

    if instance.status == 'SOUMISE':
        requester_name = instance.requester.full_name if instance.requester else '—'
        _notify_users(
            roles=['VALIDATEUR', 'ADMIN'],
            type_='DA_EN_ATTENTE',
            titre=f"Nouvelle DA à valider : {instance.code}",
            message=f"{requester_name} a soumis une demande d'achat.",
            url=f'/demandes/{instance.pk}/',
        )

    elif instance.status in ('VALIDEE', 'REJETEE'):
        # DA processed — resolve its pending validation notification
        _resolve_notifications('DA_EN_ATTENTE', instance.code)


# ──────────────────────────────────────────────
# Factures avec écart
# ──────────────────────────────────────────────

@receiver(post_save, sender=Facture)
def on_facture_save(sender, instance, **kwargs):
    if kwargs.get('raw'):
        return

    if instance.ecart_detected:
        bc_montant = (
            f"{instance.bon_commande.total_amount:.2f}"
            if instance.bon_commande else '—'
        )
        _notify_users(
            roles=['ADMIN', 'ACHETEUR'],
            type_='FACTURE_ECART',
            titre=f"⚠️ Écart facture : {instance.reference}",
            message=f"Écart entre BC ({bc_montant} DH) et facture ({instance.montant_ttc:.2f} DH).",
            url=f'/factures/{instance.pk}/',
        )
    else:
        # Écart corrected or facture rejected — resolve
        _resolve_notifications('FACTURE_ECART', instance.reference)


# ──────────────────────────────────────────────
# BC non réceptionné
# ──────────────────────────────────────────────

@receiver(post_save, sender=PurchaseOrder)
def on_po_save(sender, instance, **kwargs):
    if kwargs.get('raw'):
        return

    if instance.status == 'ENVOYEE':
        today = timezone.now().date()
        if instance.expected_date < today:
            date_str = instance.expected_date.strftime('%d/%m/%Y')
            _notify_users(
                roles=['MAGASINIER', 'ADMIN'],
                type_='BC_NON_RECU',
                titre=f"BC en attente de réception : {instance.code}",
                message=f"Livraison prévue le {date_str} non encore réceptionnée.",
                url=f'/commandes/{instance.pk}/',
            )

    elif instance.status in ('PARTIELLEMENT_RECUE', 'RECUE', 'CLOTUREE'):
        # BC received — resolve pending reception notification
        _resolve_notifications('BC_NON_RECU', instance.code)
