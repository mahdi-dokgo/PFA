from .models import AuditLog


def log_action(module, object_ref, action, user=None, detail=''):
    AuditLog.objects.create(
        module=module,
        object_ref=object_ref,
        action=action,
        detail=detail or '',
        actor=user if (user and user.is_authenticated) else None,
        actor_name=user.full_name if (user and user.is_authenticated) else '—',
    )
