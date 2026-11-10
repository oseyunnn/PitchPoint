from datetime import time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.register.models import UserAccount
from .models import Assignment, Comment, Notification, Pitch, WorkSubmission


class WorkSubmissionTests(TestCase):
    def setUp(self):
        self.member = UserAccount.objects.create_user(
            email="member@example.com",
            password="test-password",
            name="Member One",
            role="student",
            position="Writer",
        )
        self.editor = UserAccount.objects.create_user(
            email="editor@example.com",
            password="test-password",
            name="Editor One",
            role="student",
            position="Editor",
        )
        self.pitch = Pitch.objects.create(
            submitter=self.member,
            pitch_title="Community feature",
            pitch_type="Article",
            target_date=timezone.localdate() + timedelta(days=3),
            target_time=time(10, 0),
            status="open",
        )
        Assignment.objects.create(
            pitch=self.pitch,
            assigned_user=self.member,
            assigned_role="Writer",
        )
        Assignment.objects.create(
            pitch=self.pitch,
            assigned_user=self.editor,
            assigned_role="Editor",
        )
        self.submission_url = reverse("home:home")

    def test_assigned_member_can_submit_and_update_work_link(self):
        self.client.force_login(self.member)

        response = self.client.post(self.submission_url, {
            "action_type": "submit_work",
            "pitch_id": str(self.pitch.pk),
            "submission_url": "https://example.com/first-draft",
        })
        self.assertRedirects(response, self.submission_url)
        submission = WorkSubmission.objects.get(pitch=self.pitch, submitter=self.member)

        self.client.post(self.submission_url, {
            "action_type": "submit_work",
            "pitch_id": str(self.pitch.pk),
            "submission_url": "https://example.com/final-draft",
        })
        submission.refresh_from_db()
        self.assertEqual(submission.submission_url, "https://example.com/final-draft")
        self.assertEqual(WorkSubmission.objects.filter(pitch=self.pitch, submitter=self.member).count(), 1)

    def test_unassigned_member_cannot_submit_work(self):
        unassigned = UserAccount.objects.create_user(
            email="unassigned@example.com",
            password="test-password",
            name="Unassigned Member",
            role="student",
            position="Writer",
        )
        self.client.force_login(unassigned)

        self.client.post(self.submission_url, {
            "action_type": "submit_work",
            "pitch_id": str(self.pitch.pk),
            "submission_url": "https://example.com/work",
        })

        self.assertFalse(WorkSubmission.objects.filter(pitch=self.pitch).exists())

    def test_editor_feedback_and_member_reply_are_visible(self):
        submission = WorkSubmission.objects.create(
            pitch=self.pitch,
            submitter=self.member,
            submission_url="https://example.com/work",
        )
        self.client.force_login(self.editor)
        self.client.post(self.submission_url, {
            "action_type": "editor_comment",
            "submission_id": str(submission.pk),
            "content": "Please revise the introduction.",
        })
        feedback = Comment.objects.get(submission=submission, parent_comment__isnull=True)

        self.client.force_login(self.member)
        self.client.post(self.submission_url, {
            "action_type": "reply_submission_comment",
            "submission_id": str(submission.pk),
            "parent_comment_id": str(feedback.pk),
            "content": "I will update it today.",
        })

        response = self.client.get(self.submission_url)
        self.assertContains(response, "Please revise the introduction.")
        self.assertContains(response, "I will update it today.")
        self.assertContains(response, "Previous work")
        self.assertContains(response, "https://example.com/work")
        self.assertEqual(feedback.replies.count(), 1)
        self.assertTrue(Notification.objects.filter(recipient=self.member, pitch=self.pitch).exists())

    def test_non_http_work_link_is_rejected(self):
        self.client.force_login(self.member)

        self.client.post(self.submission_url, {
            "action_type": "submit_work",
            "pitch_id": str(self.pitch.pk),
            "submission_url": "javascript:alert(1)",
        })

        self.assertFalse(WorkSubmission.objects.filter(pitch=self.pitch).exists())

    def test_non_editor_cannot_comment_even_if_assigned(self):
        non_editor = UserAccount.objects.create_user(
            email="reviewer@example.com",
            password="test-password",
            name="Not An Editor",
            role="student",
            position="Writer",
        )
        Assignment.objects.create(
            pitch=self.pitch,
            assigned_user=non_editor,
            assigned_role="Editor",
        )
        submission = WorkSubmission.objects.create(
            pitch=self.pitch,
            submitter=self.member,
            submission_url="https://example.com/work",
        )
        self.client.force_login(non_editor)

        self.client.post(self.submission_url, {
            "action_type": "editor_comment",
            "submission_id": str(submission.pk),
            "content": "This should not be saved.",
        })

        self.assertFalse(Comment.objects.filter(submission=submission).exists())
