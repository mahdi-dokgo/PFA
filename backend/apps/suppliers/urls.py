from django.urls import path
from .views import SupplierListCreateView, SupplierDetailView, archive_supplier

urlpatterns = [
    path('', SupplierListCreateView.as_view()),
    path('<int:pk>/', SupplierDetailView.as_view()),
    path('<int:pk>/archive/', archive_supplier),
]
