from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from apps.articles.models import Article, Category
from apps.users.models import Role

from ..forms.articles import ArticleForm, CategoryForm
from ..mixins import RoleRequiredMixin

WRITE_ROLES = [Role.ADMIN, Role.ACHETEUR]


class ArticleListView(LoginRequiredMixin, ListView):
    model = Article
    template_name = 'webapp/articles/list.html'
    context_object_name = 'articles'
    paginate_by = 20

    def get_queryset(self):
        qs = Article.objects.select_related('category').order_by('reference')
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(reference__icontains=search))
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category_id=category)
        return qs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['categories'] = Category.objects.order_by('name')
        data['current_category'] = self.request.GET.get('category', '')
        data['search'] = self.request.GET.get('q', '')
        return data


class ArticleCreateView(RoleRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'webapp/articles/form.html'
    allowed_roles = WRITE_ROLES
    success_url = reverse_lazy('webapp:article_list')

    def form_valid(self, form):
        messages.success(self.request, f"Article « {form.instance.reference} » créé avec succès.")
        return super().form_valid(form)


class ArticleUpdateView(RoleRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'webapp/articles/form.html'
    allowed_roles = WRITE_ROLES
    success_url = reverse_lazy('webapp:article_list')

    def form_valid(self, form):
        messages.success(self.request, f"Article « {form.instance.reference} » mis à jour.")
        return super().form_valid(form)


class ArticleDeleteView(RoleRequiredMixin, View):
    allowed_roles = WRITE_ROLES

    def post(self, request, pk):
        article = get_object_or_404(Article, pk=pk)
        try:
            article.delete()
            messages.success(request, f"Article « {article.reference} » supprimé.")
        except ProtectedError:
            messages.error(request, f"Impossible de supprimer « {article.reference} » : il est utilisé dans des demandes ou commandes.")
        return redirect('webapp:article_list')


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'webapp/articles/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_queryset(self):
        return Category.objects.order_by('name')


class CategoryCreateView(RoleRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'webapp/articles/category_form.html'
    allowed_roles = WRITE_ROLES
    success_url = reverse_lazy('webapp:category_list')

    def form_valid(self, form):
        messages.success(self.request, f"Catégorie « {form.instance.name} » créée avec succès.")
        return super().form_valid(form)


class CategoryUpdateView(RoleRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'webapp/articles/category_form.html'
    allowed_roles = WRITE_ROLES
    success_url = reverse_lazy('webapp:category_list')

    def form_valid(self, form):
        messages.success(self.request, f"Catégorie « {form.instance.name} » mise à jour.")
        return super().form_valid(form)


class CategoryDeleteView(RoleRequiredMixin, View):
    allowed_roles = WRITE_ROLES

    def post(self, request, pk):
        category = get_object_or_404(Category, pk=pk)
        name = category.name
        category.delete()
        messages.success(request, f"Catégorie « {name} » supprimée.")
        return redirect('webapp:category_list')
