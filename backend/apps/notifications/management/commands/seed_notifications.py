from django.core.management.base import BaseCommand
from django.db.models import F
from django.utils import timezone


class Command(BaseCommand):
    help = 'Recrée les notifications basées sur les données actuelles (idempotent)'

    def handle(self, *args, **options):
        from apps.articles.models import Article
        from apps.factures.models import Facture
        from apps.notifications.models import Notification
        from apps.orders.models import PurchaseOrder
        from apps.requests_app.models import PurchaseRequest
        from apps.users.models import Role, User

        Notification.objects.all().delete()
        self.stdout.write('  Notifications existantes supprimées.')

        created = 0
        today = timezone.now().date()

        def notify(roles, type_, titre, message, url=''):
            nonlocal created
            for user in User.objects.filter(role__in=roles, is_active=True):
                Notification.objects.create(
                    user=user, type=type_,
                    titre=titre, message=message, url=url,
                )
                created += 1

        # 1 — Stock critique : tous les articles sous le seuil minimum
        for article in Article.objects.filter(current_stock__lt=F('min_threshold')):
            notify(
                roles=[Role.MAGASINIER, Role.ADMIN],
                type_='STOCK_CRITIQUE',
                titre=f'Stock critique : {article.name}',
                message=(
                    f'La quantité de {article.name} est de {article.current_stock} '
                    f'(seuil min : {article.min_threshold})'
                ),
                url='/stock/?alert=1',
            )
            self.stdout.write(f'  ✓ STOCK_CRITIQUE : {article.reference}')

        # 2 — DA en attente de validation : toutes les DA soumises
        for pr in PurchaseRequest.objects.filter(status='SOUMISE'):
            notify(
                roles=[Role.VALIDATEUR, Role.ADMIN],
                type_='DA_EN_ATTENTE',
                titre=f'Nouvelle DA à valider : {pr.code}',
                message="Un utilisateur a soumis une demande d'achat.",
                url='/demandes/',
            )
            self.stdout.write(f'  ✓ DA_EN_ATTENTE : {pr.code}')

        # 3 — BC non réceptionné : statut ENVOYEE avec date de livraison dépassée
        for po in PurchaseOrder.objects.filter(status='ENVOYEE', expected_date__lt=today):
            notify(
                roles=[Role.MAGASINIER, Role.ADMIN],
                type_='BC_NON_RECU',
                titre=f'BC non réceptionné : {po.code}',
                message=(
                    f'Le bon de commande {po.code} (fournisseur : {po.supplier.name}) '
                    f'était attendu le {po.expected_date.strftime("%d/%m/%Y")}.'
                ),
                url='/commandes/',
            )
            self.stdout.write(f'  ✓ BC_NON_RECU : {po.code}')

        # 4 — Facture avec écart de montant détecté
        for facture in Facture.objects.filter(ecart_detected=True):
            bc_montant = (
                f'{facture.bon_commande.total_amount:.2f}'
                if facture.bon_commande else '—'
            )
            notify(
                roles=[Role.ADMIN, Role.ACHETEUR],
                type_='FACTURE_ECART',
                titre=f'Écart facture : {facture.reference}',
                message=(
                    f'Écart entre BC ({bc_montant} DH) '
                    f'et facture ({facture.montant_ttc:.2f} DH).'
                ),
                url=f'/factures/{facture.pk}/',
            )
            self.stdout.write(f'  ✓ FACTURE_ECART : {facture.reference}')

        if created == 0:
            self.stdout.write('  (aucune condition active trouvée)')

        self.stdout.write(self.style.SUCCESS(f'{created} notification(s) créée(s).'))
