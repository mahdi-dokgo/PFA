from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from apps.requests_app import services
from apps.requests_app.models import PurchaseRequest
from apps.users.models import Role

from ..forms.purchase_requests import (
    ApprovalCommentForm,
    PurchaseRequestForm,
    RequestLineFormSet,
)
from ..mixins import RoleRequiredMixin


class PurchaseRequestListView(LoginRequiredMixin, ListView):
    template_name = 'webapp/purchase_requests/list.html'
    context_object_name = 'requests'
    paginate_by = 20

    def get_queryset(self):
        qs = PurchaseRequest.objects.select_related('requester').order_by('-created_at')
        if self.request.user.role == Role.DEMANDEUR:
            qs = qs.filter(requester=self.request.user)

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(code__icontains=search)

        return qs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['status_choices'] = PurchaseRequest.Status.choices
        data['current_status'] = self.request.GET.get('status', '')
        data['search'] = self.request.GET.get('q', '')
        return data


class PurchaseRequestCreateView(RoleRequiredMixin, CreateView):
    model = PurchaseRequest
    form_class = PurchaseRequestForm
    template_name = 'webapp/purchase_requests/form.html'
    allowed_roles = [Role.ADMIN, Role.DEMANDEUR]

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if 'formset' not in data:
            data['formset'] = RequestLineFormSet(self.request.POST or None, instance=self.object)
        return data

    def form_valid(self, form):
        with transaction.atomic():
            form.instance.requester = self.request.user
            self.object = form.save()
            formset = RequestLineFormSet(self.request.POST, instance=self.object)
            if not formset.is_valid():
                transaction.set_rollback(True)
                self.object = None
                return self.render_to_response(self.get_context_data(form=form, formset=formset))
            formset.save()
            services.add_audit_entry(self.object, self.request.user, 'Création')

        messages.success(self.request, f"Demande {self.object.code} créée avec succès.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('webapp:request_detail', kwargs={'pk': self.object.pk})


class PurchaseRequestDetailView(LoginRequiredMixin, DetailView):
    template_name = 'webapp/purchase_requests/detail.html'
    context_object_name = 'purchase_request'

    def get_queryset(self):
        qs = PurchaseRequest.objects.select_related('requester').prefetch_related('lines__article', 'audit')
        if self.request.user.role == Role.DEMANDEUR:
            qs = qs.filter(requester=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['approval_form'] = ApprovalCommentForm()
        return data


class PurchaseRequestSubmitView(RoleRequiredMixin, View):
    allowed_roles = [Role.ADMIN, Role.DEMANDEUR]

    def post(self, request, pk):
        qs = PurchaseRequest.objects.all()
        if request.user.role == Role.DEMANDEUR:
            qs = qs.filter(requester=request.user)
        pr = get_object_or_404(qs, pk=pk, status=PurchaseRequest.Status.BROUILLON)
        services.submit_purchase_request(pr, request.user)
        messages.success(request, f"Demande {pr.code} soumise pour validation.")
        return redirect('webapp:request_detail', pk=pr.pk)


class PurchaseRequestApproveView(RoleRequiredMixin, View):
    allowed_roles = [Role.ADMIN, Role.VALIDATEUR]

    def post(self, request, pk):
        pr = get_object_or_404(PurchaseRequest, pk=pk, status=PurchaseRequest.Status.SOUMISE)
        comment = request.POST.get('comment', '')
        services.approve_purchase_request(pr, request.user, comment)
        messages.success(request, f"Demande {pr.code} validée.")
        return redirect('webapp:request_detail', pk=pr.pk)


class PurchaseRequestRejectView(RoleRequiredMixin, View):
    allowed_roles = [Role.ADMIN, Role.VALIDATEUR]

    def post(self, request, pk):
        pr = get_object_or_404(PurchaseRequest, pk=pk, status=PurchaseRequest.Status.SOUMISE)
        comment = request.POST.get('comment', '')
        services.reject_purchase_request(pr, request.user, comment)
        messages.warning(request, f"Demande {pr.code} rejetée.")
        return redirect('webapp:request_detail', pk=pr.pk)


_EXPORT_ROLES = [Role.ADMIN, Role.ACHETEUR, Role.DIRECTION]


class ExportDaExcelView(RoleRequiredMixin, View):
    allowed_roles = _EXPORT_ROLES

    def get(self, request):
        from datetime import date
        from ..utils.exports import export_excel

        qs = PurchaseRequest.objects.select_related('requester').order_by('-created_at')
        headers = ['Référence', 'Demandeur', 'Priorité', 'Statut', 'Date de création', 'Montant estimé']
        rows = [
            [
                pr.code,
                pr.requester.full_name,
                pr.get_priority_display(),
                pr.get_status_display(),
                pr.created_at.strftime('%d/%m/%Y'),
                '—',
            ]
            for pr in qs
        ]
        return export_excel(f"demandes_achat_{date.today()}.xlsx", headers, rows, title="Demandes d'achat")


class ExportDaPdfView(RoleRequiredMixin, View):
    allowed_roles = _EXPORT_ROLES

    def get(self, request):
        from datetime import date
        from ..utils.exports import export_pdf

        qs = PurchaseRequest.objects.select_related('requester').order_by('-created_at')
        headers = ['Référence', 'Demandeur', 'Priorité', 'Statut', 'Date de création', 'Montant estimé']
        rows = [
            [
                pr.code,
                pr.requester.full_name,
                pr.get_priority_display(),
                pr.get_status_display(),
                pr.created_at.strftime('%d/%m/%Y'),
                '—',
            ]
            for pr in qs
        ]
        return export_pdf(
            filename=f"demandes_achat_{date.today()}.pdf",
            title="Demandes d'achat",
            headers=headers,
            rows=rows,
            subtitle=f"Exporté le {date.today().strftime('%d/%m/%Y')}",
        )
