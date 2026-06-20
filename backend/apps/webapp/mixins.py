from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restreint l'accès à une vue aux utilisateurs dont le role figure dans allowed_roles.

    Usage:
        class MyView(RoleRequiredMixin, ListView):
            allowed_roles = ['ADMIN', 'ACHETEUR']
    """
    allowed_roles = ()

    def test_func(self):
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "Vous n'avez pas la permission d'accéder à cette page.")
        return redirect('webapp:dashboard')
