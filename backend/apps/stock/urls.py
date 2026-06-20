from django.urls import path
from .views import MovementsView, StockAlertsView

urlpatterns = [
    path('movements/', MovementsView.as_view()),
    path('alerts/', StockAlertsView.as_view()),
]
