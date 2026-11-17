from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from apps.home.models import Pitch, Assignment


@login_required
def profile_view(request):
    user = request.user
    submitted_count = Pitch.objects.filter(submitter=user).count()
    assigned_count = Assignment.objects.filter(assigned_user=user).count()
    all_user_pitches = Pitch.objects.filter(
        Q(submitter=user) | Q(assignments__assigned_user=user)
    ).distinct().order_by("-target_date")
    unread_count = user.notifications.filter(is_read=False).count()

    return render(request, "user_profile/profile.html", {
        "user": user,
        "full_name": user.name,
        "username": user.username or user.email.split("@")[0],
        "position": user.position or "Staff Member",
        "email": user.email,
        "student_id": user.student_id or "",
        "course": user.course or "",
        "year_level": user.year_level or "",
        "contact_number": user.contact_number or "",
        "submitted_count": submitted_count,
        "assigned_count": assigned_count,
        "pitches": all_user_pitches,
        "unread_count": unread_count,
    })
