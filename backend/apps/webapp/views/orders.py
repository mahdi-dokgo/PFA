from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from apps.orders import services
from apps.orders.models import PurchaseOrder
from apps.requests_app.models import PurchaseRequest
from apps.users.models import Role

from apps.audit.utils import log_action
from ..forms.orders import POLineFormSet, POStatusTransitionForm, PurchaseOrderForm
from ..mixins import RoleRequiredMixin


class PurchaseOrderListView(LoginRequiredMixin, ListView):
    template_name = 'webapp/orders/list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        qs = PurchaseOrder.objects.select_related('supplier', 'request').order_by('-created_at')

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(code__icontains=search)

        return qs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['status_choices'] = PurchaseOrder.Status.choices
        data['current_status'] = self.request.GET.get('status', '')
        data['search'] = self.request.GET.get('q', '')
        return data


class PurchaseOrderCreateView(RoleRequiredMixin, CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'webapp/orders/form.html'
    allowed_roles = [Role.ADMIN, Role.ACHETEUR]

    def get_initial(self):
        initial = super().get_initial()
        if self.request.method == 'GET':
            from_request_id = self.request.GET.get('from_request')
            if from_request_id:
                pr = PurchaseRequest.objects.filter(
                    pk=from_request_id, status=PurchaseRequest.Status.VALIDEE
                ).first()
                if pr:
                    initial['request'] = pr.pk
        return initial

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if 'formset' not in data:
            formset_kwargs = {'instance': PurchaseOrder()}
            if self.request.method == 'GET':
                from_request_id = self.request.GET.get('from_request')
                if from_request_id:
                    pr = PurchaseRequest.objects.filter(
                        pk=from_request_id, status=PurchaseRequest.Status.VALIDEE
                    ).prefetch_related('lines__article').first()
                    if pr:
                        formset_kwargs['initial'] = [
                            {'article': line.article_id, 'quantity': line.quantity}
                            for line in pr.lines.all()
                        ]
            data['formset'] = POLineFormSet(self.request.POST or None, **formset_kwargs)
        return data

    def form_valid(self, form):
        formset = POLineFormSet(self.request.POST, instance=PurchaseOrder())
        if not formset.is_valid():
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        lines_data = []
        total_amount = Decimal('0')
        for line_form in formset:
            if not line_form.cleaned_data:
                continue
            article = line_form.cleaned_data.get('article')
            if not article:
                continue
            quantity = line_form.cleaned_data['quantity']
            unit_price = line_form.cleaned_data['unit_price']
            lines_data.append({'article': article, 'quantity': quantity, 'unit_price': unit_price})
            total_amount += quantity * unit_price

        try:
            self.object = services.create_purchase_order_with_lines(
                supplier=form.cleaned_data['supplier'],
                request=form.cleaned_data.get('request'),
                expected_date=form.cleaned_data['expected_date'],
                total_amount=total_amount,
                lines_data=lines_data,
            )
        except DjangoValidationError as exc:
            form.add_error('request', exc.messages)
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        messages.success(self.request, f"Bon de commande {self.object.code} créé avec succès.")
        log_action('BC', self.object.code, 'Création', user=self.request.user,
                   detail=f"Fournisseur : {self.object.supplier.name} | Montant : {self.object.total_amount} DH")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('webapp:po_detail', kwargs={'pk': self.object.pk})


class PurchaseOrderDetailView(LoginRequiredMixin, DetailView):
    template_name = 'webapp/orders/detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return PurchaseOrder.objects.select_related('supplier', 'request').prefetch_related('lines__article')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['transition_form'] = POStatusTransitionForm(initial={'status': self.object.status})
        return data


class PurchaseOrderTransitionView(RoleRequiredMixin, View):
    allowed_roles = [Role.ADMIN, Role.ACHETEUR, Role.VALIDATEUR]

    def post(self, request, pk):
        po = get_object_or_404(PurchaseOrder, pk=pk)
        form = POStatusTransitionForm(request.POST)
        if form.is_valid():
            try:
                services.transition_purchase_order(po, form.cleaned_data['status'])
                log_action('BC', po.code, f"Transition → {po.get_status_display()}", user=request.user)
                messages.success(request, f"Statut du bon {po.code} mis à jour : {po.get_status_display()}.")
            except DjangoValidationError as exc:
                messages.error(request, exc.message)
        else:
            messages.error(request, "Statut invalide.")
        return redirect('webapp:po_detail', pk=po.pk)


_EXPORT_ROLES = [Role.ADMIN, Role.ACHETEUR, Role.DIRECTION]


class ExportBcExcelView(RoleRequiredMixin, View):
    allowed_roles = _EXPORT_ROLES

    def get(self, request):
        from datetime import date
        from ..utils.exports import export_excel

        qs = PurchaseOrder.objects.select_related('supplier', 'request').order_by('-created_at')
        headers = ['Référence', 'Fournisseur', 'DA liée', 'Montant TTC (DH)', 'Statut',
                   'Date de création', 'Livraison prévue']
        rows = [
            [
                po.code,
                po.supplier.name,
                po.request.code if po.request else '—',
                f'{po.total_amount:.2f}',
                po.get_status_display(),
                po.created_at.strftime('%d/%m/%Y'),
                po.expected_date.strftime('%d/%m/%Y'),
            ]
            for po in qs
        ]
        return export_excel(f"bons_commande_{date.today()}.xlsx", headers, rows, title='Bons de commande')


class ExportBcPdfView(RoleRequiredMixin, View):
    allowed_roles = _EXPORT_ROLES

    def get(self, request):
        from datetime import date
        from ..utils.exports import export_pdf

        qs = PurchaseOrder.objects.select_related('supplier', 'request').order_by('-created_at')
        headers = ['Référence', 'Fournisseur', 'DA liée', 'Montant TTC (DH)', 'Statut',
                   'Date création', 'Livraison prévue']
        rows = [
            [
                po.code,
                po.supplier.name,
                po.request.code if po.request else '—',
                f'{po.total_amount:.2f}',
                po.get_status_display(),
                po.created_at.strftime('%d/%m/%Y'),
                po.expected_date.strftime('%d/%m/%Y'),
            ]
            for po in qs
        ]
        return export_pdf(
            filename=f"bons_commande_{date.today()}.pdf",
            title='Bons de commande',
            headers=headers,
            rows=rows,
            subtitle=f"Exporté le {date.today().strftime('%d/%m/%Y')}",
        )


class ExportBcDetailPdfView(RoleRequiredMixin, View):
    allowed_roles = _EXPORT_ROLES

    def get(self, request, pk):
        from ..utils.exports import export_bc_detail_pdf

        po = get_object_or_404(
            PurchaseOrder.objects.select_related('supplier', 'request')
                                 .prefetch_related('lines__article'),
            pk=pk,
        )
        return export_bc_detail_pdf(po)
