from django.views.generic import ListView, CreateView, UpdateView, View
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

from apps.users.models import User, Role
from apps.webapp.mixins import RoleRequiredMixin
from apps.webapp.forms.users import UserCreateForm, UserUpdateForm


class UserListView(RoleRequiredMixin, ListView):
    model = User
    template_name = 'webapp/users/list.html'
    context_object_name = 'users'
    allowed_roles = [Role.ADMIN]

    def get_queryset(self):
        return User.objects.all().order_by('full_name')


class UserCreateView(RoleRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = 'webapp/users/form.html'
    success_url = reverse_lazy('webapp:user_list')
    allowed_roles = [Role.ADMIN]

    def form_valid(self, form):
        messages.success(self.request, "Utilisateur créé avec succès.")
        return super().form_valid(form)


class UserUpdateView(RoleRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'webapp/users/form.html'
    success_url = reverse_lazy('webapp:user_list')
    allowed_roles = [Role.ADMIN]

    def form_valid(self, form):
        messages.success(self.request, "Utilisateur modifié avec succès.")
        return super().form_valid(form)


class UserToggleActiveView(RoleRequiredMixin, View):
    allowed_roles = [Role.ADMIN]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, "Vous ne pouvez pas désactiver votre propre compte.")
            return redirect('webapp:user_list')
        user.is_active = not user.is_active
        user.save()
        etat = "activé" if user.is_active else "désactivé"
        messages.success(request, f"Compte {user.full_name} {etat}.")
        return redirect('webapp:user_list')


class UserDeleteView(RoleRequiredMixin, View):
    allowed_roles = [Role.ADMIN]

    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            return redirect('webapp:user_list')
        if user.role == Role.ADMIN and User.objects.filter(role=Role.ADMIN, is_active=True).count() <= 1:
            messages.error(request, "Impossible de supprimer le dernier administrateur actif.")
            return redirect('webapp:user_list')
        nom = user.full_name
        user.delete()
        messages.success(request, f"Utilisateur {nom} supprimé.")
        return redirect('webapp:user_list')
