from rest_framework.test import APITestCase, force_authenticate
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from app_videos.models import Genres, Video
from app_videos.api.views import GenreVideoCountView


class VideoFileListViewTest(APITestCase):
    def test_list_view_exists(self):
        url = reverse("video_list")
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 403, 401])


class GenreVideoCountViewTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.genre1 = Genres.objects.create(name="Action")
        self.genre2 = Genres.objects.create(name="Comedy")
        video1 = Video.objects.create(title="Test Video 1", slug="test-video-1", description="desc")
        video2 = Video.objects.create(title="Test Video 2", slug="test-video-2", description="desc")
        self.genre1.videos.add(video1)
        self.genre2.videos.add(video2)

    def test_genre_video_count_view_exists(self):
        url = reverse("genre_video_count")
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 403, 401])

    def test_genre_video_count_view(self):
        request = self.factory.get("/api/genres/video-count/")
        force_authenticate(request, user=self.create_test_user())
        view = GenreVideoCountView.as_view()
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], 1)
        self.assertEqual(response.data["comedy"], 1)

    def create_test_user(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        return User.objects.create_user(username="testuser", password="testpass")
