import json

from django.contrib import messages
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from apps.factures.models import Facture, LigneFacture
from apps.orders.models import PurchaseOrder
from apps.receptions.models import Reception, ReceptionLine
from apps.users.models import Role

from apps.audit.utils import log_action
from ..forms.factures import FactureForm, FactureRejeterForm, LigneFactureFormSet
from ..mixins import RoleRequiredMixin

_VIEW_ROLES  = [Role.ADMIN, Role.ACHETEUR, Role.VALIDATEUR, Role.DIRECTION]
_WRITE_ROLES = [Role.ADMIN, Role.ACHETEUR]
_ADMIN_ROLES = [Role.ADMIN]

_FORMSET_PREFIX = 'lignes'


class FactureListView(RoleRequiredMixin, ListView):
    template_name       = 'webapp/factures/list.html'
    context_object_name = 'factures'
    paginate_by         = 20
    allowed_roles       = _VIEW_ROLES

    def get_queryset(self):
        qs = (
            Facture.objects
            .select_related('fournisseur', 'bon_commande', 'created_by')
            .order_by('-created_at')
        )
        statut = self.request.GET.get('statut')
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['statut_choices'] = Facture.Statut.choices
        data['current_statut'] = self.request.GET.get('statut', '')
        return data


class FactureCreateView(RoleRequiredMixin, View):
    allowed_roles = _WRITE_ROLES
    template_name = 'webapp/factures/create.html'

    def _bc_amounts(self):
        return {
            str(po['pk']): float(po['total_amount'])
            for po in PurchaseOrder.objects.exclude(status='ANNULEE').values('pk', 'total_amount')
        }

    def _ctx(self, form, formset):
        return {
            'form': form,
            'formset': formset,
            'bc_amounts_json': json.dumps(self._bc_amounts()),
        }

    def get(self, request):
        form = FactureForm()
        formset = LigneFactureFormSet(
            queryset=LigneFacture.objects.none(),
            prefix=_FORMSET_PREFIX,
        )
        return render(request, self.template_name, self._ctx(form, formset))

    def post(self, request):
        form = FactureForm(request.POST)
        formset = LigneFactureFormSet(
            request.POST,
            queryset=LigneFacture.objects.none(),
            prefix=_FORMSET_PREFIX,
        )
        if form.is_valid() and formset.is_valid():
            facture = form.save(commit=False)
            facture.created_by = request.user
            facture.save()
            lignes = formset.save(commit=False)
            for ligne in lignes:
                ligne.facture = facture
                ligne.save()
            log_action('FACTURE', facture.reference, 'Création', user=request.user,
                       detail=f"Fournisseur : {facture.fournisseur.name} | Montant TTC : {facture.montant_ttc} DH")
            messages.success(request, f"Facture {facture.reference} créée avec succès.")
            return redirect('webapp:facture_detail', pk=facture.pk)
        return render(request, self.template_name, self._ctx(form, formset))


class FactureDetailView(RoleRequiredMixin, DetailView):
    model               = Facture
    template_name       = 'webapp/factures/detail.html'
    context_object_name = 'facture'
    allowed_roles       = _VIEW_ROLES

    def get_queryset(self):
        return Facture.objects.select_related(
            'fournisseur', 'bon_commande__supplier', 'created_by',
        ).prefetch_related('lignes')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        facture = self.object
        receptions = []
        reception_total = 0
        if facture.bon_commande:
            receptions = list(
                Reception.objects
                .filter(po=facture.bon_commande)
                .order_by('-received_at')
            )
            reception_total = (
                ReceptionLine.objects
                .filter(reception__po=facture.bon_commande)
                .aggregate(
                    total=Sum(
                        ExpressionWrapper(
                            F('received_quantity') * F('po_line__unit_price'),
                            output_field=DecimalField(max_digits=14, decimal_places=2),
                        )
                    )
                )['total'] or 0
            )
        data['receptions']      = receptions
        data['reception_total'] = reception_total
        data['lignes']          = facture.lignes.all()
        return data


class FactureValiderView(RoleRequiredMixin, View):
    allowed_roles = _WRITE_ROLES

    def post(self, request, pk):
        facture = get_object_or_404(Facture, pk=pk, statut=Facture.Statut.EN_ATTENTE)
        facture.statut = Facture.Statut.VALIDEE
        facture.save()
        log_action('FACTURE', facture.reference, 'Validation', user=request.user)
        messages.success(request, f"Facture {facture.reference} validée.")
        return redirect('webapp:facture_detail', pk=pk)


class FacturePayerView(RoleRequiredMixin, View):
    allowed_roles = _ADMIN_ROLES

    def post(self, request, pk):
        facture = get_object_or_404(Facture, pk=pk, statut=Facture.Statut.VALIDEE)
        facture.statut = Facture.Statut.PAYEE
        facture.save()
        log_action('FACTURE', facture.reference, 'Paiement', user=request.user)
        messages.success(request, f"Facture {facture.reference} marquée comme payée.")
        return redirect('webapp:facture_detail', pk=pk)


class FactureRejeterView(RoleRequiredMixin, View):
    allowed_roles = _WRITE_ROLES
    template_name = 'webapp/factures/rejeter_form.html'

    def get(self, request, pk):
        facture = get_object_or_404(Facture, pk=pk)
        if facture.statut == Facture.Statut.PAYEE:
            messages.error(request, "Impossible de rejeter une facture déjà payée.")
            return redirect('webapp:facture_detail', pk=pk)
        form = FactureRejeterForm()
        return render(request, self.template_name, {'form': form, 'facture': facture})

    def post(self, request, pk):
        facture = get_object_or_404(Facture, pk=pk)
        if facture.statut == Facture.Statut.PAYEE:
            messages.error(request, "Impossible de rejeter une facture déjà payée.")
            return redirect('webapp:facture_detail', pk=pk)
        form = FactureRejeterForm(request.POST)
        if form.is_valid():
            facture.statut      = Facture.Statut.REJETEE
            facture.commentaire = form.cleaned_data['commentaire']
            facture.save()
            log_action('FACTURE', facture.reference, 'Rejet', user=request.user,
                       detail=facture.commentaire)
            messages.success(request, f"Facture {facture.reference} rejetée.")
            return redirect('webapp:facture_detail', pk=pk)
        return render(request, self.template_name, {'form': form, 'facture': facture})


_EXPORT_ROLES = [Role.ADMIN, Role.ACHETEUR, Role.DIRECTION]


class ExportFacturesExcelView(RoleRequiredMixin, View):
    allowed_roles = _EXPORT_ROLES

    def get(self, request):
        from datetime import date
        from ..utils.exports import export_excel

        qs = Facture.objects.select_related('fournisseur', 'bon_commande', 'created_by').order_by('-created_at')
        headers = ['Référence', 'Fournisseur', 'BC liée', 'Date facture', 'Échéance',
                   'Montant HT (DH)', 'Montant TTC (DH)', 'Statut', 'Écart']
        rows = [
            [
                f.reference,
                f.fournisseur.name,
                f.bon_commande.code if f.bon_commande else '—',
                f.date_facture.strftime('%d/%m/%Y'),
                f.date_echeance.strftime('%d/%m/%Y'),
                f'{f.montant_ht:.2f}',
                f'{f.montant_ttc:.2f}',
                f.get_statut_display(),
                'Oui' if f.ecart_detected else 'Non',
            ]
            for f in qs
        ]
        return export_excel(f"factures_{date.today()}.xlsx", headers, rows, title='Factures fournisseurs')


class ExportFacturesPdfView(RoleRequiredMixin, View):
    allowed_roles = _EXPORT_ROLES

    def get(self, request):
        from datetime import date
        from ..utils.exports import export_pdf

        qs = Facture.objects.select_related('fournisseur', 'bon_commande').order_by('-created_at')
        headers = ['Référence', 'Fournisseur', 'BC liée', 'Date facture',
                   'Montant HT', 'Montant TTC', 'Statut', 'Écart']
        rows = [
            [
                f.reference,
                f.fournisseur.name,
                f.bon_commande.code if f.bon_commande else '—',
                f.date_facture.strftime('%d/%m/%Y'),
                f'{f.montant_ht:.2f} DH',
                f'{f.montant_ttc:.2f} DH',
                f.get_statut_display(),
                'Oui' if f.ecart_detected else 'Non',
            ]
            for f in qs
        ]
        return export_pdf(
            filename=f"factures_{date.today()}.pdf",
            title='Factures fournisseurs',
            headers=headers,
            rows=rows,
            subtitle=f"Exporté le {date.today().strftime('%d/%m/%Y')}",
        )
