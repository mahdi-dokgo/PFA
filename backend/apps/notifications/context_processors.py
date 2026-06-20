from .models import Notification


def notifications_processor(request):
    if not request.user.is_authenticated:
        return {}
    qs     = Notification.objects.filter(user=request.user, resolue=False)
    count  = qs.count()
    notifs = qs.order_by('-created_at')[:10]
    return {'notifications': notifs, 'notifications_count': count}
