from django.urls import path
from .views import UserListCreateView, UserDetailView, deactivate_user, set_role

urlpatterns = [
    path('', UserListCreateView.as_view()),
    path('<int:pk>/', UserDetailView.as_view()),
    path('<int:pk>/deactivate/', deactivate_user),
    path('<int:pk>/role/', set_role),
]
