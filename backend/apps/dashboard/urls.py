from django.urls import path
from .views import (KpisView, RequestsPerPeriodView, OrdersByStatusView,
                    SpendBySupplierView, MostRequestedArticlesView, LateOrdersView)

urlpatterns = [
    path('kpis/', KpisView.as_view()),
    path('requests-per-period/', RequestsPerPeriodView.as_view()),
    path('orders-by-status/', OrdersByStatusView.as_view()),
    path('spend-by-supplier/', SpendBySupplierView.as_view()),
    path('most-requested-articles/', MostRequestedArticlesView.as_view()),
    path('late-orders/', LateOrdersView.as_view()),
]
