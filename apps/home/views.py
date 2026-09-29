from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import PitchRequest

@login_required
def home_view(request):
    if request.method == "POST":
        title = request.POST.get("title")
        date = request.POST.get("date")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        pitch_type = request.POST.get("pitch_type")
        organization = request.POST.get("organization")
        active_email = request.POST.get("active_email")
        id_number = request.POST.get("id_number")
        contact_number = request.POST.get("contact_number")

        PitchRequest.objects.create(
            user=request.user,
            title=title,
            date=date,
            start_time=start_time,
            end_time=end_time,
            pitch_type=pitch_type,
            organization=organization,
            active_email=active_email,
            id_number=id_number,
            contact_number=contact_number,
        )
        messages.success(request, "Pitch request submitted successfully!")
        return redirect("home:home")

    pitches = PitchRequest.objects.all().order_by("-created_at")
    
    # Safely retrieve user's first name or fallback to username
    first_name = request.user.first_name if request.user.first_name else request.user.username
    if hasattr(request.user, 'userprofile') and request.user.userprofile.full_name:
        first_name = request.user.userprofile.full_name.split()[0]

    return render(request, "home/home.html", {
        "pitches": pitches,
        "first_name": first_name,
    })