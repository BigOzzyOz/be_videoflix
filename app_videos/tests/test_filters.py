from django.test import TestCase
from django.utils import timezone
from app_videos.models import Video, VideoFile, Genres
from app_videos.api.filters import VideoFileFilter


class VideoFileFilterTest(TestCase):
    def setUp(self):
        self.genre = Genres.objects.create(name="Action")
        self.video_recent = Video.objects.create(
            title="Recent Video",
            description="desc",
            release_date=timezone.now() - timezone.timedelta(days=10),
            is_published=True,
        )
        self.video_old = Video.objects.create(
            title="Old Video",
            description="desc",
            release_date=timezone.now() - timezone.timedelta(days=200),
            is_published=True,
        )
        self.video_recent.genres.add(self.genre)
        self.video_old.genres.add(self.genre)
        self.vf_recent = VideoFile.objects.create(video=self.video_recent, language="en", is_ready=True)
        self.vf_old = VideoFile.objects.create(video=self.video_old, language="en", is_ready=True)

    def test_filter_newly_released_true(self):
        filterset = VideoFileFilter({"newly_released": True}, queryset=VideoFile.objects.all())
        result = filterset.qs
        self.assertIn(self.vf_recent, result)
        self.assertNotIn(self.vf_old, result)

    def test_filter_newly_released_false(self):
        filterset = VideoFileFilter({"newly_released": False}, queryset=VideoFile.objects.all())
        result = filterset.qs
        self.assertIn(self.vf_recent, result)
        self.assertNotIn(self.vf_old, result)

    def test_filter_newly_released_false_no_videos(self):
        VideoFile.objects.all().delete()
        filterset = VideoFileFilter({"newly_released": False}, queryset=VideoFile.objects.all())
        result = filterset.qs
        self.assertEqual(list(result), [])
