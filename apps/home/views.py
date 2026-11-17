import uuid
import urllib.request
import urllib.error
from datetime import timedelta
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from .forms import SubmissionCommentForm, WorkSubmissionForm
from .models import (
    Assignment,
    Comment,
    Notification,
    Pitch,
    PitchEndorsement,
    PitchRoleNeed,
    PitchReview,
    WorkSubmission,
    VolunteerRequest,
    VolunteerResponse,
)


COMPLETED_PITCH_STATUSES = ("complete", "completed", "done")
CLOSED_PITCH_STATUSES = COMPLETED_PITCH_STATUSES + ("cancelled", "canceled")
PITCH_ROLE_CHOICES = (
    ("writer", "Writer"),
    ("artist", "Artist"),
    ("photojournalist", "Photojournalist"),
    ("researcher", "Researcher"),
    ("social-media-associate", "Social Media Associate"),
    ("website-associate", "Website Associate"),
    ("editor", "Editor"),
    ("other", "Other"),
)


def _is_editor(user):
    if not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    role = (getattr(user, "role", "") or "").casefold()
    if role in ("admin", "editor", "manager"):
        return True
    position = (getattr(user, "position", "") or "").strip().casefold()
    return any(keyword in position for keyword in ("editor", "manager", "head", "director", "lead"))


def _available_role_slots(pitch, role_need):
    normalized_role = role_need.role.strip().casefold()
    assignments = getattr(pitch, "all_assignments_list", [])
    assigned_user_ids = {
        assignment.assigned_user_id
        for assignment in assignments
        if (assignment.assigned_role or "").strip().casefold() == normalized_role
    }
    volunteer_requests = getattr(pitch, "all_volunteer_requests_list", [])
    active_response_user_ids = {
        response.volunteer_id
        for volunteer_request in volunteer_requests
        for response in getattr(volunteer_request, "all_responses_list", [])
        if response.role.strip().casefold() == normalized_role
        and response.response_status.strip().casefold() in ("pending", "accepted", "approved")
    }
    occupied_slots = len(assigned_user_ids | active_response_user_ids)
    return max(role_need.slots_needed - occupied_slots, 0)


def _dashboard_context(user):
    today = timezone.localdate()
    is_editor = _is_editor(user)

    # Base query for active pitches
    all_active_pitches = Pitch.objects.select_related("submitter").prefetch_related(
        "role_needs",
        Prefetch("assignments", queryset=Assignment.objects.select_related("assigned_user"), to_attr="all_assignments_list"),
        Prefetch(
            "volunteer_requests",
            queryset=VolunteerRequest.objects.prefetch_related(
                Prefetch("responses", queryset=VolunteerResponse.objects.select_related("volunteer"), to_attr="all_responses_list")
            ),
            to_attr="all_volunteer_requests_list",
        ),
        Prefetch(
            "work_submissions",
            queryset=WorkSubmission.objects.select_related("submitter").prefetch_related(
                Prefetch("comments", queryset=Comment.objects.select_related("author").order_by("created_at"), to_attr="submission_comments")
            ),
            to_attr="all_submissions_list",
        ),
    ).order_by("-submitted_at")

    pitches_list = list(all_active_pitches)

    my_assigned_pitches = []
    my_created_pitches = []
    review_needed_pitches = []
    today_tasks = []

    for pitch in pitches_list:
        pitch.is_owner = (user.is_authenticated and pitch.submitter_id == user.pk)
        assignments = getattr(pitch, "all_assignments_list", [])
        volunteer_requests = getattr(pitch, "all_volunteer_requests_list", [])
        submissions = getattr(pitch, "all_submissions_list", [])

        # Assigned members
        pitch.assigned_members = assignments
        user_assignment = next((a for a in assignments if a.assigned_user_id == user.pk), None) if user.is_authenticated else None
        pitch.current_user_assignment = user_assignment
        pitch.user_is_assigned = user_assignment is not None

        # Permissions
        pitch.can_submit_work = pitch.user_is_assigned
        pitch.can_review_work = is_editor or pitch.is_owner

        # Volunteer applications on this pitch
        pending_responses = []
        user_volunteer_resp = None
        for v_req in volunteer_requests:
            for resp in getattr(v_req, "all_responses_list", []):
                if resp.response_status.strip().casefold() == "pending":
                    pending_responses.append(resp)
                if user.is_authenticated and resp.volunteer_id == user.pk:
                    user_volunteer_resp = resp

        pitch.pending_volunteers = pending_responses
        pitch.user_volunteer_response = user_volunteer_resp
        pitch.user_has_volunteered = user_volunteer_resp is not None

        # Role needs and open slots
        pitch.open_roles_list = []
        needs = list(pitch.role_needs.all())
        for need in needs:
            need.available_slots = _available_role_slots(pitch, need)
            if need.available_slots > 0:
                pitch.open_roles_list.append(need)

        pitch.has_open_roles = bool(pitch.open_roles_list) or not needs

        # Submissions on this pitch
        pitch.dashboard_submissions = submissions
        pitch.current_user_submission = next(
            (s for s in submissions if user.is_authenticated and s.submitter_id == user.pk),
            None
        )

        for submission in submissions:
            submission.is_owned_by_user = (user.is_authenticated and submission.submitter_id == user.pk)
            comments = getattr(submission, "submission_comments", [])
            replies_by_parent = {}
            for comment in comments:
                if comment.parent_comment_id:
                    replies_by_parent.setdefault(comment.parent_comment_id, []).append(comment)
            submission.dashboard_comment_threads = []
            for comment in comments:
                if comment.parent_comment_id is None:
                    comment.dashboard_replies = replies_by_parent.get(comment.pk, [])
                    comment.can_reply = submission.is_owned_by_user and _is_editor(comment.author)
                    submission.dashboard_comment_threads.append(comment)

        # Categorize
        if pitch.user_is_assigned:
            my_assigned_pitches.append(pitch)
        if pitch.is_owner:
            my_created_pitches.append(pitch)
        if pitch.can_review_work and submissions:
            review_needed_pitches.append(pitch)

        if (pitch.user_is_assigned or pitch.is_owner) and pitch.target_date >= today:
            today_tasks.append(pitch)

    # Sort today tasks by date
    today_tasks.sort(key=lambda p: (p.target_date, p.target_time))
    today_tasks = today_tasks[:5]

    # Notifications & stats
    unread_notifications = []
    unread_count = 0
    other_unread_count = 0
    submitted_count = 0
    assigned_count = 0
    completed_count = 0
    ongoing_count = 0
    pending_volunteers_count = 0

    if user.is_authenticated:
        submitted_count = Pitch.objects.filter(submitter=user).count()
        user_assignments = Assignment.objects.filter(assigned_user=user)
        assigned_count = user_assignments.count()
        completed_count = Pitch.objects.filter(
            Q(submitter=user) | Q(assignments__assigned_user=user),
            status__in=COMPLETED_PITCH_STATUSES,
        ).distinct().count()
        ongoing_count = Pitch.objects.filter(
            Q(submitter=user) | Q(assignments__assigned_user=user)
        ).exclude(status__in=CLOSED_PITCH_STATUSES).distinct().count()

        notifs = Notification.objects.filter(recipient=user, is_read=False).order_by("-created_at")
        unread_count = notifs.count()
        unread_notifications = list(notifs[:4])
        other_unread_count = max(unread_count - 4, 0)

        # Count total pending volunteers on user's created pitches
        pending_volunteers_count = sum(len(p.pending_volunteers) for p in my_created_pitches)

    # 6-week activity chart
    chart_start = today - timedelta(days=41)
    activity_counts = [0] * 6
    if user.is_authenticated:
        chart_since = timezone.now() - timedelta(days=42)
        activity_sources = (
            Pitch.objects.filter(submitter=user, submitted_at__gte=chart_since).values_list("submitted_at", flat=True),
            Assignment.objects.filter(assigned_user=user, assigned_at__gte=chart_since).values_list("assigned_at", flat=True),
            Comment.objects.filter(author=user, created_at__gte=chart_since).values_list("created_at", flat=True),
            PitchReview.objects.filter(reviewer=user, reviewed_at__gte=chart_since).values_list("reviewed_at", flat=True),
            PitchEndorsement.objects.filter(endorser=user, endorsed_at__gte=chart_since).values_list("endorsed_at", flat=True),
            VolunteerResponse.objects.filter(volunteer=user, responded_at__gte=chart_since).values_list("responded_at", flat=True),
            WorkSubmission.objects.filter(submitter=user, updated_at__gte=chart_since).values_list("updated_at", flat=True),
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

    chart_polyline = " ".join(f"{point['x']},{point['y']}" for point in chart_points)
    chart_line = " ".join(f"{point['x']},{point['y']}" for point in chart_points)
    chart_area = f"18,104 {chart_line} 283,104"

    previous_submissions = []
    if user.is_authenticated:
        previous_submissions = WorkSubmission.objects.filter(submitter=user).select_related("pitch").order_by("-updated_at")[:8]

    return {
        "pitches": pitches_list,
        "my_assigned_pitches": my_assigned_pitches,
        "my_created_pitches": my_created_pitches,
        "review_needed_pitches": review_needed_pitches,
        "pitch_role_choices": [{"key": key, "label": label} for key, label in PITCH_ROLE_CHOICES],
        "previous_submissions": previous_submissions,
        "today_tasks": today_tasks,
        "unread_notifications": unread_notifications,
        "unread_count": unread_count,
        "other_unread_count": other_unread_count,
        "submitted_count": submitted_count,
        "assigned_count": assigned_count,
        "completed_count": completed_count,
        "ongoing_count": ongoing_count,
        "pending_volunteers_count": pending_volunteers_count,
        "chart_points": chart_points,
        "chart_polyline": chart_polyline,
        "chart_area": chart_area,
        "chart_max": chart_max,
        "chart_activity_total": sum(activity_counts),
        "chart_active_weeks": sum(count > 0 for count in activity_counts),
        "chart_peak_week": chart_points[activity_counts.index(max(activity_counts))]["label"] if any(activity_counts) else "No activity yet",
        "is_authenticated": user.is_authenticated,
        "is_editor": is_editor,
    }


def _handle_submission_action(request, action_type):
    if not request.user.is_authenticated:
        messages.error(request, "Please sign in to manage work submissions.")
        return redirect("login:login")

    submission_id = request.POST.get("submission_id")
    if action_type in ("editor_comment", "reply_submission_comment"):
        submission = get_object_or_404(
            WorkSubmission.objects.select_related("pitch", "submitter"),
            submission_id=submission_id,
        )
        comment_form = SubmissionCommentForm(request.POST)
        if not comment_form.is_valid():
            messages.error(request, "Enter a comment before submitting.")
            return redirect("home:home")

        if action_type == "editor_comment":
            if not (_is_editor(request.user) or submission.pitch.submitter_id == request.user.pk):
                messages.error(request, "You are not assigned to review this work.")
                return redirect("home:home")
            comment = Comment.objects.create(
                pitch=submission.pitch,
                submission=submission,
                author=request.user,
                content=comment_form.cleaned_data["content"],
            )
            if submission.submitter_id != request.user.pk:
                Notification.objects.create(
                    recipient=submission.submitter,
                    pitch=submission.pitch,
                    message=f"Editorial feedback posted on your work for '{submission.pitch.pitch_title}'.",
                )
            messages.success(request, "Your editorial feedback has been sent.")
            return redirect("home:home")

        parent_comment = get_object_or_404(
            Comment.objects.select_related("author"),
            comment_id=request.POST.get("parent_comment_id"),
            submission=submission,
            parent_comment__isnull=True,
        )
        if submission.submitter_id != request.user.pk and not _is_editor(request.user):
            messages.error(request, "You can only reply to feedback on your own work.")
            return redirect("home:home")
        Comment.objects.create(
            pitch=submission.pitch,
            submission=submission,
            parent_comment=parent_comment,
            author=request.user,
            content=comment_form.cleaned_data["content"],
        )
        if parent_comment.author_id != request.user.pk:
            Notification.objects.create(
                recipient=parent_comment.author,
                pitch=submission.pitch,
                message=f"{request.user.name} replied to feedback on '{submission.pitch.pitch_title}'.",
            )
        messages.success(request, "Your reply has been sent.")
        return redirect("home:home")

    pitch = get_object_or_404(Pitch, pitch_id=request.POST.get("pitch_id"))
    if not Assignment.objects.filter(pitch=pitch, assigned_user=request.user).exists():
        messages.error(request, "Only members assigned to this pitch can submit work.")
        return redirect("home:home")

    form = WorkSubmissionForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Enter a valid http or https link to your work.")
        return redirect("home:home")

    submission, created = WorkSubmission.objects.get_or_create(
        pitch=pitch,
        submitter=request.user,
        defaults={"submission_url": form.cleaned_data["submission_url"]},
    )
    if not created:
        submission.submission_url = form.cleaned_data["submission_url"]
        submission.save(update_fields=("submission_url", "updated_at"))

    # Notify pitch submitter
    if pitch.submitter and pitch.submitter_id != request.user.pk:
        Notification.objects.create(
            recipient=pitch.submitter,
            pitch=pitch,
            message=f"{request.user.name} submitted work for '{pitch.pitch_title}'.",
        )

    messages.success(
        request,
        "Work submitted successfully! Editors and pitch leads will review it." if created else "Your work link has been updated.",
    )
    return redirect("home:home")


def home_view(request):
    if request.method == "POST":
        action_type = request.POST.get("action_type")
        if action_type in ("submit_work", "editor_comment", "reply_submission_comment"):
            return _handle_submission_action(request, action_type)

        # ------------------------------------
        # ACTION: Manage Volunteer Application (Approve / Decline)
        # ------------------------------------
        if action_type == "manage_volunteer":
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to manage volunteer requests.")
                return redirect("login:login")

            response_id = request.POST.get("response_id")
            decision = request.POST.get("decision")  # "approve" or "decline"
            response = get_object_or_404(
                VolunteerResponse.objects.select_related("volunteer_request__pitch", "volunteer"),
                response_id=response_id,
            )
            pitch = response.volunteer_request.pitch

            # Check permission: must be pitch submitter, editor, or admin
            if not (pitch.submitter_id == request.user.pk or _is_editor(request.user)):
                messages.error(request, "You do not have permission to review volunteers for this pitch.")
                return redirect("home:home")

            if decision == "approve":
                response.response_status = "accepted"
                response.save(update_fields=["response_status"])

                assigned_role = response.role or getattr(response.volunteer, "position", "") or "Staff"
                Assignment.objects.get_or_create(
                    pitch=pitch,
                    assigned_user=response.volunteer,
                    defaults={"assigned_role": assigned_role},
                )

                # Send approval notification to volunteer
                Notification.objects.create(
                    recipient=response.volunteer,
                    pitch=pitch,
                    message=f"Congratulations! You were assigned as {assigned_role} for '{pitch.pitch_title}'. Check your dashboard to view tasks and submit work.",
                )
                messages.success(request, f"Approved {response.volunteer.name} as {assigned_role} for '{pitch.pitch_title}'.")
            elif decision == "decline":
                response.response_status = "declined"
                response.save(update_fields=["response_status"])

                # Send decline notification to volunteer
                Notification.objects.create(
                    recipient=response.volunteer,
                    pitch=pitch,
                    message=f"Your volunteer application for '{pitch.pitch_title}' was not selected this time.",
                )
                messages.info(request, f"Declined application from {response.volunteer.name}.")

            return redirect("home:home")

        # ------------------------------------
        # ACTION: Update Pitch Status (e.g. Mark Completed)
        # ------------------------------------
        if action_type == "update_pitch_status":
            if not request.user.is_authenticated:
                messages.error(request, "Please log in.")
                return redirect("login:login")

            pitch_id = request.POST.get("pitch_id")
            new_status = request.POST.get("status")
            pitch = get_object_or_404(Pitch, pitch_id=pitch_id)

            if not (pitch.submitter_id == request.user.pk or _is_editor(request.user)):
                messages.error(request, "You do not have permission to update this pitch status.")
                return redirect("home:home")

            if new_status in ("open", "in_progress", "completed", "cancelled"):
                pitch.status = new_status
                pitch.save(update_fields=["status"])
                messages.success(request, f"Pitch '{pitch.pitch_title}' status updated to {new_status.replace('_', ' ').title()}.")

            return redirect("home:home")

        # ------------------------------------
        # ACTION: Volunteer for a Pitch
        # ------------------------------------
        if action_type == "volunteer":
            if not request.user.is_authenticated:
                messages.error(request, "Please log in to volunteer.")
                return redirect("login:login")

            pitch_id = request.POST.get("pitch_id")
            chosen_role = (request.POST.get("role") or getattr(request.user, "position", "") or "Staff").strip()

            try:
                pitch = Pitch.objects.get(pitch_id=pitch_id)

                vol_request, _ = VolunteerRequest.objects.get_or_create(
                    pitch=pitch,
                    defaults={
                        "requester": pitch.submitter or request.user,
                        "status": "open",
                    },
                )

                existing_response = VolunteerResponse.objects.filter(
                    volunteer_request=vol_request,
                    volunteer=request.user,
                ).first()

                if existing_response:
                    if existing_response.response_status in ("pending", "accepted", "approved"):
                        messages.info(request, f"You have already applied to volunteer for '{pitch.pitch_title}'.")
                    else:
                        existing_response.response_status = "pending"
                        existing_response.role = chosen_role
                        existing_response.save(update_fields=["response_status", "role"])
                        messages.success(request, f"Application updated to volunteer as {chosen_role} for '{pitch.pitch_title}'!")
                else:
                    VolunteerResponse.objects.create(
                        volunteer_request=vol_request,
                        volunteer=request.user,
                        role=chosen_role,
                        response_status="pending",
                    )
                    # Notify pitch submitter
                    if pitch.submitter and pitch.submitter_id != request.user.pk:
                        Notification.objects.create(
                            recipient=pitch.submitter,
                            pitch=pitch,
                            message=f"{request.user.name} ({chosen_role}) applied to volunteer for your pitch '{pitch.pitch_title}'!",
                        )
                    messages.success(request, f"Successfully signed up to volunteer as {chosen_role} for '{pitch.pitch_title}'!")

            except Pitch.DoesNotExist:
                messages.error(request, "Selected pitch was not found.")

            return redirect("home:home")

        # ------------------------------------
        # ACTION: Submit a New Pitch
        # ------------------------------------
        if action_type == "create_pitch":
            if not request.user.is_authenticated:
                messages.error(request, "Please sign in to submit a pitch.")
                return redirect("login:login")

            valid_roles = dict(PITCH_ROLE_CHOICES)
            selected_roles = set(request.POST.getlist("needed_roles"))
            role_slots = {}
            if selected_roles:
                for role_key in selected_roles:
                    if role_key in valid_roles:
                        slots = int(request.POST.get(f"slots_{role_key}", "1"))
                        role_slots[valid_roles[role_key]] = max(1, min(slots, 20))

            pitch_title = request.POST.get("pitch_title", "").strip()
            pitch_type = request.POST.get("pitch_type", "").strip() or "Event Coverage"
            location = request.POST.get("location", "").strip()
            target_date = request.POST.get("target_date")
            target_time = request.POST.get("target_time")
            additional_details = request.POST.get("additional_details", "")
            pdf_letter_url = ""

            if not pitch_title or not target_date or not target_time:
                messages.error(request, "Pitch title, target date, and target time are required.")
                return redirect("home:home")

            if "pdf_file" in request.FILES and request.FILES["pdf_file"]:
                pdf_file = request.FILES["pdf_file"]
                file_extension = pdf_file.name.split(".")[-1]
                unique_filename = f"{uuid.uuid4()}.{file_extension}"
                file_bytes = pdf_file.read()

                base_url = getattr(settings, "SUPABASE_URL", "").rstrip("/")
                bucket = getattr(settings, "SUPABASE_BUCKET", "pitch-letters")
                api_key = getattr(settings, "SUPABASE_KEY", "")

                if base_url and api_key:
                    upload_endpoint = f"{base_url}/storage/v1/object/{bucket}/{unique_filename}"
                    headers = {
                        "apikey": api_key,
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/pdf",
                        "x-upsert": "true",
                    }
                    try:
                        req = urllib.request.Request(upload_endpoint, data=file_bytes, headers=headers, method="POST")
                        with urllib.request.urlopen(req, timeout=10) as response:
                            if response.status in (200, 201):
                                pdf_letter_url = f"{base_url}/storage/v1/object/public/{bucket}/{unique_filename}"
                    except Exception as e:
                        print(f"--> UPLOAD WARNING (Supabase storage): {e}")

            new_pitch = Pitch.objects.create(
                submitter=request.user,
                pitch_title=pitch_title,
                pitch_type=pitch_type,
                location=location,
                target_date=target_date,
                target_time=target_time,
                pdf_letter_url=pdf_letter_url,
                additional_details=additional_details,
                status="open",
            )

            if role_slots:
                PitchRoleNeed.objects.bulk_create([
                    PitchRoleNeed(pitch=new_pitch, role=role, slots_needed=slots)
                    for role, slots in role_slots.items()
                ])

            VolunteerRequest.objects.create(
                pitch=new_pitch,
                requester=request.user,
                status="open",
            )

            messages.success(request, f"Pitch '{new_pitch.pitch_title}' submitted successfully!")
            return redirect("home:home")

    return render(request, "home/dashboard.html", _dashboard_context(request.user))


def pitches_view(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Please sign in to volunteer for a pitch.")
            return redirect("login:login")

        pitch_id = request.POST.get("pitch_id")
        role = (request.POST.get("role") or getattr(request.user, "position", "") or "Staff").strip()

        pitch = get_object_or_404(
            Pitch.objects.prefetch_related(
                "role_needs",
                "assignments",
                Prefetch(
                    "volunteer_requests",
                    queryset=VolunteerRequest.objects.prefetch_related("responses"),
                    to_attr="dashboard_volunteer_requests",
                ),
            ),
            pitch_id=pitch_id,
        )

        today = timezone.localdate()
        if pitch.status.strip().casefold() in CLOSED_PITCH_STATUSES or pitch.target_date < today:
            messages.error(request, "This pitch is no longer accepting volunteers.")
            return redirect("home:pitches")

        # Check if already assigned
        if pitch.assignments.filter(assigned_user=request.user).exists():
            messages.info(request, "You are already an assigned contributor on this pitch.")
            return redirect("home:pitches")

        duplicate_request = False
        try:
            with transaction.atomic():
                vol_request, _ = VolunteerRequest.objects.get_or_create(
                    pitch=pitch,
                    defaults={"requester": pitch.submitter or request.user, "status": "open"},
                )
                existing = VolunteerResponse.objects.filter(
                    volunteer_request=vol_request,
                    volunteer=request.user,
                ).first()

                if existing:
                    if existing.response_status in ("pending", "accepted", "approved"):
                        duplicate_request = True
                    else:
                        existing.response_status = "pending"
                        existing.role = role
                        existing.save(update_fields=["response_status", "role"])
                else:
                    VolunteerResponse.objects.create(
                        volunteer_request=vol_request,
                        volunteer=request.user,
                        role=role,
                        response_status="pending",
                    )
                    # Notify submitter
                    if pitch.submitter and pitch.submitter_id != request.user.pk:
                        Notification.objects.create(
                            recipient=pitch.submitter,
                            pitch=pitch,
                            message=f"{request.user.name} ({role}) volunteered for your pitch '{pitch.pitch_title}'.",
                        )
        except IntegrityError:
            duplicate_request = True

        if duplicate_request:
            messages.info(request, f"You have already submitted a volunteer application for '{pitch.pitch_title}'.")
        else:
            messages.success(request, f"Your volunteer application as {role} for '{pitch.pitch_title}' was sent to the pitch lead!")

        return redirect("home:pitches")

    # Browse & Filters
    search_query = request.GET.get("q", "").strip()
    active_tab = request.GET.get("tab", "all").strip().lower()
    role_filter = request.GET.get("role", "").strip()
    today = timezone.localdate()

    pitches = Pitch.objects.select_related("submitter").prefetch_related(
        "role_needs",
        Prefetch("assignments", queryset=Assignment.objects.select_related("assigned_user"), to_attr="all_assignments_list"),
        Prefetch(
            "volunteer_requests",
            queryset=VolunteerRequest.objects.prefetch_related(
                Prefetch("responses", queryset=VolunteerResponse.objects.select_related("volunteer"), to_attr="all_responses_list")
            ),
            to_attr="all_volunteer_requests_list",
        ),
    ).order_by("target_date", "target_time")

    if search_query:
        pitches = pitches.filter(
            Q(pitch_title__icontains=search_query)
            | Q(pitch_type__icontains=search_query)
            | Q(location__icontains=search_query)
            | Q(additional_details__icontains=search_query)
            | Q(submitter__name__icontains=search_query)
        )

    user_position = (getattr(request.user, "position", "") or "").strip()
    user_position_lower = user_position.casefold()

    all_pitches = []
    open_pitches = []
    matched_pitches = []
    my_pitches = []

    for pitch in pitches:
        assignments = getattr(pitch, "all_assignments_list", [])
        volunteer_requests = getattr(pitch, "all_volunteer_requests_list", [])
        pitch.assigned_members = assignments

        # Check user status
        pitch.is_owner = (request.user.is_authenticated and pitch.submitter_id == request.user.pk)
        pitch.user_assignment = next((a for a in assignments if a.assigned_user_id == request.user.pk), None) if request.user.is_authenticated else None
        pitch.user_is_assigned = pitch.user_assignment is not None

        user_resp = None
        for v_req in volunteer_requests:
            for resp in getattr(v_req, "all_responses_list", []):
                if request.user.is_authenticated and resp.volunteer_id == request.user.pk:
                    user_resp = resp
                    break
            if user_resp:
                break
        pitch.user_volunteer_response = user_resp
        pitch.user_has_requested = user_resp is not None and user_resp.response_status in ("pending", "accepted", "approved")

        # Calculate role needs
        pitch.open_roles = []
        pitch.all_open_roles = []
        needs = list(pitch.role_needs.all())

        if needs:
            for need in needs:
                need.available_slots = _available_role_slots(pitch, need)
                if need.available_slots > 0:
                    pitch.all_open_roles.append(need)
                    if not user_position_lower or need.role.strip().casefold() == user_position_lower:
                        pitch.open_roles.append(need)
        else:
            # Pitch has no rigid role restrictions -> open for all roles
            pitch.has_open_call = True

        pitch.is_open_for_volunteers = (
            pitch.status.strip().casefold() in ("open", "pending", "in_progress")
            and pitch.target_date >= today
            and (bool(pitch.all_open_roles) or not needs)
        )

        pitch.is_matched = bool(pitch.open_roles) or (pitch.is_open_for_volunteers and not needs)

        if role_filter:
            if needs and not any(r.role.casefold() == role_filter.casefold() for r in needs):
                continue

        all_pitches.append(pitch)
        if pitch.is_open_for_volunteers:
            open_pitches.append(pitch)
        if pitch.is_matched and pitch.is_open_for_volunteers:
            matched_pitches.append(pitch)
        if pitch.is_owner:
            my_pitches.append(pitch)

    # Determine display list based on active tab
    if active_tab == "open":
        display_pitches = open_pitches
    elif active_tab == "matched":
        display_pitches = matched_pitches
    elif active_tab == "my":
        display_pitches = my_pitches
    else:
        display_pitches = all_pitches

    total_role_openings = sum(
        need.available_slots
        for pitch in open_pitches
        for need in getattr(pitch, "all_open_roles", [])
    )

    unread_count = request.user.notifications.filter(is_read=False).count() if request.user.is_authenticated else 0

    return render(request, "home/pitches.html", {
        "search_query": search_query,
        "active_tab": active_tab,
        "role_filter": role_filter,
        "pitches": display_pitches,
        "all_count": len(all_pitches),
        "open_count": len(open_pitches),
        "matched_count": len(matched_pitches),
        "my_count": len(my_pitches),
        "role_opening_count": total_role_openings,
        "member_position": user_position,
        "is_authenticated": request.user.is_authenticated,
        "unread_count": unread_count,
        "pitch_role_choices": [label for _, label in PITCH_ROLE_CHOICES],
    })
