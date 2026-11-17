from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from apps.register.models import UserAccount

TTSP_POSITIONS = (
    ("Writer", "Writer"),
    ("Artist", "Artist"),
    ("Photojournalist", "Photojournalist"),
    ("Researcher", "Researcher"),
    ("Social Media Associate", "Social Media Associate"),
    ("Website Associate", "Website Associate"),
    ("Editor", "Editor"),
    ("Editor-in-Chief", "Editor-in-Chief"),
    ("Managing Editor", "Managing Editor"),
    ("Manager", "Manager"),
    ("Contributor", "Contributor"),
    ("Layout Artist", "Layout Artist"),
    ("Copy Editor", "Copy Editor"),
    ("Cartoonist", "Cartoonist"),
    ("Staff Member", "Staff Member"),
    ("Other", "Other"),
)


@login_required
def settings_view(request):
    user = request.user

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "update_profile":
            name = (request.POST.get('name') or '').strip()
            username = (request.POST.get('username') or '').strip()
            position = (request.POST.get('position') or '').strip()
            contact_number = (request.POST.get('contact_number') or '').strip()
            student_id = (request.POST.get('student_id') or '').strip()
            course = (request.POST.get('course') or '').strip()
            year_level_raw = request.POST.get('year_level')

            if name:
                user.name = name
            if username:
                if UserAccount.objects.filter(username=username).exclude(pk=user.pk).exists():
                    messages.error(request, f"The username '@{username}' is already taken.")
                    return redirect('user_settings:settings')
                user.username = username
            if position:
                user.position = position

            user.contact_number = contact_number
            user.student_id = student_id
            user.course = course
            if year_level_raw and str(year_level_raw).isdigit():
                user.year_level = int(year_level_raw)
            elif not year_level_raw:
                user.year_level = None

            user.save()
            messages.success(request, "Your profile and editorial details have been updated!")

        elif action == "update_password":
            old_pass = request.POST.get('old_password')
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')

            if not user.check_password(old_pass):
                messages.error(request, "Current password is incorrect.")
            elif len(new_pass or "") < 8:
                messages.error(request, "New password must be at least 8 characters long.")
            elif new_pass != confirm_pass:
                messages.error(request, "New password and confirmation do not match.")
            else:
                user.set_password(new_pass)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password updated successfully!")

        return redirect('user_settings:settings')

    unread_count = user.notifications.filter(is_read=False).count() if user.is_authenticated else 0

    return render(request, 'user_settings/settings.html', {
        'user': user,
        'name': user.name,
        'username': user.username or '',
        'email': user.email,
        'position': user.position or '',
        'contact_number': user.contact_number or '',
        'student_id': user.student_id or '',
        'course': user.course or '',
        'year_level': user.year_level or '',
        'position_choices': TTSP_POSITIONS,
        'unread_count': unread_count,
    })
