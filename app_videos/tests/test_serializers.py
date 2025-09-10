from django.test import TestCase, RequestFactory
from app_videos.api.serializers import VideoFileSerializer
from app_videos.models import Video, VideoFile, Genres
from django.db.models.signals import post_save
from app_videos.signals import video_file_post_save
from django.core.files.uploadedfile import SimpleUploadedFile


class VideoFileSerializerTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/api/videos/")
        self.genre = Genres.objects.create(name="Action")
        self.video = Video.objects.create(title="Test Video", slug="test-video-serializer", description="desc")
        self.video.genres.add(self.genre)
        self.vf = VideoFile.objects.create(
            video=self.video,
            language="en",
            is_ready=True,
            thumbnail=SimpleUploadedFile("thumb.png", b"filecontent", content_type="image/png"),
            preview_file=SimpleUploadedFile("preview.mp4", b"filecontent", content_type="video/mp4"),
            hls_master_path="/media/hls/master.m3u8",
        )
        post_save.disconnect(video_file_post_save, sender=VideoFile)

    def tearDown(self):
        post_save.connect(video_file_post_save, sender=VideoFile)

    def test_serialize_video_file(self):
        video_obj = Video.objects.create(title="Test Video", description="desc")
        video_file = VideoFile.objects.create(
            video=video_obj, duration=10, original_file="uploads/test.mp4", language="en"
        )
        serializer = VideoFileSerializer(video_file)
        self.assertIn("language", serializer.data)

    def test_get_thumbnail_url(self):
        serializer = VideoFileSerializer(self.vf, context={"request": self.request})
        url = serializer.get_thumbnail_url(self.vf)
        self.assertTrue(url.endswith(self.vf.thumbnail.url))

    def test_get_preview_url(self):
        serializer = VideoFileSerializer(self.vf, context={"request": self.request})
        url = serializer.get_preview_url(self.vf)
        self.assertTrue(url.endswith(self.vf.preview_file.url))

    def test_get_hls_url(self):
        serializer = VideoFileSerializer(self.vf, context={"request": self.request})
        url = serializer.get_hls_url(self.vf)
        self.assertTrue(url.endswith(str(self.vf.hls_master_path)))

    def test_get_genres(self):
        serializer = VideoFileSerializer(self.vf, context={"request": self.request})
        genres = serializer.get_genres(self.vf)
        self.assertEqual(genres, [self.genre.name])
