from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from app_videos import admin
from app_videos.admin import GenreAdmin, VideoAdmin, VideoFileAdmin, VideoFileInline
from app_videos.models import Genres, Video, VideoFile
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io
from django.core.files.base import ContentFile
from unittest.mock import patch, MagicMock
from app_videos.utils import get_video_file_status


class VideoAdminTest(TestCase):
    def setUp(self):
        self.admin = VideoAdmin(Video, AdminSite())
        self.genre = Genres.objects.create(name="Action")
        self.video = Video.objects.create(title="Test Video", description="desc")
        self.video.genres.add(self.genre)
        self.vf = VideoFile.objects.create(
            video=self.video,
            duration=10,
            original_file=SimpleUploadedFile("test.mp4", b"filecontent"),
            language="en",
            is_ready=True,
            localized_title="Localized Title",
            localized_description="Localized Description",
        )

    def test_get_genres(self):
        result = self.admin.get_genres(self.video)
        self.assertIn("Action", result)

    def test_available_languages_short(self):
        result = self.admin.available_languages_short(self.video)
        self.assertIn("en", result)

    def test_available_languages_short_none_ready(self):
        video_not_ready = Video.objects.create(title="Test Video 2", description="desc")
        video_not_ready.genres.add(self.genre)
        result = self.admin.available_languages_short(video_not_ready)
        self.assertEqual(result, "None ready")

    def test_available_languages_detailed(self):
        result = self.admin.available_languages_detailed(self.video)
        self.assertIn("✅", str(result))

    def test_available_languages_detailed_no_files(self):
        video = Video.objects.create(
            title="Test Video", slug="test-video-unique1", description="desc", is_published=True
        )
        admin_instance = VideoAdmin(Video, AdminSite())
        result = admin_instance.available_languages_detailed(video)
        self.assertEqual(result, "No video files uploaded yet")

    def test_available_languages_detailed_processing_status(self):
        video = Video.objects.create(
            title="Test Video", slug="test-video-unique2", description="desc", is_published=True
        )
        VideoFile.objects.create(video=video, language="en", is_ready=False)
        admin_instance = VideoAdmin(Video, AdminSite())
        result = admin_instance.available_languages_detailed(video)
        self.assertIn("⏳", result)
        self.assertIn("Processing", result)


class VideoFileAdminTest(TestCase):
    def test_status_display_uploading_started_registry(self):
        self.vf.is_ready = False
        self.vf.save()
        from unittest.mock import patch, MagicMock
        from app_videos.utils import get_video_file_status

        with patch("django_rq.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_queue.jobs = []
            mock_queue.failed_job_registry.get_job_ids.return_value = []
            mock_queue.started_job_registry.get_job_ids.return_value = ["jobid1"]
            mock_job = MagicMock()
            mock_job.args = [self.vf.id]
            mock_queue.fetch_job.side_effect = lambda job_id: mock_job if job_id == "jobid1" else None
            mock_get_queue.return_value = mock_queue
            result = get_video_file_status(self.vf)
            self.assertIn("uploading", str(result))

    def test_status_display_pending_fallback(self):
        self.vf.is_ready = False
        self.vf.save()

        with patch("django_rq.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_queue.jobs = []
            mock_queue.failed_job_registry.get_job_ids.return_value = []
            mock_queue.started_job_registry.get_job_ids.return_value = []
            mock_queue.fetch_job.return_value = None
            mock_get_queue.return_value = mock_queue
            result = get_video_file_status(self.vf)
            self.assertIn("not started", str(result))

    def test_status_display_done(self):
        self.vf.is_ready = True
        self.vf.save()
        result = self.admin.status_display(self.vf)
        self.assertIn("✅", str(result))

    def test_status_display_error(self):
        self.vf.is_ready = False
        self.vf.save()

        with patch("django_rq.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_queue.failed_job_registry.get_job_ids.return_value = ["jobid1"]
            mock_queue.fetch_job.return_value = MagicMock(args=[self.vf.id])
            mock_queue.jobs = []
            mock_get_queue.return_value = mock_queue
            result = self.admin.status_display(self.vf)
            self.assertIn("❌", str(result))

    def test_status_display_uploading(self):
        self.vf.is_ready = False
        self.vf.save()

        with patch("django_rq.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            job = MagicMock(args=[self.vf.id], is_started=True)
            mock_queue.jobs = [job]
            mock_queue.failed_job_registry.get_job_ids.return_value = []
            mock_queue.fetch_job.return_value = None
            mock_get_queue.return_value = mock_queue
            result = self.admin.status_display(self.vf)
            self.assertIn("⏳", str(result))

    def test_status_display_pending(self):
        self.vf.is_ready = False
        self.vf.save()

        with patch("django_rq.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            job = MagicMock(args=[self.vf.id], is_started=False)
            mock_queue.jobs = [job]
            mock_queue.failed_job_registry.get_job_ids.return_value = []
            mock_queue.fetch_job.return_value = None
            mock_get_queue.return_value = mock_queue
            result = self.admin.status_display(self.vf)
            self.assertIn("🕒", str(result))

    def setUp(self):
        self.admin = VideoFileAdmin(VideoFile, AdminSite())
        self.genre = Genres.objects.create(name="Action")
        self.video = Video.objects.create(title="Test Video", description="desc")
        self.video.genres.add(self.genre)
        image = Image.new("RGB", (100, 100), color="red")
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        thumbnail_file = SimpleUploadedFile("thumb.png", img_bytes.read(), content_type="image/png")
        self.vf = VideoFile.objects.create(
            video=self.video,
            duration=10,
            original_file=SimpleUploadedFile("test.mp4", b"filecontent"),
            language="en",
            is_ready=True,
            thumbnail=thumbnail_file,
            localized_title="Localized Title",
            localized_description="Localized Description",
        )

    def test_thumbnail_preview(self):
        result = self.admin.thumbnail_preview(self.vf)
        self.assertTrue("img" in str(result) or result == "-")

    def test_display_title_admin(self):
        result = self.admin.display_title_admin(self.vf)
        self.assertIn("Localized Title", result)

    def test_display_description_admin(self):
        result = self.admin.display_description_admin(self.vf)
        self.assertIn("Localized Description", result)

    def test_thumbnail_preview_with_thumbnail(self):
        result = self.admin.thumbnail_preview(self.vf)
        self.assertIn('<img src="', str(result))
        self.assertIn('style="height: 50px;"', str(result))

    def test_display_title_admin_origin(self):
        self.vf.localized_title = ""
        self.vf.save()
        result = self.admin.display_title_admin(self.vf)
        self.assertIn("📄", result)
        self.assertIn("(origin)", result)
        self.assertIn(self.video.title, result)

    def test_display_description_admin_origin(self):
        self.vf.localized_description = ""
        self.vf.save()
        result = self.admin.display_description_admin(self.vf)
        self.assertIn("📄", result)
        self.assertIn("... (origin)", result)
        self.assertIn(self.video.description[:100], result)

    def test_thumbnail_preview_no_thumbnail(self):
        self.vf.thumbnail = None
        self.vf.save()
        result = self.admin.thumbnail_preview(self.vf)
        self.assertEqual(result, "-")


class GenreAdminTest(TestCase):
    def setUp(self):
        self.admin = GenreAdmin(Genres, AdminSite())
        self.genre = Genres.objects.create(name="Action")
        self.video = Video.objects.create(title="Test Video", description="desc")
        self.genre.videos.add(self.video)

    def test_video_count(self):
        count = self.admin.video_count(self.genre)
        self.assertEqual(count, 1)
        self.genre.videos.remove(self.video)
        count = self.admin.video_count(self.genre)
        self.assertEqual(count, 0)

    def test_genre_admin_exists(self):
        self.assertTrue(hasattr(admin, "GenreAdmin"))


class VideoFileInlineTest(TestCase):
    def test_status_display_pending_fallback(self):
        self.vf.is_ready = False
        self.vf.save()

        with patch("django_rq.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_queue.jobs = []
            mock_queue.failed_job_registry.get_job_ids.return_value = []
            mock_queue.started_job_registry.get_job_ids.return_value = []
            mock_queue.fetch_job.return_value = None
            mock_get_queue.return_value = mock_queue
            result = get_video_file_status(self.vf)
            self.assertIn("not started", str(result))

    def test_status_display_done(self):
        self.vf.is_ready = True
        self.vf.save()
        result = self.inline.status_display(self.vf)
        self.assertIn("✅", str(result))

    def test_status_display_error(self):
        self.vf.is_ready = False
        self.vf.save()

        with patch("django_rq.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_queue.failed_job_registry.get_job_ids.return_value = ["jobid1"]
            mock_queue.fetch_job.return_value = MagicMock(args=[self.vf.id])
            mock_queue.jobs = []
            mock_get_queue.return_value = mock_queue
            result = self.inline.status_display(self.vf)
            self.assertIn("❌", str(result))

    def test_status_display_uploading(self):
        self.vf.is_ready = False
        self.vf.save()

        with patch("django_rq.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            job = MagicMock(args=[self.vf.id], is_started=True)
            mock_queue.jobs = [job]
            mock_queue.failed_job_registry.get_job_ids.return_value = []
            mock_queue.fetch_job.return_value = None
            mock_get_queue.return_value = mock_queue
            result = self.inline.status_display(self.vf)
            self.assertIn("⏳", str(result))

    def test_status_display_pending(self):
        self.vf.is_ready = False
        self.vf.save()

        with patch("django_rq.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            job = MagicMock(args=[self.vf.id], is_started=False)
            mock_queue.jobs = [job]
            mock_queue.failed_job_registry.get_job_ids.return_value = []
            mock_queue.fetch_job.return_value = None
            mock_get_queue.return_value = mock_queue
            result = self.inline.status_display(self.vf)
            self.assertIn("🕒", str(result))

    def setUp(self):
        self.inline = VideoFileInline(VideoFile, AdminSite())
        self.genre = Genres.objects.create(name="Action")
        self.video = Video.objects.create(title="Test Video", description="desc")
        self.video.genres.add(self.genre)
        self.vf = VideoFile.objects.create(
            video=self.video,
            duration=10,
            original_file=SimpleUploadedFile("test.mp4", b"filecontent"),
            language="en",
            is_ready=True,
        )

    def test_thumbnail_preview(self):
        result = self.inline.thumbnail_preview(self.vf)
        self.assertTrue("img" in str(result) or result == "-")

    def test_thumbnail_preview_line_23(self):
        result = self.inline.thumbnail_preview(self.vf)
        self.assertTrue(isinstance(result, str) or hasattr(result, "__html__"))


class VideoFileInlineLine23Test(TestCase):
    def setUp(self):
        self.inline = VideoFileInline(VideoFile, AdminSite())
        self.genre = Genres.objects.create(name="Action")
        self.video = Video.objects.create(title="Test Video", description="desc")
        self.video.genres.add(self.genre)
        image = Image.new("RGB", (10, 10), color="red")
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        thumbnail_file = ContentFile(img_bytes.read(), "thumb.png")
        self.vf = VideoFile.objects.create(
            video=self.video,
            duration=10,
            original_file=SimpleUploadedFile("test.mp4", b"filecontent"),
            language="en",
            is_ready=True,
            thumbnail=thumbnail_file,
        )

    def test_thumbnail_preview_img_tag(self):
        result = self.inline.thumbnail_preview(self.vf)
        self.assertIn("<img", str(result))
        self.assertIn('style="height: 80px;"', str(result))
