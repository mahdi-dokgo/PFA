from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.auth_urls')),
    path('api/users/', include('apps.users.urls')),
    path('api/categories/', include('apps.articles.category_urls')),
    path('api/articles/', include('apps.articles.urls')),
    path('api/suppliers/', include('apps.suppliers.urls')),
    path('api/purchase-requests/', include('apps.requests_app.urls')),
    path('api/consultations/', include('apps.consultations.urls')),
    path('api/purchase-orders/', include('apps.orders.urls')),
    path('api/receptions/', include('apps.receptions.urls')),
    path('api/stock/', include('apps.stock.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),

    # Notifications (AJAX endpoints)
    path('notifications/', include('apps.notifications.urls')),

    # Frontend Django classique (templates + sessions)
    path('', include('apps.webapp.urls')),
]
