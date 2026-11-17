from datetime import time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.register.models import UserAccount
from .models import (
    Assignment,
    Comment,
    Notification,
    Pitch,
    PitchRoleNeed,
    VolunteerRequest,
    VolunteerResponse,
    WorkSubmission,
)


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


class PitchBrowseTests(TestCase):
    def setUp(self):
        self.member = UserAccount.objects.create_user(
            email="pitch-writer@example.com",
            password="pitch-member-password",
            name="Pitch Writer",
            role="student",
            position="Writer",
        )
        self.open_pitch = Pitch.objects.create(
            submitter=self.member,
            pitch_title="Open community story",
            pitch_type="Article",
            target_date=timezone.localdate() + timedelta(days=4),
            target_time=time(10, 0),
            status="open",
        )
        PitchRoleNeed.objects.create(
            pitch=self.open_pitch,
            role="Writer",
            slots_needed=2,
        )
        PitchRoleNeed.objects.create(
            pitch=self.open_pitch,
            role="Editor",
            slots_needed=1,
        )
        Assignment.objects.create(
            pitch=self.open_pitch,
            assigned_user=self.member,
            assigned_role="Writer",
        )
        self.artist_pitch = Pitch.objects.create(
            pitch_title="Design an event poster",
            pitch_type="Design",
            target_date=timezone.localdate() + timedelta(days=5),
            target_time=time(11, 0),
            status="open",
        )
        PitchRoleNeed.objects.create(
            pitch=self.artist_pitch,
            role="Artist",
            slots_needed=1,
        )
        self.closed_pitch = Pitch.objects.create(
            pitch_title="Closed community story",
            pitch_type="Article",
            target_date=timezone.localdate() - timedelta(days=1),
            target_time=time(10, 0),
            status="completed",
        )
        PitchRoleNeed.objects.create(
            pitch=self.closed_pitch,
            role="Writer",
            slots_needed=1,
        )
        self.url = reverse("home:pitches")

    def test_open_pitches_are_filtered_by_member_position_and_remaining_slots(self):
        self.client.force_login(self.member)

        response = self.client.get(self.url)

        self.assertContains(response, "Open community story")
        self.assertNotContains(response, "Design an event poster")
        self.assertNotContains(response, "Closed community story")
        self.assertContains(response, "1 spot")

    def test_search_includes_closed_pitches_with_closed_status(self):
        self.client.force_login(self.member)

        response = self.client.get(self.url, {"q": "community story"})

        self.assertContains(response, "Open community story")
        self.assertContains(response, "Closed community story")
        self.assertContains(response, "pitch-status-pill is-closed")

    def test_member_can_request_an_open_role_and_slot_is_reserved(self):
        self.client.force_login(self.member)
        volunteer_request = VolunteerRequest.objects.create(
            pitch=self.open_pitch,
            requester=self.member,
        )

        response = self.client.post(self.url, {
            "pitch_id": str(self.open_pitch.pk),
            "role": "Writer",
        })

        self.assertRedirects(response, self.url)
        self.assertTrue(VolunteerResponse.objects.filter(
            volunteer_request=volunteer_request,
            volunteer=self.member,
            role="Writer",
        ).exists())
        self.assertContains(self.client.get(self.url), "Request sent for Writer")

    def test_member_cannot_request_a_role_that_does_not_match_their_position(self):
        self.client.force_login(self.member)

        self.client.post(self.url, {
            "pitch_id": str(self.open_pitch.pk),
            "role": "Editor",
        })

        self.assertFalse(VolunteerResponse.objects.filter(volunteer=self.member).exists())

    def test_pitch_submission_saves_selected_roles_and_slot_counts(self):
        self.client.force_login(self.member)

        response = self.client.post(reverse("home:home"), {
            "action_type": "create_pitch",
            "pitch_title": "New campus feature",
            "pitch_type": "Article",
            "target_date": (timezone.localdate() + timedelta(days=8)).isoformat(),
            "target_time": "13:30",
            "needed_roles": ["writer", "artist"],
            "slots_writer": "3",
            "slots_artist": "1",
        })

        self.assertRedirects(response, reverse("home:home"))
        pitch = Pitch.objects.get(pitch_title="New campus feature")
        self.assertEqual(
            dict(pitch.role_needs.values_list("role", "slots_needed")),
            {"Writer": 3, "Artist": 1},
        )
