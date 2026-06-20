from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.db.models import Count, Sum
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.orders.models import PurchaseOrder

from apps.suppliers.models import Supplier
from apps.users.models import Role

from ..forms.suppliers import SupplierForm
from ..mixins import RoleRequiredMixin


class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'webapp/suppliers/list.html'
    context_object_name = 'suppliers'
    paginate_by = 20

    def get_queryset(self):
        qs = Supplier.objects.all().order_by('name')
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(name__icontains=search)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['status_choices'] = Supplier.Status.choices
        data['current_status'] = self.request.GET.get('status', '')
        data['search'] = self.request.GET.get('q', '')
        return data


class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = 'webapp/suppliers/detail.html'
    context_object_name = 'supplier'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        supplier = self.object
        orders = (
            PurchaseOrder.objects
            .filter(supplier=supplier)
            .select_related('request')
            .order_by('-created_at')
        )
        data['orders'] = orders
        stats = orders.exclude(status='ANNULEE').aggregate(
            total_bc=Count('id'),
            total_depenses=Sum('total_amount'),
        )
        data['total_bc'] = stats['total_bc'] or 0
        data['total_depenses'] = stats['total_depenses'] or 0
        data['articles'] = supplier.articles.all().order_by('reference')
        return data


class SupplierCreateView(RoleRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'webapp/suppliers/form.html'
    allowed_roles = [Role.ADMIN, Role.ACHETEUR]
    success_url = reverse_lazy('webapp:supplier_list')

    def form_valid(self, form):
        messages.success(self.request, f"Fournisseur « {form.instance.name} » créé avec succès.")
        return super().form_valid(form)


class SupplierUpdateView(RoleRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'webapp/suppliers/form.html'
    allowed_roles = [Role.ADMIN, Role.ACHETEUR]
    success_url = reverse_lazy('webapp:supplier_list')

    def form_valid(self, form):
        messages.success(self.request, f"Fournisseur « {form.instance.name} » mis à jour.")
        return super().form_valid(form)


class SupplierArchiveToggleView(RoleRequiredMixin, View):
    allowed_roles = [Role.ADMIN, Role.ACHETEUR]

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        if supplier.status == Supplier.Status.ACTIVE:
            supplier.status = Supplier.Status.ARCHIVED
            messages.success(request, f"Fournisseur « {supplier.name} » archivé.")
        else:
            supplier.status = Supplier.Status.ACTIVE
            messages.success(request, f"Fournisseur « {supplier.name} » réactivé.")
        supplier.save()
        return redirect('webapp:supplier_list')
