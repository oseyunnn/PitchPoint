from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    position = models.CharField(max_length=100, blank=True, null=True)
    ttsp_email = models.EmailField(blank=True, null=True)
    
    def __str__(self):
        return self.full_name