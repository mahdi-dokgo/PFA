from django.urls import path
from .views import ReceptionListCreateView

urlpatterns = [
    path('', ReceptionListCreateView.as_view()),
]
