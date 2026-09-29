from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.home.models import PitchRequest

@login_required
def profile_view(request):
    user_profile = getattr(request.user, 'userprofile', None)
    user_pitches = PitchRequest.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'full_name': user_profile.full_name if user_profile else request.user.username,
        'position': user_profile.position if user_profile and user_profile.position else 'Member',
        'username': request.user.username,
        'pitches': user_pitches,
    }
    return render(request, 'user_profile/profile.html', context)