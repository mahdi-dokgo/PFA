from django.urls import path
from .views import POListCreateView, PODetailView, transition_po

urlpatterns = [
    path('', POListCreateView.as_view()),
    path('<int:pk>/', PODetailView.as_view()),
    path('<int:pk>/transition/', transition_po),
]
