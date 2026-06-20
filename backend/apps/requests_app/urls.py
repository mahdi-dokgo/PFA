from django.urls import path
from .views import PurchaseRequestListCreateView, PurchaseRequestDetailView, submit_request, approve_request, reject_request

urlpatterns = [
    path('', PurchaseRequestListCreateView.as_view()),
    path('<int:pk>/', PurchaseRequestDetailView.as_view()),
    path('<int:pk>/submit/', submit_request),
    path('<int:pk>/approve/', approve_request),
    path('<int:pk>/reject/', reject_request),
]
