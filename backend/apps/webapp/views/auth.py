from django.contrib.auth.views import LoginView

from ..forms.auth import EmailAuthenticationForm


class WebLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True
