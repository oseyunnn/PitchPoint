from django.shortcuts import render
from apps.home.models import Notification


def inbox_view(request):
    if request.user.is_authenticated:
        notifications = request.user.notifications.select_related("pitch").order_by("-created_at")
        unread_count = request.user.notifications.filter(is_read=False).count()
    else:
        notifications = Notification.objects.none()
        unread_count = 0
    return render(request, "inbox/inbox.html", {
        "notifications": notifications,
        "unread_count": unread_count,
    })