from django.urls import path
from . import views

urlpatterns = [
    path('<int:pk>/lire/', views.notification_mark_read, name='notification_mark_read'),
    path('tout-lire/', views.notification_mark_all_read, name='notification_mark_all_read'),
]
