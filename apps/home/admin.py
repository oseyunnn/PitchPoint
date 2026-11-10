from django.contrib import admin
from .models import Pitch, PitchRoleNeed


class PitchRoleNeedInline(admin.TabularInline):
    model = PitchRoleNeed
    extra = 1


@admin.register(Pitch)
class PitchAdmin(admin.ModelAdmin):
    list_display = ("pitch_title", "pitch_type", "target_date", "status")
    list_filter = ("status", "pitch_type")
    search_fields = ("pitch_title", "pitch_type", "location")
    inlines = (PitchRoleNeedInline,)
