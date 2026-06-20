from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from apps.consultations.models import Consultation, ConsultationFournisseur, Proposition
from apps.requests_app.models import PurchaseRequest
from apps.suppliers.models import Supplier
from apps.users.models import Role

from ..forms.consultations import ConsultationForm, PropositionForm
from ..mixins import RoleRequiredMixin

_VIEW_ROLES    = [Role.ADMIN, Role.ACHETEUR, Role.VALIDATEUR, Role.DIRECTION]
_WRITE_ROLES   = [Role.ADMIN, Role.ACHETEUR]


class ConsultationListView(RoleRequiredMixin, ListView):
    template_name      = 'webapp/consultations/list.html'
    context_object_name = 'consultations'
    paginate_by        = 20
    allowed_roles      = _VIEW_ROLES

    def get_queryset(self):
        qs = (
            Consultation.objects
            .select_related('created_by', 'demande_achat')
            .prefetch_related('fournisseurs')
            .order_by('-created_at')
        )
        statut = self.request.GET.get('statut')
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['statut_choices'] = Consultation.Statut.choices
        data['current_statut'] = self.request.GET.get('statut', '')
        return data


class ConsultationCreateView(RoleRequiredMixin, CreateView):
    model         = Consultation
    form_class    = ConsultationForm
    template_name = 'webapp/consultations/create.html'
    allowed_roles = _WRITE_ROLES

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['fournisseurs'] = Supplier.objects.filter(status='active').order_by('name')
        return data

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        consultation = form.save()
        for fid in self.request.POST.getlist('fournisseurs'):
            try:
                f = Supplier.objects.get(pk=fid, status='active')
                ConsultationFournisseur.objects.create(consultation=consultation, fournisseur=f)
            except Supplier.DoesNotExist:
                pass
        messages.success(self.request, f"Consultation {consultation.code} créée avec succès.")
        return redirect('webapp:consultation_detail', pk=consultation.pk)


class ConsultationDetailView(RoleRequiredMixin, DetailView):
    model               = Consultation
    template_name       = 'webapp/consultations/detail.html'
    context_object_name = 'consultation'
    allowed_roles       = _VIEW_ROLES

    def get_queryset(self):
        return Consultation.objects.select_related(
            'created_by', 'demande_achat'
        ).prefetch_related(
            'fournisseurs__fournisseur',
            'fournisseurs__proposition',
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        cf_list = list(
            self.object.fournisseurs.select_related('fournisseur').all()
        )
        propositions = []
        for cf in cf_list:
            try:
                propositions.append(cf.proposition)
            except Proposition.DoesNotExist:
                pass
        data['cf_list'] = cf_list
        data['propositions_sorted'] = sorted(propositions, key=lambda p: p.prix_unitaire)
        data['has_comparison'] = len(propositions) >= 2
        return data


class PropositionSaisirView(RoleRequiredMixin, View):
    allowed_roles = _WRITE_ROLES

    def _get_objects(self, pk, fournisseur_id):
        consultation = get_object_or_404(Consultation, pk=pk, statut=Consultation.Statut.OUVERTE)
        cf = get_object_or_404(
            ConsultationFournisseur,
            consultation=consultation,
            fournisseur_id=fournisseur_id,
        )
        try:
            instance = cf.proposition
        except Proposition.DoesNotExist:
            instance = None
        return consultation, cf, instance

    def get(self, request, pk, fournisseur_id):
        consultation, cf, instance = self._get_objects(pk, fournisseur_id)
        form = PropositionForm(instance=instance)
        return render(request, 'webapp/consultations/proposition_form.html',
                      {'form': form, 'consultation': consultation, 'cf': cf})

    def post(self, request, pk, fournisseur_id):
        consultation, cf, instance = self._get_objects(pk, fournisseur_id)
        form = PropositionForm(request.POST, instance=instance)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.consultation_fournisseur = cf
            prop.save()
            cf.statut = ConsultationFournisseur.Statut.PROPOSITION_RECUE
            cf.save()
            messages.success(request, f"Proposition de {cf.fournisseur.name} enregistrée.")
            return redirect('webapp:consultation_detail', pk=pk)
        return render(request, 'webapp/consultations/proposition_form.html',
                      {'form': form, 'consultation': consultation, 'cf': cf})


class PropositionRetenirView(RoleRequiredMixin, View):
    allowed_roles = _WRITE_ROLES

    def post(self, request, pk, proposition_id):
        consultation = get_object_or_404(Consultation, pk=pk, statut=Consultation.Statut.OUVERTE)
        proposition  = get_object_or_404(
            Proposition, pk=proposition_id,
            consultation_fournisseur__consultation=consultation,
        )
        # Reset all: mark non-retained and eliminate
        Proposition.objects.filter(
            consultation_fournisseur__consultation=consultation
        ).update(retenue=False)
        ConsultationFournisseur.objects.filter(
            consultation=consultation
        ).update(statut=ConsultationFournisseur.Statut.ELIMINE)
        # Retain winner
        proposition.retenue = True
        proposition.save()
        proposition.consultation_fournisseur.statut = ConsultationFournisseur.Statut.RETENU
        proposition.consultation_fournisseur.save()
        messages.success(
            request,
            f"Offre de {proposition.consultation_fournisseur.fournisseur.name} retenue.",
        )
        return redirect('webapp:consultation_detail', pk=pk)


class ConsultationCloturerView(RoleRequiredMixin, View):
    allowed_roles = _WRITE_ROLES

    def post(self, request, pk):
        consultation = get_object_or_404(Consultation, pk=pk, statut=Consultation.Statut.OUVERTE)
        consultation.statut = Consultation.Statut.CLOTUREE
        consultation.save()
        messages.success(request, f"Consultation {consultation.code} clôturée.")
        return redirect('webapp:consultation_detail', pk=pk)
