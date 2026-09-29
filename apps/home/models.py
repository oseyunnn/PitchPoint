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