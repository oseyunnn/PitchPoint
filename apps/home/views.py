import uuid
import urllib.request
import urllib.error
import json
from datetime import timedelta
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from .models import (
    Assignment,
    Comment,
    Notification,
    Pitch,
    PitchEndorsement,
    PitchReview,
    VolunteerRequest,
    VolunteerResponse,
)


COMPLETED_PITCH_STATUSES = ("complete", "completed", "done")
CLOSED_PITCH_STATUSES = COMPLETED_PITCH_STATUSES + ("cancelled", "canceled")


def _dashboard_context(user):
    today = timezone.localdate()
    future_pitches = Pitch.objects.filter(target_date__gte=today)
    open_pitches = future_pitches.filter(status__in=("open", "pending"))
    pitches = (open_pitches if open_pitches.exists() else future_pitches)
    pitches = pitches.order_by("target_date", "target_time")[:12]
    context = {
        "pitches": pitches,
        "today_tasks": [],
        "unread_notifications": [],
        "unread_count": 0,
        "other_unread_count": 0,
        "submitted_count": 0,
        "assigned_count": 0,
        "completed_count": 0,
        "ongoing_count": 0,
        "chart_points": [],
        "chart_polyline": "",
        "chart_max": 1,
        "is_authenticated": user.is_authenticated,
    }

    chart_start = today - timedelta(days=41)
    activity_counts = [0] * 6
    if user.is_authenticated:
        context["submitted_count"] = Pitch.objects.filter(submitter=user).count()
        user_assignments = Assignment.objects.filter(assigned_user=user)
        context["assigned_count"] = user_assignments.count()
        context["completed_count"] = Pitch.objects.filter(
            Q(submitter=user) | Q(assignments__assigned_user=user),
            status__in=COMPLETED_PITCH_STATUSES,
        ).distinct().count()
        context["ongoing_count"] = Pitch.objects.filter(
            assignments__assigned_user=user
        ).exclude(status__in=CLOSED_PITCH_STATUSES).distinct().count()
        context["today_tasks"] = Pitch.objects.filter(
            Q(submitter=user) | Q(assignments__assigned_user=user),
            target_date__gte=today,
        ).distinct().order_by("target_date", "target_time")[:3]

        notifications = Notification.objects.filter(
            recipient=user,
            is_read=False,
        ).order_by("-created_at")
        context["unread_count"] = notifications.count()
        context["unread_notifications"] = notifications[:3]
        context["other_unread_count"] = max(context["unread_count"] - 3, 0)

        chart_since = timezone.now() - timedelta(days=42)
        activity_sources = (
            Pitch.objects.filter(submitter=user, submitted_at__gte=chart_since).values_list("submitted_at", flat=True),
            Assignment.objects.filter(assigned_user=user, assigned_at__gte=chart_since).values_list("assigned_at", flat=True),
            Comment.objects.filter(author=user, created_at__gte=chart_since).values_list("created_at", flat=True),
            PitchReview.objects.filter(reviewer=user, reviewed_at__gte=chart_since).values_list("reviewed_at", flat=True),
            PitchEndorsement.objects.filter(endorser=user, endorsed_at__gte=chart_since).values_list("endorsed_at", flat=True),
            VolunteerResponse.objects.filter(volunteer=user, responded_at__gte=chart_since).values_list("responded_at", flat=True),
        )
        for activity_source in activity_sources:
            for created_at in activity_source:
                week_index = min((created_at.date() - chart_start).days // 7, 5)
                if week_index >= 0:
                    activity_counts[week_index] += 1

    chart_max = max(activity_counts) or 1
    chart_points = []
    for index, count in enumerate(activity_counts):
        point_date = chart_start + timedelta(days=index * 7)
        chart_points.append({
            "x": 18 + index * 53,
            "y": 104 - round(count / chart_max * 78),
            "count": count,
            "label": point_date.strftime("%b %d"),
        })

    context["chart_points"] = chart_points
    context["chart_polyline"] = " ".join(
        f"{point['x']},{point['y']}" for point in chart_points
    )
    context["chart_max"] = chart_max
    return context

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
        location = request.POST.get("location", "").strip()
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
            location=location,
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

    return render(request, "home/dashboard.html", _dashboard_context(request.user))