from rest_framework.permissions import BasePermission, SAFE_METHODS

ADMIN      = 'ADMIN'
DEMANDEUR  = 'DEMANDEUR'
VALIDATEUR = 'VALIDATEUR'
ACHETEUR   = 'ACHETEUR'
MAGASINIER = 'MAGASINIER'
DIRECTION  = 'DIRECTION'


def _role(request, *roles):
    return request.user.is_authenticated and request.user.role in roles


# ── Gestion des utilisateurs ───────────────────────────────────────────────

class IsAdmin(BasePermission):
    """ADMIN uniquement."""
    def has_permission(self, request, view):
        return _role(request, ADMIN)


# ── Fournisseurs / Articles / Catégories ───────────────────────────────────

class IsAdminOrAcheteur(BasePermission):
    """ADMIN ou ACHETEUR — accès complet (lecture + écriture)."""
    def has_permission(self, request, view):
        return _role(request, ADMIN, ACHETEUR)


class IsAdminOrAcheteurReadAll(BasePermission):
    """Lecture : tout rôle authentifié (y.c. DIRECTION).
    Écriture : ADMIN ou ACHETEUR uniquement."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return _role(request, ADMIN, ACHETEUR)


# ── Consultations / Bons de commande ──────────────────────────────────────

class IsAdminOrAcheteurOrValidateur(BasePermission):
    """ADMIN, ACHETEUR ou VALIDATEUR.
    Utilisé pour les transitions de statut des BCs (approbation VALIDATEUR)."""
    def has_permission(self, request, view):
        return _role(request, ADMIN, ACHETEUR, VALIDATEUR)


class IsAdminOrAcheteurOrValidateurReadAll(BasePermission):
    """Lecture : tout rôle authentifié.
    Écriture (create / update) : ADMIN ou ACHETEUR.
    Les transitions de statut (endpoint dédié) sont gérées séparément."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return _role(request, ADMIN, ACHETEUR)


# ── Réceptions / Stock ────────────────────────────────────────────────────

class IsAdminOrMagasinier(BasePermission):
    """ADMIN ou MAGASINIER — accès complet aux réceptions et mouvements."""
    def has_permission(self, request, view):
        return _role(request, ADMIN, MAGASINIER)


class IsAdminOrMagasinierReadAll(BasePermission):
    """Lecture : tout rôle authentifié.
    Écriture : ADMIN ou MAGASINIER uniquement."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return _role(request, ADMIN, MAGASINIER)


# ── Demandes d'achat ──────────────────────────────────────────────────────

class IsAdminOrDemandeur(BasePermission):
    """ADMIN ou DEMANDEUR (soumettre une DA)."""
    def has_permission(self, request, view):
        return _role(request, ADMIN, DEMANDEUR)


class IsAdminOrValidateur(BasePermission):
    """ADMIN ou VALIDATEUR (approuver / rejeter une DA)."""
    def has_permission(self, request, view):
        return _role(request, ADMIN, VALIDATEUR)


class CanManageRequests(BasePermission):
    """Lecture : tout rôle authentifié (DIRECTION incluse).
    Création / modification : ADMIN ou DEMANDEUR uniquement.
    (VALIDATEUR approuve via les endpoints dédiés /approve/ et /reject/.)"""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return _role(request, ADMIN, DEMANDEUR)
