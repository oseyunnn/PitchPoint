from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

@login_required
def settings_view(request):
    user = request.user
    profile = getattr(user, 'userprofile', None)

    if request.method == "POST":
        action = request.POST.get('action')

        if action == "update_username":
            new_username = request.POST.get('username')
            if new_username:
                user.username = new_username
                user.save()
                messages.success(request, "Username updated!")

        elif action == "update_position":
            new_position = request.POST.get('position')
            if profile:
                profile.position = new_position
                profile.save()
                messages.success(request, "Position updated!")

        elif action == "update_password":
            old_pass = request.POST.get('old_password')
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')

            if not user.check_password(old_pass):
                messages.error(request, "Incorrect old password.")
            elif new_pass != confirm_pass:
                messages.error(request, "New passwords do not match.")
            else:
                user.set_password(new_pass)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password updated successfully!")

        return redirect('user_settings:settings')

    return render(request, 'user_settings/settings.html', {
        'username': user.username,
        'position': profile.position if profile else '',
    })