from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from app_users.admin import CustomUserAdmin, UserProfileAdmin, VideoProgressAdmin
from app_users.models import CustomUserModel, UserProfiles
from app_videos.models import Video, VideoFile, VideoProgress


class TestCustomUserAdmin(TestCase):
    def setUp(self):
        self.user = CustomUserModel.objects.create(username="testuser", email="test@example.com")
        UserProfiles.objects.create(profile_name="Max", is_kid=False, user=self.user)
        UserProfiles.objects.create(profile_name="Anna", is_kid=True, user=self.user)
        self.admin = CustomUserAdmin(CustomUserModel, AdminSite())

    def test_display_profiles(self):
        result = self.admin.display_profiles(self.user)
        self.assertIn("Max", result)
        self.assertIn("Anna", result)
        self.assertIn("👶", result)

    def test_profile_count(self):
        result = self.admin.profile_count(self.user)
        self.assertEqual(result, "2/4")


class TestUserProfileAdmin(TestCase):
    def setUp(self):
        self.user = CustomUserModel.objects.create(username="profileuser", email="profile@example.com")
        self.profile = UserProfiles.objects.create(profile_name="Max", is_kid=False, user=self.user)
        self.video = Video.objects.create(title="Testvideo", description="desc")
        self.video_file1 = VideoFile.objects.create(
            video=self.video,
            duration=100.0,
            original_file="test1.mp4",
            language="de",
            localized_title="Test Video 1",
            is_ready=True,
        )
        self.video_file2 = VideoFile.objects.create(
            video=self.video,
            duration=200.0,
            original_file="test2.mp4",
            language="en",
            localized_title="Test Video 2",
            is_ready=True,
        )
        vp1 = VideoProgress.objects.create(
            profile=self.profile, video_file=self.video_file1, current_time=10, is_started=True, is_completed=False
        )
        vp2 = VideoProgress.objects.create(
            profile=self.profile, video_file=self.video_file2, current_time=0, is_started=True, is_completed=True
        )
        VideoProgress.objects.filter(pk=vp1.pk).update(current_time=3720, is_started=True, is_completed=False)
        VideoProgress.objects.filter(pk=vp2.pk).update(current_time=0, is_started=True, is_completed=True)
        self.admin = UserProfileAdmin(UserProfiles, AdminSite())

    def test_video_progress_count(self):
        result = self.admin.video_progress_count(self.profile)
        self.assertIn("2 started", result)
        self.assertIn("1 completed", result)

    def test_watch_time_display(self):
        result = self.admin.watch_time_display(self.profile)
        self.assertEqual(result, "1h 2m")

    def test_watch_time_display_zero(self):
        user = CustomUserModel.objects.create(username="emptyuser", email="empty@example.com")
        profile = UserProfiles.objects.create(profile_name="Empty", is_kid=False, user=user)
        admin = UserProfileAdmin(UserProfiles, AdminSite())
        result = admin.watch_time_display(profile)
        self.assertEqual(result, "0m")


class TestVideoProgressAdmin(TestCase):
    def setUp(self):
        self.user = CustomUserModel.objects.create(username="videouser", email="video@example.com")
        self.profile = UserProfiles.objects.create(profile_name="Max", is_kid=False, user=self.user)
        self.video = Video.objects.create(title="Testvideo", description="desc")
        self.video_file = VideoFile.objects.create(
            video=self.video,
            duration=125.0,
            original_file="test.mp4",
            language="de",
            localized_title="Test Video",
            is_ready=True,
        )
        vp = VideoProgress.objects.create(
            profile=self.profile, video_file=self.video_file, current_time=0, is_started=True, is_completed=False
        )
        VideoProgress.objects.filter(pk=vp.pk).update(
            progress_percentage=75.5, current_time=125, is_started=True, is_completed=False
        )
        self.vp = VideoProgress.objects.get(pk=vp.pk)
        self.admin = VideoProgressAdmin(VideoProgress, AdminSite())

    def test_video_title(self):
        result = self.admin.video_title(self.vp)
        self.assertEqual(result, "Test Video")

    def test_language(self):
        result = self.admin.language(self.vp)
        self.assertEqual(result, "DE")

    def test_progress_bar(self):
        result = self.admin.progress_bar(self.vp)
        self.assertIn("75.5%", result)
        self.assertIn("background:#007bff", result)

    def test_current_time_display(self):
        result = self.admin.current_time_display(self.vp)
        self.assertEqual(result, "02:05")

    def test_customusermodel_str(self):
        user = CustomUserModel(username="testuser")
        self.assertEqual(str(user), "testuser")

    def test_userprofiles_str(self):
        user = CustomUserModel(username="testuser")
        profile = UserProfiles(user=user, profile_name="TestProfile")
        self.assertEqual(str(profile), "testuser - TestProfile")
