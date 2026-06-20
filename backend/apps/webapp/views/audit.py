from django.views.generic import ListView

from apps.audit.models import AuditLog
from apps.users.models import Role
from ..mixins import RoleRequiredMixin


class AuditLogListView(RoleRequiredMixin, ListView):
    allowed_roles = [Role.ADMIN, Role.DIRECTION]
    model = AuditLog
    template_name = 'webapp/audit/list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        qs = AuditLog.objects.select_related('actor').order_by('-at')
        module = self.request.GET.get('module', '')
        q = self.request.GET.get('q', '')
        if module:
            qs = qs.filter(module=module)
        if q:
            qs = (
                qs.filter(object_ref__icontains=q)
                | qs.filter(action__icontains=q)
                | qs.filter(actor_name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['module_choices'] = AuditLog.Module.choices
        data['current_module'] = self.request.GET.get('module', '')
        data['search'] = self.request.GET.get('q', '')
        return data
