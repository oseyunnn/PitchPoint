from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.home.models import Notification


@login_required
def inbox_view(request):
    user = request.user

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "mark_all_read":
            user.notifications.filter(is_read=False).update(is_read=True)
            messages.success(request, "All notifications marked as read.")

        elif action == "mark_read":
            notification_id = request.POST.get("notification_id")
            notif = get_object_or_404(Notification, notification_id=notification_id, recipient=user)
            notif.is_read = True
            notif.save(update_fields=["is_read"])

        elif action == "mark_unread":
            notification_id = request.POST.get("notification_id")
            notif = get_object_or_404(Notification, notification_id=notification_id, recipient=user)
            notif.is_read = False
            notif.save(update_fields=["is_read"])

        elif action == "delete":
            notification_id = request.POST.get("notification_id")
            notif = get_object_or_404(Notification, notification_id=notification_id, recipient=user)
            notif.delete()
            messages.success(request, "Notification deleted.")

        elif action == "clear_read":
            user.notifications.filter(is_read=True).delete()
            messages.success(request, "Cleared all read notifications.")

        return redirect("inbox:inbox")

    filter_type = request.GET.get("filter", "all").strip().lower()
    base_queryset = user.notifications.select_related("pitch").order_by("-created_at")

    total_count = base_queryset.count()
    unread_count = base_queryset.filter(is_read=False).count()

    if filter_type == "unread":
        notifications = base_queryset.filter(is_read=False)
    elif filter_type == "pitches":
        notifications = base_queryset.filter(pitch__isnull=False)
    elif filter_type == "feedback":
        notifications = base_queryset.filter(message__icontains="feedback") | base_queryset.filter(message__icontains="comment") | base_queryset.filter(message__icontains="replied")
    else:
        notifications = base_queryset

    return render(request, "inbox/inbox.html", {
        "notifications": notifications,
        "unread_count": unread_count,
        "total_count": total_count,
        "active_filter": filter_type,
    })
