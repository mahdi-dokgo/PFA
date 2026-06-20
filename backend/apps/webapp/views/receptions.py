from apps.audit.utils import log_action
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from apps.orders.models import PurchaseOrder
from apps.receptions import services
from apps.receptions.models import Reception
from apps.users.models import Role

from ..forms.receptions import (
    RECEIVABLE_STATUSES,
    ReceptionLineFormSet,
    ReceptionNotesForm,
    ReceptionPOSelectForm,
)
from ..mixins import RoleRequiredMixin


def _receivable_po_or_404(pk):
    return get_object_or_404(
        PurchaseOrder.objects.filter(status__in=RECEIVABLE_STATUSES).select_related('supplier'),
        pk=pk,
    )


def _lines_with_remaining(po):
    lines = []
    for line in po.lines.select_related('article').order_by('id'):
        remaining = line.quantity - line.received_quantity
        if remaining > 0:
            lines.append((line, remaining))
    return lines


class ReceptionListView(LoginRequiredMixin, ListView):
    template_name = 'webapp/receptions/list.html'
    context_object_name = 'receptions'
    paginate_by = 20

    def get_queryset(self):
        return Reception.objects.select_related('po').prefetch_related('lines__article').order_by('-received_at')


class ReceptionDetailView(LoginRequiredMixin, DetailView):
    template_name = 'webapp/receptions/detail.html'
    context_object_name = 'reception'

    def get_queryset(self):
        return Reception.objects.select_related('po').prefetch_related('lines__article')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for line in self.object.lines.all():
            line.gap = services.compute_reception_line_gap(line)
        return context


class ReceptionCreateView(RoleRequiredMixin, View):
    allowed_roles = [Role.ADMIN, Role.MAGASINIER]
    template_name = 'webapp/receptions/form.html'

    def get(self, request):
        context = {'po_select_form': ReceptionPOSelectForm()}

        po_id = request.GET.get('po')
        if po_id:
            po = _receivable_po_or_404(po_id)
            lines = _lines_with_remaining(po)
            formset = ReceptionLineFormSet(initial=[
                {'po_line_id': line.pk, 'remaining_quantity': remaining, 'received_quantity': remaining}
                for line, remaining in lines
            ])
            pairs = [
                (po_line, remaining, line_form)
                for (po_line, remaining), line_form in zip(lines, formset)
            ]
            for po_line, remaining, line_form in pairs:
                line_form.fields['received_quantity'].widget.attrs['max'] = remaining

            context.update({
                'po': po,
                'formset': formset,
                'notes_form': ReceptionNotesForm(),
                'lines_with_forms': pairs,
            })
        return render(request, self.template_name, context)

    def post(self, request):
        po = _receivable_po_or_404(request.POST.get('po'))
        po_lines = {line.pk: line for line in po.lines.select_related('article').all()}

        formset = ReceptionLineFormSet(request.POST)
        notes_form = ReceptionNotesForm(request.POST)

        if formset.is_valid() and notes_form.is_valid():
            lines_data = []
            for line_form in formset:
                received_quantity = line_form.cleaned_data.get('received_quantity') or 0
                if received_quantity <= 0:
                    continue
                po_line = po_lines.get(line_form.cleaned_data['po_line_id'])
                lines_data.append({
                    'po_line': po_line,
                    'article': po_line.article,
                    'ordered_quantity': po_line.quantity,
                    'received_quantity': received_quantity,
                })

            if not lines_data:
                messages.error(request, "Veuillez indiquer au moins une quantité reçue.")
            else:
                reception = services.create_reception_with_lines(
                    po=po,
                    receiver=request.user,
                    receiver_name=request.user.full_name,
                    notes=notes_form.cleaned_data['notes'],
                    lines_data=lines_data,
                )
                log_action('RECEPTION', reception.code, 'Réception enregistrée', user=request.user,
                           detail=f"BC : {po.code}")
                messages.success(request, f"Réception {reception.code} enregistrée — stock mis à jour.")
                return redirect('webapp:reception_detail', pk=reception.pk)

        lines = _lines_with_remaining(po)
        pairs = [
            (po_line, remaining, line_form)
            for (po_line, remaining), line_form in zip(lines, formset)
        ]
        for po_line, remaining, line_form in pairs:
            line_form.fields['received_quantity'].widget.attrs['max'] = remaining

        context = {
            'po_select_form': ReceptionPOSelectForm(),
            'po': po,
            'formset': formset,
            'notes_form': notes_form,
            'lines_with_forms': pairs,
        }
        return render(request, self.template_name, context)
