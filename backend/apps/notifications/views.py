from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
@require_POST
def notification_mark_read(request, pk):
    """Mark a single notification as seen (lu=True). Does NOT resolve it."""
    Notification.objects.filter(pk=pk, user=request.user).update(lu=True)
    return JsonResponse({'ok': True})


@login_required
@require_POST
def notification_mark_all_read(request):
    """Mark all unread notifications as seen (lu=True). Does NOT resolve them."""
    Notification.objects.filter(user=request.user, lu=False, resolue=False).update(lu=True)
    return JsonResponse({'ok': True})
