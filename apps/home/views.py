import uuid
import urllib.request
import urllib.error
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .models import Pitch, VolunteerRequest, VolunteerResponse

def home_view(request):
    if request.method == "POST":
        action_type = request.POST.get("action_type")

        # ------------------------------------
        # ACTION 1: Volunteer for a Pitch
        # ------------------------------------
        if action_type == "volunteer":
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to volunteer.")
                return redirect("login:login")

            pitch_id = request.POST.get("pitch_id")
            try:
                pitch = Pitch.objects.get(pitch_id=pitch_id)
                
                vol_request, _ = VolunteerRequest.objects.get_or_create(
                    pitch=pitch,
                    defaults={
                        "requester": pitch.submitter or request.user,
                        "status": "open"
                    }
                )

                existing_response = VolunteerResponse.objects.filter(
                    volunteer_request=vol_request,
                    volunteer=request.user
                ).first()

                if existing_response:
                    messages.info(request, f"You have already volunteered for '{pitch.pitch_title}'.")
                else:
                    VolunteerResponse.objects.create(
                        volunteer_request=vol_request,
                        volunteer=request.user,
                        response_status="pending"
                    )
                    messages.success(request, f"Successfully signed up to volunteer for '{pitch.pitch_title}'!")

            except Pitch.DoesNotExist:
                messages.error(request, "Selected pitch was not found.")

            return redirect("home:home")

        # ------------------------------------
        # ACTION 2: Submit a New Pitch
        # ------------------------------------
        pitch_title = request.POST.get("pitch_title")
        pitch_type = request.POST.get("pitch_type")
        target_date = request.POST.get("target_date")
        target_time = request.POST.get("target_time")
        additional_details = request.POST.get("additional_details", "")
        pdf_letter_url = ""

        if "pdf_file" in request.FILES and request.FILES["pdf_file"]:
            pdf_file = request.FILES["pdf_file"]
            file_extension = pdf_file.name.split(".")[-1]
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_bytes = pdf_file.read()

            # Ensure clean URL base without trailing slash
            base_url = settings.SUPABASE_URL.rstrip("/")
            
            # Supabase Storage Object Upload Endpoint
            upload_endpoint = f"{base_url}/storage/v1/object/{settings.SUPABASE_BUCKET}/{unique_filename}"
            
            headers = {
                "apikey": settings.SUPABASE_KEY,
                "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                "Content-Type": "application/pdf",
                "x-upsert": "true"
            }

            try:
                req = urllib.request.Request(upload_endpoint, data=file_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req) as response:
                    if response.status in [200, 201]:
                        # Public URL format for public Supabase buckets
                        pdf_letter_url = f"{base_url}/storage/v1/object/public/{settings.SUPABASE_BUCKET}/{unique_filename}"
                        print(f"--> UPLOAD SUCCESSFUL! Saved URL: {pdf_letter_url}")
            except urllib.error.HTTPError as e:
                error_resp = e.read().decode("utf-8")
                print(f"--> SUPABASE STORAGE ERROR ({e.code}): {error_resp}")
                messages.error(request, f"Upload Failed: {error_resp}")
            except Exception as e:
                print(f"--> UPLOAD EXCEPTION: {str(e)}")

        submitter = request.user if request.user.is_authenticated else None

        new_pitch = Pitch.objects.create(
            submitter=submitter,
            pitch_title=pitch_title,
            pitch_type=pitch_type,
            target_date=target_date,
            target_time=target_time,
            pdf_letter_url=pdf_letter_url,
            additional_details=additional_details,
            status="open"
        )

        VolunteerRequest.objects.create(
            pitch=new_pitch,
            requester=submitter or request.user,
            status="open"
        )

        messages.success(request, "Pitch submitted successfully!")
        return redirect("home:home")

    pitches = Pitch.objects.filter(status="open") if Pitch.objects.filter(status="open").exists() else Pitch.objects.all()
    return render(request, "home/home.html", {"pitches": pitches})