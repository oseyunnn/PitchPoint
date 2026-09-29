from django.shortcuts import render
from apps.home.models import Pitch  # Updated import

def profile_view(request):
    user_pitches = Pitch.objects.filter(submitter=request.user) if request.user.is_authenticated else []
    return render(request, "user_profile/profile.html", {"pitches": user_pitches})