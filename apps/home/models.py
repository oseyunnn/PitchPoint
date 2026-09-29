import uuid
from django.db import models
from django.conf import settings


class Pitch(models.Model):
    pitch_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pitches",
        null=True,
        blank=True
    )
    guest_email = models.EmailField(
        null=True,
        blank=True
    )
    pitch_title = models.CharField(
        max_length=255
    )
    pitch_type = models.CharField(
        max_length=50
    )
    target_date = models.DateField()
    target_time = models.TimeField()
    pdf_letter_url = models.TextField(
        null=True,
        blank=True
    )
    additional_details = models.TextField(
        null=True,
        blank=True
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True
    )
    status = models.CharField(
        max_length=30,
        default="pending"
    )

    def __str__(self):
        return self.pitch_title


class PitchReview(models.Model):
    review_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    pitch = models.ForeignKey(
        Pitch,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pitch_reviews"
    )
    review_status = models.CharField(
        max_length=30,
        default="pending"
    )
    comments = models.TextField(
        null=True,
        blank=True
    )
    reviewed_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Review for {self.pitch.pitch_title} by {self.reviewer}"


class PitchEndorsement(models.Model):
    endorsement_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    pitch = models.ForeignKey(
        Pitch,
        on_delete=models.CASCADE,
        related_name="endorsements"
    )
    endorser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pitch_endorsements"
    )
    endorsement_status = models.CharField(
        max_length=30,
        default="pending"
    )
    remarks = models.TextField(
        null=True,
        blank=True
    )
    endorsed_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Endorsement for {self.pitch.pitch_title} by {self.endorser}"


class VolunteerRequest(models.Model):
    request_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    pitch = models.ForeignKey(
        Pitch,
        on_delete=models.CASCADE,
        related_name="volunteer_requests"
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="requested_volunteers"
    )
    num_volunteers_needed = models.SmallIntegerField(
        default=1
    )
    status = models.CharField(
        max_length=30,
        default="open"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Volunteer Request for {self.pitch.pitch_title}"


class VolunteerResponse(models.Model):
    response_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    volunteer_request = models.ForeignKey(
        VolunteerRequest,
        on_delete=models.CASCADE,
        related_name="responses"
    )
    volunteer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="volunteer_responses"
    )
    response_status = models.CharField(
        max_length=30,
        default="pending"
    )
    responded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Response by {self.volunteer} for {self.volunteer_request.pitch.pitch_title}"

class Assignment(models.Model):
    assignment_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    pitch = models.ForeignKey(
        Pitch,
        on_delete=models.CASCADE,
        related_name="assignments"
    )
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments"
    )
    assigned_role = models.CharField(
        max_length=50
    )
    assigned_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.assigned_user} as {self.assigned_role} for {self.pitch.pitch_title}"


class Comment(models.Model):
    comment_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    pitch = models.ForeignKey(
        Pitch,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    content = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Comment by {self.author} on {self.pitch.pitch_title}"


class Notification(models.Model):
    notification_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    pitch = models.ForeignKey(
        Pitch,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True
    )
    message = models.TextField()
    is_read = models.BooleanField(
        default=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Notification for {self.recipient}: {self.message[:30]}"