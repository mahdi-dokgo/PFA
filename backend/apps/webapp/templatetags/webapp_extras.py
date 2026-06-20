from django import template

from apps.receptions.services import compute_reception_line_gap

register = template.Library()

STATUS_COLORS = {
    # Demandes d'achat
    'BROUILLON': 'secondary',
    'SOUMISE': 'warning',
    'VALIDEE': 'success',
    'REJETEE': 'danger',
    'CONVERTIE': 'info',
    # Bons de commande
    'APPROUVEE': 'success',
    'ENVOYEE': 'primary',
    'PARTIELLEMENT_RECUE': 'warning',
    'RECUE': 'success',
    'CLOTUREE': 'secondary',
    'ANNULEE': 'danger',
    # Fournisseurs
    'active': 'success',
    'archived': 'secondary',
    # Factures
    'EN_ATTENTE': 'warning',
    'PAYEE': 'success',
    # Consultations
    'OUVERTE': 'success',
    'INVITE': 'warning',
    'PROPOSITION_RECUE': 'info',
    'RETENU': 'success',
    'ELIMINE': 'secondary',
}


STATUS_ICONS = {
    # Demandes d'achat
    'BROUILLON': 'bi-file-earmark',
    'SOUMISE': 'bi-hourglass-split',
    'VALIDEE': 'bi-check-circle',
    'REJETEE': 'bi-x-circle',
    'CONVERTIE': 'bi-arrow-right-circle',
    # Bons de commande
    'APPROUVEE': 'bi-check-circle',
    'ENVOYEE': 'bi-send',
    'PARTIELLEMENT_RECUE': 'bi-box-arrow-in-down',
    'RECUE': 'bi-box-seam',
    'CLOTUREE': 'bi-x-circle',
    'ANNULEE': 'bi-x-circle',
}


@register.filter
def status_badge(value):
    """Retourne la classe couleur Bootstrap correspondant à un statut."""
    return STATUS_COLORS.get(value, 'secondary')


@register.filter
def status_icon(value):
    """Retourne l'icône Bootstrap Icons correspondant à un statut."""
    return STATUS_ICONS.get(value, 'bi-circle')


@register.filter
def initials(full_name):
    """Retourne les initiales (1-2 lettres) à partir d'un nom complet."""
    parts = full_name.split()
    if not parts:
        return ''
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


@register.filter
def multiply(value, arg):
    """Multiplie deux valeurs (ex : quantité * prix unitaire)."""
    return value * arg


@register.filter
def has_gap(reception):
    """Indique si une réception laisse un écart (quantité restant à recevoir > 0)."""
    return any(compute_reception_line_gap(line) > 0 for line in reception.lines.all())


@register.simple_tag(takes_context=True)
def querystring_replace(context, **kwargs):
    """Reconstruit la querystring courante en remplaçant/ajoutant les paramètres donnés."""
    request = context['request']
    params = request.GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return params.urlencode()
