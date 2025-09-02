from django.test import TestCase
from app_videos.models import Video, VideoFile, VideoProgress, Genres
from django.db.models.signals import post_save
from app_videos.signals import video_file_post_save
from app_users.models import UserProfiles
from django.contrib.auth import get_user_model


class VideoFileModelTest(TestCase):
    def setUp(self):
        post_save.disconnect(video_file_post_save, sender=VideoFile)

    def tearDown(self):
        post_save.connect(video_file_post_save, sender=VideoFile)

    def test_video_file_str(self):
        video_obj = Video.objects.create(title="Test Video", description="desc")
        video_file = VideoFile.objects.create(
            video=video_obj,
            duration=10,
            original_file="uploads/test.mp4",
            language="en",
        )
        self.assertIn("Test Video", str(video_file))


class VideoProgressModelTest(TestCase):
    def setUp(self):
        post_save.disconnect(video_file_post_save, sender=VideoFile)
        User = get_user_model()
        self.user = User.objects.create(username="tester", email="t@t.com")
        self.profile = UserProfiles.objects.create(user=self.user, profile_name="TestProfile", preferred_language="en")
        self.video = Video.objects.create(title="Test Video", description="desc")
        self.vf = VideoFile.objects.create(
            video=self.video, duration=100.0, original_file="uploads/test.mp4", language="en"
        )

    def tearDown(self):
        post_save.connect(video_file_post_save, sender=VideoFile)

    def test_video_progress_str(self):
        User = get_user_model()
        user = User.objects.create(username="tester2", email="t2@t.com")
        profile = UserProfiles.objects.create(user=user, profile_name="TestProfile2", preferred_language="en")
        video_obj = Video.objects.create(title="Test Video", description="desc", slug="test-video-progress-str")
        video_file = VideoFile.objects.create(
            video=video_obj,
            duration=10,
            original_file="uploads/test.mp4",
            language="en",
        )
        progress = VideoProgress.objects.create(profile=profile, video_file=video_file, current_time=10)
        self.assertIsInstance(str(progress), str)
        self.assertIn("TestProfile2", str(progress))

    def test_status_completed(self):
        vp = VideoProgress.objects.create(
            profile=self.profile,
            video_file=self.vf,
            current_time=95.0,
            progress_percentage=95.0,
            is_completed=True,
            is_started=True,
        )
        self.assertEqual(vp.status, "completed")

    def test_status_just_started(self):
        vp = VideoProgress.objects.create(
            profile=self.profile,
            video_file=self.vf,
            current_time=10.0,
            progress_percentage=2.0,
            is_completed=False,
            is_started=True,
        )
        self.assertEqual(vp.status, "continue_watching")

    def test_status_just_started_exact(self):
        video = Video.objects.create(title="Test Video", description="desc", slug="test-video-just-started")
        vf = VideoFile.objects.create(video=video, duration=200.0, original_file="uploads/test.mp4", language="en")
        vp = VideoProgress.objects.create(
            profile=self.profile,
            video_file=vf,
            current_time=6.0,
            progress_percentage=0.0,
            is_completed=False,
            is_started=True,
        )
        self.assertEqual(vp.status, "just_started")

    def test_status_not_started(self):
        vp = VideoProgress.objects.create(
            profile=self.profile,
            video_file=self.vf,
            current_time=0.0,
            progress_percentage=0.0,
            is_completed=False,
            is_started=False,
        )
        self.assertEqual(vp.status, "not_started")


class GenresModelTest(TestCase):
    def test_genres_str(self):
        genre = Genres.objects.create(name="Action")
        self.assertEqual(str(genre), "Action")


class VideoModelTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.profile = UserProfiles.objects.create(user=self.user, profile_name="TestUser")
        self.genre = Genres.objects.create(name="Action")
        self.video = Video.objects.create(title="Test Video", slug="test-video-models", description="desc")
        self.video.genres.add(self.genre)
        self.vf = VideoFile.objects.create(
            video=self.video, language="en", is_ready=True, duration=100.0, original_file="uploads/test.mp4"
        )

    def test_video_str(self):
        self.assertEqual(str(self.video), self.video.title)
