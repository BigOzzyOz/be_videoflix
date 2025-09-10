from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from app_users.models import UserProfiles
from app_videos.models import VideoFile, Video

CustomUserModel = get_user_model()


class VideoProgressUpdateViewTests(APITestCase):
    def setUp(self):
        self.user = CustomUserModel.objects.create_user(
            username="videouser",
            email="video@example.com",
            password="pw",
            is_active=True,
            is_email_verified=True,
        )

        self.video = Video.objects.create(title="Testvideo", description="desc")
        self.profile = UserProfiles.objects.create(user=self.user, profile_name="TestProfile", preferred_language="en")
        self.video_file = VideoFile.objects.create(
            video=self.video,
            duration=100,
            original_file="test.mp4",
            language="de",
            localized_title="TestVideo",
            is_ready=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("update_video_progress", args=[self.profile.id, self.video_file.id])

    def test_post_valid_progress(self):
        response = self.client.post(self.url, {"current_time": 50})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("video_progress", response.data)

    def test_post_missing_current_time(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current_time", response.data)

    def test_post_invalid_current_time(self):
        response = self.client.post(self.url, {"current_time": "abc"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current_time", response.data)
        response = self.client.post(self.url, {"current_time": -10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("current_time", response.data)

    def test_delete_progress(self):
        self.client.post(self.url, {"current_time": 10})
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
