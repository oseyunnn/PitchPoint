from django.db import models
from django.contrib.auth.models import User

class PitchRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pitches")
    title = models.CharField(max_length=255)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    pitch_type = models.CharField(max_length=100)
    organization = models.CharField(max_length=255)
    active_email = models.EmailField()
    id_number = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title