from django import forms
from django.core.validators import URLValidator

from .models import WorkSubmission


class WorkSubmissionForm(forms.ModelForm):
    submission_url = forms.URLField(
        label="Link to your work",
        max_length=2048,
        validators=[URLValidator(schemes=("http", "https"))],
        widget=forms.URLInput(attrs={
            "placeholder": "https://",
            "autocomplete": "url",
            "inputmode": "url",
        }),
    )

    class Meta:
        model = WorkSubmission
        fields = ("submission_url",)


class SubmissionCommentForm(forms.Form):
    content = forms.CharField(
        label="Comment",
        min_length=1,
        max_length=5000,
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "Write a helpful note...",
        }),
    )
