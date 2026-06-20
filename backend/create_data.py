"""
Script de peuplement de la base de données avec des données de test réalistes.

Usage :
    python create_data.py

Toutes les données métier existantes sont supprimées avant chaque exécution.
Les utilisateurs sont conservés (get_or_create).
"""

import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'procurement.settings')

import django
django.setup()

from datetime import date, timedelta
from django.db.models import F
from django.utils import timezone

from apps.users.models import User
from apps.articles.models import Article, Category
from apps.suppliers.models import Supplier
from apps.requests_app.models import PurchaseRequest, RequestLine, AuditEntry
from apps.consultations.models import Consultation, Quote
from apps.orders.models import PurchaseOrder, POLine
from apps.receptions.models import Reception, ReceptionLine
from apps.stock.models import StockMovement

# ── Affichage ──────────────────────────────────────────────────────────────

def ok(msg):    print(f'  \033[92m✓\033[0m {msg}')
def section(t): print(f'\n\033[1;94m── {t} ──\033[0m')

# ── Nettoyage des données métier ───────────────────────────────────────────

section('Nettoyage')
MODELS_TO_CLEAR = [
    StockMovement, ReceptionLine, Reception,
    POLine, PurchaseOrder,
    Quote, Consultation,
    AuditEntry, RequestLine, PurchaseRequest,
    Article, Category, Supplier,
]
for Model in MODELS_TO_CLEAR:
    n, _ = Model.objects.all().delete()
    print(f'  {Model.__name__:<20} {n} supprimé(s)')

# ── Utilisateurs (non supprimés) ───────────────────────────────────────────

section('Utilisateurs')
USERS = [
    ('admin@acme.com',       'Sophie Martin',  'ADMIN'),
    ('demandeur@acme.com',   'Karim Benali',   'DEMANDEUR'),
    ('validateur@acme.com',  'Anne Dupont',    'VALIDATEUR'),
    ('acheteur@acme.com',    'Marc Lefevre',   'ACHETEUR'),
    ('magasinier@acme.com',  'Yasmine Haddad', 'MAGASINIER'),
    ('direction@acme.com',   'Pierre Rousseau','DIRECTION'),
]
roles = {}
for email, full_name, role in USERS:
    u, created = User.objects.get_or_create(
        email=email,
        defaults={'full_name': full_name, 'role': role, 'is_active': True},
    )
    if created:
        u.set_password('demo1234')
        u.save()
    roles[role] = u
    ok(f'{role:<12} {u.full_name}  ({email})')

admin      = roles['ADMIN']
demandeur  = roles['DEMANDEUR']
validateur = roles['VALIDATEUR']
acheteur   = roles['ACHETEUR']
magasinier = roles['MAGASINIER']

# ── 5 Catégories ───────────────────────────────────────────────────────────

section('5 Catégories')
CATS = [
    ('Informatique & Téléphonie',  'Matériel informatique, périphériques et équipements téléphoniques'),
    ('Fournitures de bureau',      'Papeterie, consommables et petits équipements de bureau'),
    ('Mobilier & Aménagement',     "Bureaux, chaises, rangements et cloisons"),
    ('Hygiène & Nettoyage',        "Produits d'entretien, consommables sanitaires et matériel de nettoyage"),
    ('Sécurité & EPI',             'Équipements de protection individuelle et matériel de sécurité'),
]
cats = [Category.objects.create(name=n, description=d) for n, d in CATS]
for c in cats:
    ok(c.name)

c_info, c_bur, c_mob, c_hyg, c_sec = cats

# ── 10 Fournisseurs ────────────────────────────────────────────────────────

section('10 Fournisseurs')
# (name, contact_name, email, phone, specialty, avg_lead_time_days, notes)
SUPPS = [
    ('Dell Technologies France', 'François Mercier',   'f.mercier@dell.fr',          '01 30 67 00 00', 'Informatique',             7,  'Remise 12 % sur commandes > 5 000 €'),
    ('HP France',                'Claire Vidal',        'c.vidal@hp.fr',               '01 69 82 60 00', 'Informatique',            10,  'Contrat cadre imprimantes et consommables'),
    ('Staples France',           'Mohammed Aïssa',      'm.aissa@staples.fr',           '01 55 27 40 00', 'Fournitures de bureau',    3,  'Livraison J+1 si commande avant 14 h'),
    ('Lyreco',                   'Isabelle Fontaine',   'i.fontaine@lyreco.fr',         '03 21 60 60 60', 'Fournitures de bureau',    4,  'Catalogue complet papeterie et hygiène'),
    ('Kinnarps France',          'Thomas Girard',       't.girard@kinnarps.fr',         '01 44 83 17 00', 'Mobilier',                21,  'Mobilier ergonomique haut de gamme – délai sur mesure'),
    ('Manutan',                  'Lucie Bernard',       'l.bernard@manutan.fr',         '01 48 14 57 00', 'Mobilier & Équipements',  14,  'Large gamme mobilier pro et matériel entrepôt'),
    ('Ecolab France',            'Rachid Amrani',       'r.amrani@ecolab.fr',           '01 47 17 20 00', 'Hygiène & Nettoyage',      7,  'Produits professionnels certifiés environnement'),
    ('Initial',                  'Nathalie Chevallier', 'n.chevallier@initial.fr',      '01 55 47 20 00', 'Hygiène',                  5,  'Location-entretien de textiles professionnels'),
    ('Uvex Safety France',       'Julien Moreaux',      'j.moreaux@uvex.fr',            '03 88 04 28 00', 'Sécurité & EPI',          10,  'EPI certifiés CE – casques, chaussures, lunettes'),
    ('Prosécurité',              'Sandra Lefèvre',      's.lefevre@prosecurite.fr',     '04 72 76 30 00', 'Sécurité',                 8,  'Signalétique, alarmes et matériel incendie'),
]
supps = []
for name, contact, email, phone, spec, lead, notes in SUPPS:
    s = Supplier.objects.create(
        name=name, contact_name=contact, email=email, phone=phone,
        specialty=spec, avg_lead_time_days=lead, notes=notes, status='active',
    )
    supps.append(s)
    ok(f'{name}  (délai moyen : {lead}j)')

s_dell, s_hp, s_staples, s_lyreco, s_kinnarps, s_manutan, s_ecolab, s_initial, s_uvex, s_prosec = supps

# ── 20 Articles ────────────────────────────────────────────────────────────

section('20 Articles')
# (ref, name, unit, cat, min_threshold, current_stock, safety_stock, suppliers)
ARTICLES = [
    # Informatique (stock parfois sous le seuil pour déclencher les alertes)
    ('REF-INFO-001', 'Ordinateur portable 15" Core i5',  'unité',   c_info, 5,  3,  2, [s_dell, s_hp]),      # ⚠ alerte
    ('REF-INFO-002', 'Écran 24" Full HD',                'unité',   c_info, 10, 12, 4, [s_dell]),
    ('REF-INFO-003', 'Clavier sans fil AZERTY',          'unité',   c_info, 15, 8,  5, [s_dell, s_hp]),       # ⚠ alerte
    ('REF-INFO-004', 'Souris ergonomique Bluetooth',     'unité',   c_info, 20, 25, 8, [s_hp]),
    ('REF-INFO-005', 'Câble USB-C 2 m',                  'unité',   c_info, 30, 40, 10,[s_dell, s_hp]),
    # Bureautique
    ('REF-BUR-001', 'Ramette papier A4 80g (500 feuilles)', 'ramette', c_bur, 50, 120, 20, [s_staples, s_lyreco]),
    ('REF-BUR-002', 'Stylos bille bleu (boîte 12)',      'boîte',   c_bur, 20, 35, 8,  [s_staples, s_lyreco]),
    ('REF-BUR-003', 'Cartouche encre noire HP 304',      'unité',   c_bur, 10, 6,  3,  [s_hp, s_lyreco]),     # ⚠ alerte
    ('REF-BUR-004', 'Classeur A4 dos 8 cm',              'unité',   c_bur, 40, 55, 15, [s_staples]),
    ('REF-BUR-005', 'Post-it 76×76 (bloc 100 feuilles)', 'bloc',    c_bur, 60, 44, 20, [s_lyreco]),           # ⚠ alerte
    # Mobilier
    ('REF-MOB-001', 'Bureau réglable hauteur 160×80 cm', 'unité',   c_mob, 3,  5,  1,  [s_kinnarps]),
    ('REF-MOB-002', 'Fauteuil de direction ergonomique', 'unité',   c_mob, 5,  4,  2,  [s_kinnarps, s_manutan]),# ⚠ alerte
    ('REF-MOB-003', 'Étagère métallique 5 niveaux',      'unité',   c_mob, 4,  2,  2,  [s_manutan]),          # ⚠ alerte
    ('REF-MOB-004', 'Table de réunion 8 personnes',      'unité',   c_mob, 2,  1,  1,  [s_kinnarps]),         # ⚠ alerte
    # Hygiène
    ('REF-HYG-001', 'Gel hydroalcoolique 500 ml',        'flacon',  c_hyg, 30, 48, 10, [s_ecolab, s_lyreco]),
    ('REF-HYG-002', 'Papier toilette recyclé (colis 96)','colis',   c_hyg, 10, 8,  4,  [s_ecolab, s_initial]),# ⚠ alerte
    ('REF-HYG-003', 'Savon liquide mains 5 L',           'bidon',   c_hyg, 8,  5,  3,  [s_ecolab]),           # ⚠ alerte
    ('REF-HYG-004', 'Sacs poubelle 110 L (rouleau 10)',  'rouleau', c_hyg, 20, 32, 8,  [s_lyreco]),
    # Sécurité
    ('REF-SEC-001', 'Chaussures de sécurité S3 (paire)', 'paire',   c_sec, 6,  4,  2,  [s_uvex]),             # ⚠ alerte
    ('REF-SEC-002', 'Casque de chantier blanc',          'unité',   c_sec, 10, 7,  4,  [s_uvex, s_prosec]),   # ⚠ alerte
]
articles = []
for ref, name, unit, cat, min_th, stock, safety, article_supps in ARTICLES:
    a = Article.objects.create(
        reference=ref, name=name, unit=unit, category=cat,
        min_threshold=min_th, current_stock=stock, safety_stock=safety,
    )
    a.suppliers.set(article_supps)
    articles.append(a)
    flag = '  ⚠ alerte' if stock < min_th else ''
    ok(f'{ref}  {name}  (stock: {stock}/{min_th}){flag}')

# Mouvement d'ajustement initial pour tracer l'ouverture du stock
for a in articles:
    if a.current_stock > 0:
        StockMovement.objects.create(
            article=a, movement_type='ADJUST',
            quantity=a.current_stock, reference='INIT-2026',
        )

(a_laptop, a_ecran, a_clavier, a_souris, a_cable,
 a_papier, a_stylos, a_cartouche, a_classeur, a_postit,
 a_bureau, a_fauteuil, a_etagere, a_table,
 a_gel, a_papiertoil, a_savon, a_sacs,
 a_chaussures, a_casque) = articles

# ── 5 Demandes d'achat ────────────────────────────────────────────────────

section("5 Demandes d'achat")
now = timezone.now()

def make_request(priority, target_status, lines, comment=''):
    """Crée une DA et rejoue l'audit trail jusqu'au statut cible."""
    req = PurchaseRequest(requester=demandeur, priority=priority, comment=comment)
    req.save()
    for article, qty, justif in lines:
        RequestLine.objects.create(request=req, article=article, quantity=qty, justification=justif)
    AuditEntry.objects.create(request=req, actor=demandeur,
                              actor_name=demandeur.full_name, action='Création', at=now)
    if target_status in ('SOUMISE', 'VALIDEE', 'REJETEE', 'CONVERTIE'):
        req.status = 'SOUMISE'
        req.save()
        AuditEntry.objects.create(request=req, actor=demandeur,
                                  actor_name=demandeur.full_name, action='Soumission', at=now)
    if target_status == 'VALIDEE':
        req.status = 'VALIDEE'
        req.save()
        AuditEntry.objects.create(request=req, actor=validateur,
                                  actor_name=validateur.full_name, action='Validation',
                                  comment='Approuvé – priorité confirmée', at=now)
    if target_status == 'REJETEE':
        req.status = 'REJETEE'
        req.save()
        AuditEntry.objects.create(request=req, actor=validateur,
                                  actor_name=validateur.full_name, action='Rejet',
                                  comment=comment or 'Budget insuffisant', at=now)
    if target_status == 'CONVERTIE':
        req.status = 'CONVERTIE'
        req.save()
        AuditEntry.objects.create(request=req, actor=acheteur,
                                  actor_name=acheteur.full_name, action='Conversion en BC', at=now)
    return req

req1 = make_request('urgent', 'VALIDEE', [
    (a_laptop,   3, 'Renouvellement postes service RH – arrivée 3 CDI le 02/06'),
    (a_ecran,    3, 'Un écran par nouveau poste'),
    (a_clavier,  3, ''),
], comment='Urgent : intégration de 3 nouveaux collaborateurs')
ok(f'{req1.code} [VALIDEE]   – {req1.lines.count()} lignes, {req1.audit.count()} entrées audit')

req2 = make_request('medium', 'SOUMISE', [
    (a_papier,   20, 'Réapprovisionnement trimestriel'),
    (a_stylos,    5, ''),
    (a_classeur, 10, 'Archivage contrats Q2'),
])
ok(f'{req2.code} [SOUMISE]   – {req2.lines.count()} lignes, {req2.audit.count()} entrées audit')

req3 = make_request('low', 'BROUILLON', [
    (a_bureau,   2, 'Agrandissement open-space bâtiment B'),
    (a_fauteuil, 2, ''),
])
ok(f'{req3.code} [BROUILLON] – {req3.lines.count()} lignes, {req3.audit.count()} entrées audit')

req4 = make_request('medium', 'REJETEE', [
    (a_table,    1, 'Salle de réunion 3ème étage'),
    (a_fauteuil, 8, 'Remplacement mobilier vétuste'),
], comment='Budget Q2 insuffisant – reporter en Q3')
ok(f'{req4.code} [REJETEE]   – {req4.lines.count()} lignes, {req4.audit.count()} entrées audit')

req5 = make_request('urgent', 'CONVERTIE', [
    (a_gel,   10, 'Réassort dotation mensuelle hygiène'),
    (a_savon,  5, ''),
    (a_sacs,   4, ''),
])
ok(f'{req5.code} [CONVERTIE] – {req5.lines.count()} lignes, {req5.audit.count()} entrées audit')

# ── 3 Consultations avec devis ─────────────────────────────────────────────

section('3 Consultations')

def make_consultation(linked_req, supps_list, arts_list, quotes, final_status):
    """Crée une consultation, ses devis, puis ferme si nécessaire."""
    c = Consultation(request=linked_req)
    c.save()
    c.suppliers.set(supps_list)
    c.articles.set(arts_list)
    # (supplier, unit_price, delay_days, available, quality_score, selected)
    for s, price, delay, avail, score, selected in quotes:
        Quote.objects.create(
            consultation=c, supplier=s, unit_price=price,
            delay_days=delay, available=avail, quality_score=score, selected=selected,
        )
    if final_status == 'closed':
        c.status = 'closed'
        c.save()
    return c

cons1 = make_consultation(
    req1, [s_dell, s_hp], [a_laptop, a_ecran, a_clavier],
    [
        (s_dell, 1_250.00, 10, True,  4.5, True),
        (s_hp,   1_190.00, 14, True,  4.1, False),
    ],
    'closed',
)
ok(f'{cons1.code} [closed]  – Dell retenu (meilleur score qualité)')

cons2 = make_consultation(
    req2, [s_staples, s_lyreco], [a_papier, a_stylos, a_classeur],
    [
        (s_staples, 4.20, 3, True, 4.7, False),
        (s_lyreco,  4.50, 4, True, 4.3, False),
    ],
    'open',
)
ok(f'{cons2.code} [open]    – en attente de sélection du devis')

cons3 = make_consultation(
    None, [s_ecolab, s_initial, s_lyreco], [a_gel, a_savon, a_sacs],
    [
        (s_ecolab,  3.80, 7, True,  4.6, True),
        (s_initial, 4.10, 5, True,  4.2, False),
        (s_lyreco,  3.95, 4, False, 3.8, False),
    ],
    'closed',
)
ok(f'{cons3.code} [closed]  – Ecolab retenu (meilleur rapport qualité/prix)')

# ── 5 Bons de commande ────────────────────────────────────────────────────

section('5 Bons de commande')
today = date.today()

def make_po(supplier, linked_req, target_status, exp_days, lines):
    """Crée un BC avec ses lignes et positionne son statut."""
    total = sum(qty * price for _, qty, price in lines)
    po = PurchaseOrder(
        supplier=supplier, request=linked_req,
        expected_date=today + timedelta(days=exp_days), total_amount=total,
    )
    po.save()
    po_lines = []
    for article, qty, price in lines:
        line = POLine.objects.create(order=po, article=article, quantity=qty, unit_price=price)
        po_lines.append((line, article, qty))
    po.status = target_status
    po.save()
    return po, po_lines

po1, lines1 = make_po(s_dell, req5, 'RECUE', 7, [
    (a_laptop,  3, 1_240.00),
    (a_ecran,   3,   210.00),
    (a_clavier, 3,    55.00),
])
ok(f'{po1.code} [RECUE]               – Dell  {po1.total_amount:.2f} €')

po2, lines2 = make_po(s_staples, req2, 'ENVOYEE', 4, [
    (a_papier,   20,  4.30),
    (a_stylos,    5,  8.90),
    (a_classeur, 10,  2.50),
])
ok(f'{po2.code} [ENVOYEE]             – Staples  {po2.total_amount:.2f} €')

po3, lines3 = make_po(s_kinnarps, None, 'APPROUVEE', 30, [
    (a_bureau,   2, 890.00),
    (a_fauteuil, 4, 450.00),
])
ok(f'{po3.code} [APPROUVEE]           – Kinnarps  {po3.total_amount:.2f} €')

po4, lines4 = make_po(s_ecolab, req5, 'PARTIELLEMENT_RECUE', 5, [
    (a_gel,   10,  3.85),
    (a_savon,  5, 12.50),
])
ok(f'{po4.code} [PARTIELLEMENT_RECUE] – Ecolab  {po4.total_amount:.2f} €')

po5, lines5 = make_po(s_uvex, None, 'BROUILLON', 14, [
    (a_chaussures, 5, 85.00),
    (a_casque,    10, 22.00),
])
ok(f'{po5.code} [BROUILLON]           – Uvex  {po5.total_amount:.2f} €')

# ── 3 Réceptions avec mouvements de stock ─────────────────────────────────

section('3 Réceptions')

def receive(po, po_lines_data, receiver, notes, fractions=None):
    """
    Crée une réception, met à jour les quantités reçues sur les lignes BC,
    incrémente le stock des articles et génère les mouvements de stock IN.

    po_lines_data : list of (POLine, Article, ordered_qty)
    fractions     : list of actually-received quantities (defaults to full quantity)
    """
    rec = Reception(po=po, receiver=receiver, receiver_name=receiver.full_name, notes=notes)
    rec.save()
    for i, (po_line, article, ordered_qty) in enumerate(po_lines_data):
        received_qty = fractions[i] if fractions else ordered_qty
        ReceptionLine.objects.create(
            reception=rec, po_line=po_line, article=article,
            ordered_quantity=ordered_qty, received_quantity=received_qty,
        )
        po_line.received_quantity += received_qty
        po_line.save()
        article.current_stock += received_qty
        article.save()
        StockMovement.objects.create(
            article=article, movement_type='IN',
            quantity=received_qty, reference=rec.code,
        )
    # Recalcul statut BC depuis la DB (valeurs à jour)
    all_lines = list(po.lines.all())
    all_done  = all(l.received_quantity >= l.quantity for l in all_lines)
    any_rec   = any(l.received_quantity > 0         for l in all_lines)
    if all_done:
        po.status = 'RECUE'
    elif any_rec:
        po.status = 'PARTIELLEMENT_RECUE'
    po.save()
    return rec

# Réception 1 : BC Dell – réception complète (3 laptops + 3 écrans + 3 claviers)
rec1 = receive(
    po1, lines1, magasinier,
    'Livraison conforme. Matériel vérifié et déballé avant rangement en salle serveur.',
)
ok(f'{rec1.code} – Dell   : réception complète ({len(lines1)} lignes)')

# Réception 2 : BC Ecolab – réception partielle (gel OK, savon en rupture)
rec2 = receive(
    po4, lines4[:1], magasinier,
    'Livraison partielle : gel reçu (8/10 flacons), savon reporté sous 10 jours.',
    fractions=[8],
)
ok(f'{rec2.code} – Ecolab : réception partielle (1/2 lignes, 8/10 unités)')

# Réception 3 : BC Staples – réception complète (fournitures de bureau)
rec3 = receive(
    po2, lines2, magasinier,
    'Fournitures de bureau reçues et rangées en armoire de stockage couloir B.',
)
ok(f'{rec3.code} – Staples : réception complète ({len(lines2)} lignes)')

# ── Résumé final ───────────────────────────────────────────────────────────

section('Résumé')
nb_alerts = Article.objects.filter(current_stock__lt=F('min_threshold')).count()
print(f'  Catégories            : {Category.objects.count()}')
print(f'  Fournisseurs          : {Supplier.objects.count()}')
print(f'  Articles              : {Article.objects.count()}  (dont {nb_alerts} en alerte stock)')
print(f'  Demandes d\'achat      : {PurchaseRequest.objects.count()}')
print(f'  Lignes DA             : {RequestLine.objects.count()}')
print(f'  Entrées audit         : {AuditEntry.objects.count()}')
print(f'  Consultations         : {Consultation.objects.count()}')
print(f'  Devis                 : {Quote.objects.count()}')
print(f'  Bons de commande      : {PurchaseOrder.objects.count()}')
print(f'  Lignes BC             : {POLine.objects.count()}')
print(f'  Réceptions            : {Reception.objects.count()}')
print(f'  Lignes réception      : {ReceptionLine.objects.count()}')
print(f'  Mouvements de stock   : {StockMovement.objects.count()}')
print('\n\033[1;92mBase de données peuplée avec succès !\033[0m')
