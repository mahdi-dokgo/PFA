from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import F
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from apps.articles.models import Article
from apps.notifications.models import Notification
from apps.stock import services
from apps.stock.models import StockMovement
from apps.users.models import Role

from apps.audit.utils import log_action
from ..forms.stock import StockAdjustmentForm
from ..mixins import RoleRequiredMixin


class StockOverviewView(LoginRequiredMixin, ListView):
    template_name = 'webapp/stock/overview.html'
    context_object_name = 'articles'
    paginate_by = 20

    def get_queryset(self):
        qs = Article.objects.select_related('category').order_by('reference')
        if self.request.GET.get('alert'):
            qs = qs.filter(current_stock__lte=F('min_threshold'))
        return qs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['alert_count'] = Article.objects.filter(current_stock__lte=F('min_threshold')).count()
        data['alert_only'] = bool(self.request.GET.get('alert'))
        return data


class StockMovementListView(LoginRequiredMixin, ListView):
    template_name = 'webapp/stock/movements.html'
    context_object_name = 'movements'
    paginate_by = 20

    def get_queryset(self):
        qs = StockMovement.objects.select_related('article').order_by('-at')
        article_id = self.request.GET.get('article')
        if article_id:
            qs = qs.filter(article_id=article_id)
        movement_type = self.request.GET.get('type')
        if movement_type:
            qs = qs.filter(movement_type=movement_type)
        return qs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['articles'] = Article.objects.order_by('reference')
        data['types'] = StockMovement.Type.choices
        data['current_article'] = self.request.GET.get('article', '')
        data['current_type'] = self.request.GET.get('type', '')
        return data


class ExportStockExcelView(RoleRequiredMixin, View):
    allowed_roles = [Role.ADMIN, Role.ACHETEUR, Role.DIRECTION]

    def get(self, request):
        from datetime import date
        from ..utils.exports import export_excel

        qs = Article.objects.select_related('category').order_by('reference')
        headers = ['Référence', 'Article', 'Catégorie', 'Stock actuel', 'Seuil minimum', 'Statut']
        rows = [
            [
                a.reference,
                a.name,
                a.category.name if a.category else '—',
                a.current_stock,
                a.min_threshold,
                'CRITIQUE' if a.current_stock <= a.min_threshold else 'OK',
            ]
            for a in qs
        ]
        return export_excel(f"stock_{date.today()}.xlsx", headers, rows, title='État du stock')


class StockAdjustmentCreateView(RoleRequiredMixin, View):
    allowed_roles = [Role.ADMIN, Role.MAGASINIER]
    template_name = 'webapp/stock/adjustment_form.html'

    def get(self, request):
        initial = {}
        article_id = request.GET.get('article')
        if article_id:
            initial['article'] = article_id
        form = StockAdjustmentForm(initial=initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            try:
                movement = services.create_stock_adjustment(
                    article=form.cleaned_data['article'],
                    quantity=form.cleaned_data['quantity'],
                    reference=form.cleaned_data['reference'],
                )
            except ValidationError as exc:
                form.add_error(None, exc.messages)
            else:
                # Safety net: explicit resolution regardless of signal timing
                article = movement.article
                article.refresh_from_db()
                if article.min_threshold == 0 or article.current_stock > article.min_threshold:
                    Notification.objects.filter(
                        type='STOCK_CRITIQUE',
                        message__icontains=article.name,
                        resolue=False,
                    ).update(resolue=True, resolue_at=timezone.now())

                log_action('STOCK', article.reference, 'Ajustement manuel', user=request.user,
                           detail=f"Nouvelle quantité : {article.current_stock}")
                messages.success(
                    request,
                    f"Ajustement enregistré pour « {article.reference} » "
                    f"({movement.quantity:+d}). Stock actuel : {article.current_stock}."
                )
                return redirect('webapp:stock_movements')
        return render(request, self.template_name, {'form': form})
