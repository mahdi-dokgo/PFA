import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, F, Sum
from django.urls import reverse
from django.utils import timezone
from django.views.generic import TemplateView

from apps.articles.models import Article
from apps.factures.models import Facture
from apps.orders.models import PurchaseOrder
from apps.receptions.models import Reception
from apps.requests_app.models import PurchaseRequest, RequestLine
from apps.suppliers.models import Supplier
from apps.users.models import Role

from ..forms.receptions import RECEIVABLE_STATUSES

DEMANDEUR_REQUEST_STATUSES = [
    PurchaseRequest.Status.BROUILLON,
    PurchaseRequest.Status.SOUMISE,
    PurchaseRequest.Status.VALIDEE,
    PurchaseRequest.Status.REJETEE,
]

ALL_REQUEST_STATUSES = [status for status, _ in PurchaseRequest.Status.choices]
ALL_PO_STATUSES = [status for status, _ in PurchaseOrder.Status.choices]

REQUEST_STATUS_LABELS = dict(PurchaseRequest.Status.choices)
PO_STATUS_LABELS = dict(PurchaseOrder.Status.choices)

_REQ_BADGE = {
    'BROUILLON': 'secondary',
    'SOUMISE': 'warning',
    'VALIDEE': 'success',
    'REJETEE': 'danger',
    'CONVERTIE': 'info',
}
_PO_BADGE = {
    'BROUILLON': 'secondary',
    'APPROUVEE': 'success',
    'ENVOYEE': 'primary',
    'PARTIELLEMENT_RECUE': 'info',
    'RECUE': 'success',
    'CLOTUREE': 'secondary',
    'ANNULEE': 'danger',
}

_REQ_COLORS = {
    'BROUILLON': '#9ca3af',
    'SOUMISE': '#f59e0b',
    'VALIDEE': '#22c55e',
    'REJETEE': '#ef4444',
    'CONVERTIE': '#3b82f6',
}
_PO_COLORS = {
    'BROUILLON': '#9ca3af',
    'APPROUVEE': '#22c55e',
    'ENVOYEE': '#3b82f6',
    'PARTIELLEMENT_RECUE': '#14b8a6',
    'RECUE': '#a855f7',
    'CLOTUREE': '#6b7280',
    'ANNULEE': '#ef4444',
}


def _status_counts(queryset, statuses, labels):
    counts = {row['status']: row['total'] for row in queryset.values('status').annotate(total=Count('id'))}
    return [{'status': s, 'label': labels[s], 'count': counts.get(s, 0)} for s in statuses]


def _build_alerts(user, context):
    alerts = []
    role = user.role

    if role in (Role.MAGASINIER, Role.ADMIN, Role.DIRECTION):
        n = context['stock_alert_count']
        if n is None:
            n = Article.objects.filter(current_stock__lte=F('min_threshold')).count()
        if n:
            alerts.append({
                'icon': 'bi-exclamation-triangle', 'color': 'danger',
                'title': f"{n} article(s) sous le seuil minimal", 'subtitle': 'Stock critique',
                'url': f"{reverse('webapp:stock_overview')}?alert=1",
            })

    if role in (Role.VALIDATEUR, Role.ADMIN, Role.DIRECTION):
        n = context['pending_validation_count']
        if n is None:
            n = PurchaseRequest.objects.filter(status=PurchaseRequest.Status.SOUMISE).count()
        if n:
            alerts.append({
                'icon': 'bi-clock-history', 'color': 'warning',
                'title': f"{n} demande(s) en attente de validation", 'subtitle': 'Action requise',
                'url': f"{reverse('webapp:request_list')}?status=SOUMISE",
            })

    if role in (Role.ACHETEUR, Role.ADMIN, Role.DIRECTION):
        n = context['validated_requests_count']
        if n is None:
            n = PurchaseRequest.objects.filter(status=PurchaseRequest.Status.VALIDEE).count()
        if n:
            alerts.append({
                'icon': 'bi-arrow-right-circle', 'color': 'info',
                'title': f"{n} demande(s) validée(s) à convertir en BC", 'subtitle': 'À traiter',
                'url': f"{reverse('webapp:request_list')}?status=VALIDEE",
            })

    if role in (Role.MAGASINIER, Role.ADMIN, Role.DIRECTION):
        n = context['receivable_po_count']
        if n is None:
            n = PurchaseOrder.objects.filter(status__in=RECEIVABLE_STATUSES).count()
        if n:
            alerts.append({
                'icon': 'bi-truck', 'color': 'primary',
                'title': f"{n} bon(s) de commande en attente de réception", 'subtitle': 'À réceptionner',
                'url': reverse('webapp:reception_create'),
            })

    return alerts


# ──────────────────────────────────────────────
# Summary KPI bar helpers
# ──────────────────────────────────────────────

def _kpi(label, value, icon, color, font_size=28, animate=True):
    return {'label': label, 'value': value, 'icon': icon, 'color': color,
            'font_size': font_size, 'animate': animate}


def _fmt_budget(raw):
    return f"{int(raw):,}".replace(',', ' ') + " DH"


def _admin_kpis():
    total = PurchaseRequest.objects.count()
    budget_raw = (
        PurchaseOrder.objects.exclude(status__in=['BROUILLON', 'ANNULEE'])
        .aggregate(t=Sum('total_amount'))['t'] or 0
    )
    non_draft = PurchaseRequest.objects.exclude(status='BROUILLON').count()
    validated = PurchaseRequest.objects.filter(status__in=['VALIDEE', 'CONVERTIE']).count()
    taux = round(validated / non_draft * 100) if non_draft else 0
    po_linked = list(
        PurchaseOrder.objects.filter(request__isnull=False).select_related('request')[:100]
    )
    delays = [max(0, (po.created_at - po.request.created_at).days) for po in po_linked]
    delai = round(sum(delays) / len(delays)) if delays else 0
    return [
        _kpi('Total demandes',    str(total),          'bi-file-earmark-text', '#3b82f6'),
        _kpi('Budget engagé',     _fmt_budget(budget_raw), 'bi-cash-stack',   '#22c55e', font_size=22, animate=False),
        _kpi('Taux de validation', f'{taux}%',          'bi-check-circle',   '#14b8a6'),
        _kpi('Délai moyen',       f'{delai} j',         'bi-clock',          '#f59e0b'),
    ]


def _role_kpis(user):
    role = user.role

    if role == Role.DEMANDEUR:
        mine = PurchaseRequest.objects.filter(requester=user)
        return [
            _kpi('Mes demandes', str(mine.count()),                                      'bi-file-earmark-text', '#3b82f6'),
            _kpi('En attente',   str(mine.filter(status='SOUMISE').count()),              'bi-hourglass-split',   '#f59e0b'),
            _kpi('Validées',     str(mine.filter(status__in=['VALIDEE','CONVERTIE']).count()), 'bi-check-circle', '#22c55e'),
            _kpi('Rejetées',     str(mine.filter(status='REJETEE').count()),              'bi-x-circle',          '#ef4444'),
        ]

    if role == Role.VALIDATEUR:
        soumise  = PurchaseRequest.objects.filter(status='SOUMISE').count()
        validee  = PurchaseRequest.objects.filter(status__in=['VALIDEE', 'CONVERTIE']).count()
        rejetee  = PurchaseRequest.objects.filter(status='REJETEE').count()
        total_processed = validee + rejetee
        taux = round(validee / total_processed * 100) if total_processed else 0
        return [
            _kpi('À valider',         str(soumise), 'bi-hourglass-split', '#f59e0b'),
            _kpi('Validées',          str(validee), 'bi-check-circle',    '#22c55e'),
            _kpi('Rejetées',          str(rejetee), 'bi-x-circle',        '#ef4444'),
            _kpi('Taux de validation', f'{taux}%',  'bi-percent',         '#14b8a6'),
        ]

    if role == Role.ACHETEUR:
        bc_en_cours = PurchaseOrder.objects.filter(
            status__in=['APPROUVEE', 'ENVOYEE', 'PARTIELLEMENT_RECUE']
        ).count()
        budget_raw = (
            PurchaseOrder.objects.exclude(status__in=['BROUILLON', 'ANNULEE'])
            .aggregate(t=Sum('total_amount'))['t'] or 0
        )
        fournisseurs     = Supplier.objects.filter(status='active').count()
        factures_attente = Facture.objects.filter(statut='EN_ATTENTE').count()
        return [
            _kpi('BC en cours',          str(bc_en_cours),        'bi-cart-check', '#3b82f6'),
            _kpi('Budget engagé',        _fmt_budget(budget_raw), 'bi-cash-stack', '#22c55e', font_size=22, animate=False),
            _kpi('Fournisseurs actifs',  str(fournisseurs),       'bi-truck',      '#14b8a6'),
            _kpi('Factures en attente',  str(factures_attente),   'bi-receipt',    '#f59e0b'),
        ]

    if role == Role.MAGASINIER:
        receptable        = PurchaseOrder.objects.filter(status__in=RECEIVABLE_STATUSES).count()
        sous_seuil        = Article.objects.filter(current_stock__lte=F('min_threshold')).count()
        now               = timezone.now()
        receptions_mois   = Reception.objects.filter(
            received_at__year=now.year, received_at__month=now.month
        ).count()
        total_articles    = Article.objects.count()
        return [
            _kpi('Réceptions en attente', str(receptable),      'bi-truck',            '#3b82f6'),
            _kpi('Articles sous seuil',   str(sous_seuil),      'bi-exclamation-triangle', '#ef4444'),
            _kpi('Réceptions ce mois',    str(receptions_mois), 'bi-box-arrow-in-down', '#22c55e'),
            _kpi('Articles en stock',     str(total_articles),  'bi-box-seam',         '#14b8a6'),
        ]

    return _admin_kpis()


# ──────────────────────────────────────────────
# Chart data helpers
# ──────────────────────────────────────────────

def _top_suppliers_data():
    rows = (
        PurchaseOrder.objects.exclude(status='ANNULEE')
        .values('supplier__name')
        .annotate(total=Sum('total_amount'))
        .order_by('-total')[:5]
    )
    return {
        'labels': [r['supplier__name'] or '—' for r in rows],
        'data': [float(r['total'] or 0) for r in rows],
    }


def _top_articles_data():
    rows = (
        RequestLine.objects
        .values('article__name')
        .annotate(total=Sum('quantity'))
        .order_by('-total')[:5]
    )
    return {
        'labels': [r['article__name'] or '—' for r in rows],
        'data': [int(r['total']) for r in rows],
    }


def _req_donut(queryset, title):
    counts = _status_counts(queryset, ALL_REQUEST_STATUSES, REQUEST_STATUS_LABELS)
    return {
        'data': {'labels': [i['label'] for i in counts], 'data': [i['count'] for i in counts],
                 'colors': [_REQ_COLORS.get(i['status'], '#9ca3af') for i in counts]},
        'title': title,
    }


def _po_donut(title):
    counts = _status_counts(PurchaseOrder.objects.all(), ALL_PO_STATUSES, PO_STATUS_LABELS)
    return {
        'data': {'labels': [i['label'] for i in counts], 'data': [i['count'] for i in counts],
                 'colors': [_PO_COLORS.get(i['status'], '#9ca3af') for i in counts]},
        'title': title,
    }


def _chart_data(user):
    role = user.role

    if role == Role.DEMANDEUR:
        donut = _req_donut(PurchaseRequest.objects.filter(requester=user), 'Mes demandes par statut')
        return {'request_chart_data': donut['data'], 'donut_chart_title': donut['title'],
                'supplier_chart_data': {}, 'show_donut_chart': True, 'show_bar_chart': False,
                'top_articles_data': {}, 'show_articles_chart': False}

    if role == Role.VALIDATEUR:
        donut = _req_donut(PurchaseRequest.objects.all(), 'Répartition des demandes par statut')
        return {'request_chart_data': donut['data'], 'donut_chart_title': donut['title'],
                'supplier_chart_data': {}, 'show_donut_chart': True, 'show_bar_chart': False,
                'top_articles_data': {}, 'show_articles_chart': False}

    if role == Role.ACHETEUR:
        donut = _po_donut('Répartition des BCs par statut')
        return {'request_chart_data': donut['data'], 'donut_chart_title': donut['title'],
                'supplier_chart_data': _top_suppliers_data(), 'show_donut_chart': True, 'show_bar_chart': True,
                'top_articles_data': _top_articles_data(), 'show_articles_chart': True}

    if role == Role.MAGASINIER:
        return {'request_chart_data': {}, 'donut_chart_title': '',
                'supplier_chart_data': {}, 'show_donut_chart': False, 'show_bar_chart': False,
                'top_articles_data': {}, 'show_articles_chart': False}

    # ADMIN / DIRECTION
    donut = _req_donut(PurchaseRequest.objects.all(), 'Répartition des demandes par statut')
    return {'request_chart_data': donut['data'], 'donut_chart_title': donut['title'],
            'supplier_chart_data': _top_suppliers_data(), 'show_donut_chart': True, 'show_bar_chart': True,
            'top_articles_data': _top_articles_data(), 'show_articles_chart': True}


# ──────────────────────────────────────────────
# Recent activity helper
# ──────────────────────────────────────────────

def _req_activity(r):
    return {
        'date': r.updated_at,
        'user': r.requester.full_name if r.requester else '—',
        'action': f"Demande {r.code} — {REQUEST_STATUS_LABELS.get(r.status, r.status)}",
        'badge': REQUEST_STATUS_LABELS.get(r.status, r.status),
        'badge_color': _REQ_BADGE.get(r.status, 'secondary'),
    }


def _po_activity(po):
    return {
        'date': po.created_at,
        'user': po.supplier.name if po.supplier else '—',
        'action': f"BC {po.code} — {PO_STATUS_LABELS.get(po.status, po.status)}",
        'badge': PO_STATUS_LABELS.get(po.status, po.status),
        'badge_color': _PO_BADGE.get(po.status, 'secondary'),
    }


def _rec_activity(rec):
    return {
        'date': rec.received_at,
        'user': rec.receiver_name or '—',
        'action': f"Réception {rec.code}",
        'badge': 'Réceptionnée',
        'badge_color': 'success',
    }


_FAC_BADGE = {
    'EN_ATTENTE': 'warning',
    'VALIDEE':    'primary',
    'PAYEE':      'success',
    'REJETEE':    'danger',
}
_FAC_LABELS = dict(Facture.Statut.choices)


def _fac_activity(f):
    return {
        'date':        f.created_at,
        'user':        f.fournisseur.name if f.fournisseur else '—',
        'action':      f"Facture {f.reference} — {_FAC_LABELS.get(f.statut, f.statut)}",
        'badge':       _FAC_LABELS.get(f.statut, f.statut),
        'badge_color': _FAC_BADGE.get(f.statut, 'secondary'),
    }


def _recent_activities(user):
    role = user.role
    activities = []

    if role == Role.DEMANDEUR:
        for r in PurchaseRequest.objects.filter(requester=user).select_related('requester').order_by('-updated_at')[:10]:
            activities.append(_req_activity(r))

    elif role == Role.VALIDATEUR:
        for r in (PurchaseRequest.objects
                  .filter(status__in=['SOUMISE', 'VALIDEE', 'REJETEE', 'CONVERTIE'])
                  .select_related('requester').order_by('-updated_at')[:10]):
            activities.append(_req_activity(r))

    elif role == Role.ACHETEUR:
        for po in PurchaseOrder.objects.select_related('supplier').order_by('-created_at')[:7]:
            activities.append(_po_activity(po))
        for r in (PurchaseRequest.objects
                  .filter(status__in=['VALIDEE', 'CONVERTIE'])
                  .select_related('requester').order_by('-updated_at')[:5]):
            activities.append(_req_activity(r))

    elif role == Role.MAGASINIER:
        for rec in Reception.objects.order_by('-received_at')[:10]:
            activities.append(_rec_activity(rec))

    else:  # ADMIN / DIRECTION
        for r in PurchaseRequest.objects.select_related('requester').order_by('-updated_at')[:5]:
            activities.append(_req_activity(r))
        for po in PurchaseOrder.objects.select_related('supplier').order_by('-created_at')[:5]:
            activities.append(_po_activity(po))
        for rec in Reception.objects.order_by('-received_at')[:5]:
            activities.append(_rec_activity(rec))
        for f in Facture.objects.select_related('fournisseur').order_by('-created_at')[:5]:
            activities.append(_fac_activity(f))

    activities.sort(key=lambda x: x['date'], reverse=True)
    return activities[:5]


# ──────────────────────────────────────────────
# View
# ──────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'webapp/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'request_status_counts': None,
            'po_status_counts': None,
            'pending_validation_count': None,
            'validated_requests_count': None,
            'stock_alert_count': None,
            'receivable_po_count': None,
        })

        user = self.request.user
        role = user.role

        if role == Role.DEMANDEUR:
            context['request_status_counts'] = _status_counts(
                PurchaseRequest.objects.filter(requester=user),
                DEMANDEUR_REQUEST_STATUSES, REQUEST_STATUS_LABELS,
            )
        elif role == Role.VALIDATEUR:
            context['pending_validation_count'] = PurchaseRequest.objects.filter(
                status=PurchaseRequest.Status.SOUMISE
            ).count()
        elif role == Role.ACHETEUR:
            context['po_status_counts'] = _status_counts(
                PurchaseOrder.objects.all(), ALL_PO_STATUSES, PO_STATUS_LABELS,
            )
            context['validated_requests_count'] = PurchaseRequest.objects.filter(
                status=PurchaseRequest.Status.VALIDEE
            ).count()
        elif role == Role.MAGASINIER:
            context['stock_alert_count'] = Article.objects.filter(current_stock__lte=F('min_threshold')).count()
            context['receivable_po_count'] = PurchaseOrder.objects.filter(status__in=RECEIVABLE_STATUSES).count()
        elif role in (Role.ADMIN, Role.DIRECTION):
            context['request_status_counts'] = _status_counts(
                PurchaseRequest.objects.all(), ALL_REQUEST_STATUSES, REQUEST_STATUS_LABELS,
            )
            context['po_status_counts'] = _status_counts(
                PurchaseOrder.objects.all(), ALL_PO_STATUSES, PO_STATUS_LABELS,
            )
            context['stock_alert_count'] = Article.objects.filter(current_stock__lte=F('min_threshold')).count()

        context['alerts'] = _build_alerts(user, context)

        context['summary_kpis'] = _role_kpis(user)
        context.update(_chart_data(user))
        context['recent_activities'] = _recent_activities(user)
        context['user_role'] = str(role)

        return context
