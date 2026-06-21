from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Password reset flow
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url='/password-reset/done/',
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html',
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/password-reset-complete/',
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html',
         ),
         name='password_reset_complete'),
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
