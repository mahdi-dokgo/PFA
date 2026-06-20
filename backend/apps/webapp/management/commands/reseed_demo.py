import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Efface et recharge des données réalistes — Clinique Al Shifa, Rabat"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=== STEP 1 — Suppression des données existantes ==='))
        self._delete_all()

        self.stdout.write(self.style.WARNING('\n=== STEP 2 — Utilisateurs ==='))
        users = self._seed_users()

        self.stdout.write(self.style.WARNING('\n=== STEP 3 — Référentiel ==='))
        suppliers = self._seed_suppliers()
        categories = self._seed_categories()
        articles = self._seed_articles(categories, suppliers)

        self.stdout.write(self.style.WARNING('\n=== STEP 4 — Processus achat ==='))
        requests = self._seed_requests(articles, users)
        orders = self._seed_orders(suppliers, requests, articles)
        self._seed_receptions(orders, articles, users)
        self._seed_factures(orders, suppliers, users)

        self.stdout.write(self.style.WARNING("\n=== STEP 5 — Journal d'audit ==="))
        self._seed_audit_logs(users)

        self.stdout.write(self.style.WARNING('\n=== STEP 6 — Notifications ==='))
        call_command('seed_notifications')

        self.stdout.write(self.style.SUCCESS('\nReseed Clinique Al Shifa terminé avec succès !'))

    # ------------------------------------------------------------------ #
    #  STEP 1 — Delete                                                     #
    # ------------------------------------------------------------------ #

    def _delete_all(self):
        from apps.audit.models import AuditLog
        from apps.notifications.models import Notification
        from apps.stock.models import StockMovement
        from apps.receptions.models import Reception, ReceptionLine
        from apps.orders.models import PurchaseOrder, POLine
        from apps.factures.models import Facture, LigneFacture
        from apps.consultations.models import Consultation, ConsultationFournisseur, Proposition
        from apps.requests_app.models import AuditEntry, PurchaseRequest, RequestLine
        from apps.articles.models import Article, Category
        from apps.suppliers.models import Supplier
        from apps.users.models import User

        pairs = [
            (AuditLog,                'Journal audit'),
            (Notification,            'Notifications'),
            (StockMovement,           'Mouvements stock'),
            (ReceptionLine,           'Lignes réception'),
            (Reception,               'Réceptions'),
            (POLine,                  'Lignes BC'),
            (PurchaseOrder,           'Bons de commande'),
            (LigneFacture,            'Lignes facture'),
            (Facture,                 'Factures'),
            (Proposition,             'Propositions'),
            (ConsultationFournisseur, 'Consultations fournisseurs'),
            (Consultation,            'Consultations'),
            (AuditEntry,              'Entrées audit DA'),
            (RequestLine,             'Lignes demandes'),
            (PurchaseRequest,         'Demandes achat'),
        ]
        for model, label in pairs:
            n = model.objects.all().delete()[0]
            self.stdout.write(f'  ✓ {label} : {n} supprimé(s)')

        # Clear article–supplier M2M then delete
        for art in Article.objects.all():
            art.suppliers.clear()
        n = Article.objects.all().delete()[0]
        self.stdout.write(f'  ✓ Articles : {n} supprimé(s)')

        n = Category.objects.all().delete()[0]
        self.stdout.write(f'  ✓ Catégories : {n} supprimé(s)')

        n = Supplier.objects.all().delete()[0]
        self.stdout.write(f'  ✓ Fournisseurs : {n} supprimé(s)')

        n = User.objects.all().delete()[0]
        self.stdout.write(f'  ✓ Utilisateurs : {n} supprimé(s)')

    # ------------------------------------------------------------------ #
    #  STEP 2 — Users                                                      #
    # ------------------------------------------------------------------ #

    def _seed_users(self):
        from apps.users.models import User, Role

        rows = [
            ('Karim Benali',     'k.benali@alshifa.ma',     'admin', Role.ADMIN,      True),
            ('Nadia Ezzahraoui', 'n.ezzahraoui@alshifa.ma', '1234',  Role.DEMANDEUR,  False),
            ('Mourad Tazi',      'm.tazi@alshifa.ma',       '1234',  Role.VALIDATEUR, False),
            ('Salma Idrissi',    's.idrissi@alshifa.ma',    '1234',  Role.ACHETEUR,   False),
            ('Hassan Ouchen',    'h.ouchen@alshifa.ma',     '1234',  Role.MAGASINIER, False),
            ('Dr. Youssef Amrani', 'y.amrani@alshifa.ma',  '1234',  Role.DIRECTION,  False),
        ]
        result = {}
        for full_name, email, password, role, is_staff in rows:
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=role,
                is_staff=is_staff,
            )
            result[role] = user
            self.stdout.write(f'  ✓ {full_name} ({role})')
        return result

    # ------------------------------------------------------------------ #
    #  STEP 3 — Référentiel                                                #
    # ------------------------------------------------------------------ #

    def _seed_suppliers(self):
        from apps.suppliers.models import Supplier

        rows = [
            dict(name='Pharma Atlas Rabat',
                 contact_name='Hamid Berrada', email='contact@pharmaatlas.ma',
                 phone='0537-441-200', specialty='Médicaments et consommables médicaux',
                 avg_lead_time_days=2),
            dict(name='MedEquip Maroc',
                 contact_name='Fatima Zahra Alaoui', email='info@medequip.ma',
                 phone='0522-334-150', specialty='Matériel et équipements médicaux',
                 avg_lead_time_days=7),
            dict(name='CleanMed Services',
                 contact_name='Anas Senhaji', email='anas@cleanmed.ma',
                 phone='0537-882-310', specialty='Hygiène, désinfection et stérilisation',
                 avg_lead_time_days=3),
            dict(name='Bureau Pro Agdal',
                 contact_name='Rim Kettani', email='rim@bureauproagdal.ma',
                 phone='0537-771-090', specialty='Fournitures de bureau et administratives',
                 avg_lead_time_days=2),
            dict(name='TechMed Casablanca',
                 contact_name='Kamal Fassi', email='k.fassi@techmed.ma',
                 phone='0522-650-400', specialty='Équipements électroniques et informatiques',
                 avg_lead_time_days=5),
        ]
        result = {}
        for d in rows:
            s = Supplier.objects.create(**d)
            result[d['name']] = s
            self.stdout.write(f"  ✓ Fournisseur : {s.name}")
        return result

    def _seed_categories(self):
        from apps.articles.models import Category

        names = [
            'Consommables médicaux',
            'Équipements médicaux',
            'Hygiène et stérilisation',
            'Fournitures administratives',
        ]
        result = {}
        for name in names:
            c = Category.objects.create(name=name)
            result[name] = c
            self.stdout.write(f"  ✓ Catégorie : {c.name}")
        return result

    def _seed_articles(self, categories, suppliers):
        from apps.articles.models import Article

        rows = [
            dict(reference='MED-001', name='Gants chirurgicaux latex (boîte 100)',
                 unit='Boîte', category=categories['Consommables médicaux'],
                 current_stock=45, min_threshold=20, safety_stock=10,
                 supplier_keys=['Pharma Atlas Rabat']),
            dict(reference='MED-002', name='Seringues jetables 10ml (boîte 100)',
                 unit='Boîte', category=categories['Consommables médicaux'],
                 current_stock=8, min_threshold=15, safety_stock=5,
                 supplier_keys=['Pharma Atlas Rabat']),
            dict(reference='MED-003', name='Masques chirurgicaux (boîte 50)',
                 unit='Boîte', category=categories['Consommables médicaux'],
                 current_stock=60, min_threshold=25, safety_stock=10,
                 supplier_keys=['Pharma Atlas Rabat', 'CleanMed Services']),
            dict(reference='MED-004', name='Compresses stériles 10x10 (boîte 100)',
                 unit='Boîte', category=categories['Consommables médicaux'],
                 current_stock=12, min_threshold=10, safety_stock=5,
                 supplier_keys=['Pharma Atlas Rabat']),
            dict(reference='EQP-001', name='Tensiomètre électronique',
                 unit='Unité', category=categories['Équipements médicaux'],
                 current_stock=4, min_threshold=2, safety_stock=1,
                 supplier_keys=['MedEquip Maroc']),
            dict(reference='EQP-002', name='Fauteuil de consultation',
                 unit='Unité', category=categories['Équipements médicaux'],
                 current_stock=2, min_threshold=1, safety_stock=1,
                 supplier_keys=['MedEquip Maroc']),
            dict(reference='HYG-001', name='Solution désinfectante 5L',
                 unit='Bidon', category=categories['Hygiène et stérilisation'],
                 current_stock=18, min_threshold=8, safety_stock=4,
                 supplier_keys=['CleanMed Services']),
            dict(reference='HYG-002', name='Savon antiseptique liquide 1L',
                 unit='Flacon', category=categories['Hygiène et stérilisation'],
                 current_stock=6, min_threshold=10, safety_stock=5,
                 supplier_keys=['CleanMed Services']),
            dict(reference='ADM-001', name='Ramette papier A4',
                 unit='Ramette', category=categories['Fournitures administratives'],
                 current_stock=30, min_threshold=10, safety_stock=5,
                 supplier_keys=['Bureau Pro Agdal']),
            dict(reference='ADM-002', name='Cartouche encre HP (noir)',
                 unit='Unité', category=categories['Fournitures administratives'],
                 current_stock=3, min_threshold=4, safety_stock=2,
                 supplier_keys=['Bureau Pro Agdal', 'TechMed Casablanca']),
        ]
        result = {}
        for d in rows:
            supplier_keys = d.pop('supplier_keys')
            art = Article.objects.create(**d)
            art.suppliers.set([suppliers[k] for k in supplier_keys])
            result[d['reference']] = art
            self.stdout.write(f"  ✓ Article : {art.reference} — {art.name}")
        return result

    # ------------------------------------------------------------------ #
    #  STEP 4 — Processus achat                                            #
    # ------------------------------------------------------------------ #

    def _seed_requests(self, articles, users):
        from apps.requests_app.models import AuditEntry, PurchaseRequest, RequestLine

        nadia  = users['DEMANDEUR']
        mourad = users['VALIDATEUR']

        rows = [
            dict(code='DA-2026-001', status='CONVERTIE', priority='urgent', comment='',
                 lines=[(articles['MED-001'], 50), (articles['MED-002'], 20)]),
            dict(code='DA-2026-002', status='VALIDEE', priority='urgent', comment='',
                 lines=[(articles['MED-003'], 30), (articles['MED-004'], 20)]),
            dict(code='DA-2026-003', status='REJETEE', priority='medium',
                 comment='Budget insuffisant ce trimestre, reporter au T3',
                 lines=[(articles['EQP-002'], 3)]),
            dict(code='DA-2026-004', status='SOUMISE', priority='urgent', comment='',
                 lines=[(articles['HYG-001'], 10), (articles['HYG-002'], 15)]),
            dict(code='DA-2026-005', status='BROUILLON', priority='low', comment='',
                 lines=[(articles['ADM-001'], 10), (articles['ADM-002'], 5)]),
            dict(code='DA-2026-006', status='VALIDEE', priority='medium', comment='',
                 lines=[(articles['ADM-002'], 10)]),
        ]
        result = {}
        for d in rows:
            lines = d.pop('lines')
            pr = PurchaseRequest.objects.create(
                code=d['code'],
                requester=nadia,
                priority=d['priority'],
                status=d['status'],
                comment=d['comment'],
            )
            for article, qty in lines:
                RequestLine.objects.create(request=pr, article=article, quantity=qty)

            # AuditEntry pour les statuts avancés
            if d['status'] in ('SOUMISE', 'VALIDEE', 'CONVERTIE', 'REJETEE'):
                AuditEntry.objects.create(
                    request=pr, actor=nadia, actor_name=nadia.full_name, action='Soumission',
                )
            if d['status'] in ('VALIDEE', 'CONVERTIE'):
                AuditEntry.objects.create(
                    request=pr, actor=mourad, actor_name=mourad.full_name, action='Validation',
                )
            if d['status'] == 'REJETEE':
                AuditEntry.objects.create(
                    request=pr, actor=mourad, actor_name=mourad.full_name, action='Rejet',
                    comment='Budget insuffisant ce trimestre, reporter au T3',
                )

            result[d['code']] = pr
            self.stdout.write(f"  ✓ DA : {pr.code} ({pr.status})")
        return result

    def _seed_orders(self, suppliers, requests, articles):
        from apps.orders.models import PurchaseOrder, POLine

        rows = [
            dict(
                code='BC-2026-001',
                supplier=suppliers['Pharma Atlas Rabat'],
                request=requests['DA-2026-001'],
                status='RECUE',
                expected_date=datetime.date(2026, 5, 15),
                lines=[
                    (articles['MED-001'], 50, Decimal('85.00')),
                    (articles['MED-002'], 20, Decimal('120.00')),
                ],
            ),
            dict(
                code='BC-2026-002',
                supplier=suppliers['CleanMed Services'],
                request=requests['DA-2026-004'],
                status='ENVOYEE',
                expected_date=datetime.date(2026, 6, 25),
                lines=[
                    (articles['HYG-001'], 10, Decimal('95.00')),
                    (articles['HYG-002'], 15, Decimal('38.00')),
                ],
            ),
            dict(
                code='BC-2026-003',
                supplier=suppliers['Bureau Pro Agdal'],
                request=requests['DA-2026-006'],
                status='APPROUVEE',
                expected_date=datetime.date(2026, 6, 30),
                lines=[
                    (articles['ADM-001'], 10, Decimal('42.00')),
                    (articles['ADM-002'], 10, Decimal('155.00')),
                ],
            ),
            dict(
                code='BC-2026-004',
                supplier=suppliers['MedEquip Maroc'],
                request=None,
                status='BROUILLON',
                expected_date=datetime.date(2026, 7, 15),
                lines=[
                    (articles['EQP-001'], 3, Decimal('850.00')),
                ],
            ),
        ]
        result = {}
        for d in rows:
            lines_data = d.pop('lines')
            total = sum(qty * price for _, qty, price in lines_data)
            po = PurchaseOrder.objects.create(
                code=d['code'],
                supplier=d['supplier'],
                request=d['request'],
                status=d['status'],
                expected_date=d['expected_date'],
                total_amount=total,
            )
            for article, qty, unit_price in lines_data:
                POLine.objects.create(order=po, article=article, quantity=qty, unit_price=unit_price)

            result[d['code']] = po
            self.stdout.write(f"  ✓ BC : {po.code} ({po.status}) — {total:.2f} DH")
        return result

    def _seed_receptions(self, orders, articles, users):
        from apps.orders.models import POLine
        from apps.receptions.models import Reception, ReceptionLine
        from apps.stock.models import StockMovement

        hassan = users['MAGASINIER']
        bc = orders['BC-2026-001']

        rec = Reception.objects.create(
            code='REC-2026-001',
            po=bc,
            receiver=hassan,
            receiver_name=hassan.full_name,
            notes='Livraison conforme, colis en bon état',
        )

        for po_line in bc.lines.select_related('article').all():
            ReceptionLine.objects.create(
                reception=rec,
                po_line=po_line,
                article=po_line.article,
                ordered_quantity=po_line.quantity,
                received_quantity=po_line.quantity,
            )
            # Update POLine received_quantity
            po_line.received_quantity = po_line.quantity
            po_line.save(update_fields=['received_quantity'])

            # Update article stock
            art = po_line.article
            art.current_stock += po_line.quantity
            art.save(update_fields=['current_stock'])

            # Stock movement IN
            StockMovement.objects.create(
                article=art,
                movement_type='IN',
                quantity=po_line.quantity,
                reference=rec.code,
            )

        self.stdout.write(f"  ✓ Réception : {rec.code} → {bc.code}")

    def _seed_factures(self, orders, suppliers, users):
        from apps.factures.models import Facture, LigneFacture

        salma = users['ACHETEUR']
        bc = orders['BC-2026-001']

        fac = Facture.objects.create(
            reference='FAC-2026-001',
            bon_commande=bc,
            fournisseur=suppliers['Pharma Atlas Rabat'],
            date_facture=datetime.date(2026, 5, 20),
            date_echeance=datetime.date(2026, 6, 20),
            montant_ht=Decimal('6833.33'),
            montant_ttc=Decimal('8200.00'),
            statut='VALIDEE',
            created_by=salma,
        )
        LigneFacture.objects.create(
            facture=fac,
            designation='Gants chirurgicaux latex (boîte 100)',
            quantite=50,
            prix_unitaire=Decimal('85.00'),
        )
        LigneFacture.objects.create(
            facture=fac,
            designation='Seringues jetables 10ml (boîte 100)',
            quantite=20,
            prix_unitaire=Decimal('120.00'),
        )

        self.stdout.write(f"  ✓ Facture : {fac.reference} ({fac.statut}) — {fac.montant_ttc} DH TTC")

    # ------------------------------------------------------------------ #
    #  STEP 5 — AuditLog entries                                           #
    # ------------------------------------------------------------------ #

    def _seed_audit_logs(self, users):
        from apps.audit.utils import log_action

        nadia  = users['DEMANDEUR']
        mourad = users['VALIDATEUR']
        salma  = users['ACHETEUR']
        hassan = users['MAGASINIER']

        log_action('DA', 'DA-2026-001', 'Soumission',
                   user=nadia, detail='Priorité : Urgente')
        log_action('DA', 'DA-2026-001', 'Validation',
                   user=mourad, detail='Approuvé — réapprovisionnement urgent')
        log_action('BC', 'BC-2026-001', 'Création',
                   user=salma, detail='Fournisseur : Pharma Atlas Rabat | Montant : 6 650.00 DH')
        log_action('BC', 'BC-2026-001', 'Transition → Reçue', user=hassan)
        log_action('RECEPTION', 'REC-2026-001', 'Réception enregistrée',
                   user=hassan, detail='BC : BC-2026-001 — livraison conforme')
        log_action('FACTURE', 'FAC-2026-001', 'Validation',
                   user=salma, detail='Montant TTC : 8 200.00 DH')

        self.stdout.write("  ✓ 6 entrées AuditLog créées")
