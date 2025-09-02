from django.test import TestCase
from unittest.mock import patch, MagicMock
from app_videos.models import Video, VideoFile
from app_videos.signals import (
    video_file_post_save,
    check_file_and_start_processing,
    _restart_file_check,
    _is_file_ready,
    _enqueue_video_processing_jobs,
)


class SignalsTestCase(TestCase):
    def setUp(self):
        self.print_patcher = patch("builtins.print")
        self.mock_print = self.print_patcher.start()

    def tearDown(self):
        self.print_patcher.stop()

    def test_video_file_post_save_enqueues(self):
        with patch("app_videos.signals.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_get_queue.return_value = mock_queue
            video = Video.objects.create(title="Test", slug="test-signal")
            vf = VideoFile.objects.create(video=video, duration=10, original_file="uploads/test.mp4", language="en")
            video_file_post_save(VideoFile, vf, True)
            self.assertTrue(mock_queue.enqueue.called)

    def test_check_file_and_start_processing_retries(self):
        with patch("app_videos.signals.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_get_queue.return_value = mock_queue
            with patch("app_videos.signals.VideoFile.objects.get", side_effect=VideoFile.DoesNotExist):
                with patch("app_videos.signals._restart_file_check") as retry_mock:
                    check_file_and_start_processing("fake_id", 0)
                    self.assertTrue(retry_mock.called)

    def test_check_file_and_start_processing_ready(self):
        with patch("app_videos.signals.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_get_queue.return_value = mock_queue
            video = Video.objects.create(title="Test", slug="test-signal-ready")
            vf = VideoFile.objects.create(video=video, duration=10, original_file="uploads/test.mp4", language="en")
            with patch("app_videos.signals.VideoFile.objects.get", return_value=vf):
                with patch("app_videos.signals._is_file_ready", return_value=True):
                    with patch("app_videos.signals._enqueue_video_processing_jobs") as jobs_mock:
                        check_file_and_start_processing(vf.id, 0)
                        self.assertTrue(jobs_mock.called)

    def test_restart_file_check_enqueues(self):
        with patch("app_videos.signals.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_get_queue.return_value = mock_queue
            _restart_file_check("vid", 1)
            self.assertTrue(mock_queue.enqueue_in.called)

    def test_is_file_ready_false(self):
        file_field = MagicMock()
        file_field.name = None
        self.assertFalse(_is_file_ready(file_field))

    def test_is_file_ready_no_name(self):
        file_field = MagicMock()
        file_field.name = None
        self.assertFalse(_is_file_ready(file_field))

    def test_is_file_ready_not_exists(self):
        file_field = MagicMock()
        file_field.name = "file.mp4"
        file_field.path = "file.mp4"
        with patch("os.path.exists", return_value=False):
            self.assertFalse(_is_file_ready(file_field))

    def test_is_file_ready_not_accessible(self):
        file_field = MagicMock()
        file_field.name = "file.mp4"
        file_field.path = "file.mp4"
        with patch("os.path.exists", return_value=True), patch("os.access", return_value=False):
            self.assertFalse(_is_file_ready(file_field))

    def test_is_file_ready_empty_file(self):
        file_field = MagicMock()
        file_field.name = "file.mp4"
        file_field.path = "file.mp4"
        with (
            patch("os.path.exists", return_value=True),
            patch("os.access", return_value=True),
            patch("os.path.getsize", return_value=0),
        ):
            self.assertFalse(_is_file_ready(file_field))

    def test_is_file_ready_size_changed(self):
        file_field = MagicMock()
        file_field.name = "file.mp4"
        file_field.path = "file.mp4"
        with (
            patch("os.path.exists", return_value=True),
            patch("os.access", return_value=True),
            patch("os.path.getsize", side_effect=[10, 20]),
            patch("time.sleep", return_value=None),
        ):
            self.assertFalse(_is_file_ready(file_field))

    def test_is_file_ready_ioerror(self):
        file_field = MagicMock()
        file_field.name = "file.mp4"
        file_field.path = "file.mp4"
        with (
            patch("os.path.exists", return_value=True),
            patch("os.access", return_value=True),
            patch("os.path.getsize", return_value=10),
            patch("time.sleep", return_value=None),
            patch("builtins.open", side_effect=IOError),
        ):
            self.assertFalse(_is_file_ready(file_field))

    def test_is_file_ready_valueerror(self):
        file_field = MagicMock()
        file_field.name = "file.mp4"
        file_field.path = "file.mp4"
        with patch("os.path.exists", side_effect=ValueError):
            with patch("builtins.print") as print_mock:
                self.assertFalse(_is_file_ready(file_field))
                print_mock.assert_called()

    def test_enqueue_video_processing_jobs(self):
        with patch("app_videos.signals.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_get_queue.return_value = mock_queue
            instance = MagicMock()
            instance.id = "vid"
            _enqueue_video_processing_jobs(instance)
            self.assertGreaterEqual(mock_queue.enqueue.call_count, 4)

    def test_check_file_and_start_processing_does_not_exist_gives_up(self):
        with patch("app_videos.signals.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_get_queue.return_value = mock_queue
            with patch("app_videos.signals.VideoFile.objects.get", side_effect=VideoFile.DoesNotExist):
                with patch("builtins.print") as print_mock:
                    check_file_and_start_processing("fake_id", 10)
                    print_mock.assert_called_with(
                        "VideoFile with id fake_id still does not exist after 10 retries. Giving up."
                    )

    def test_check_file_and_start_processing_file_not_ready_gives_up(self):
        with patch("app_videos.signals.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_get_queue.return_value = mock_queue
            video = Video.objects.create(title="Test", slug="test-signal-not-ready")
            vf = VideoFile.objects.create(video=video, duration=10, original_file="uploads/test.mp4", language="en")
            with patch("app_videos.signals.VideoFile.objects.get", return_value=vf):
                with patch("app_videos.signals._is_file_ready", return_value=False):
                    with patch("builtins.print") as print_mock:
                        check_file_and_start_processing(vf.id, 10)
                        print_mock.assert_called_with(
                            f"File {vf.original_file.name} is still not ready after 10 retries. Giving up."
                        )

    def test_is_file_ready_true(self):
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"1234567890" * 200)  # >1KB
            tmp.flush()
            tmp.close()
            file_field = MagicMock()
            file_field.name = tmp.name
            file_field.path = tmp.name
            with (
                patch("os.path.exists", return_value=True),
                patch("os.access", return_value=True),
                patch("os.path.getsize", side_effect=[2000, 2000]),
                patch("time.sleep", return_value=None),
            ):
                self.assertTrue(_is_file_ready(file_field))
            os.unlink(tmp.name)

    def test_check_file_and_start_processing_file_not_ready_retries(self):
        with patch("app_videos.signals.get_queue") as mock_get_queue:
            mock_queue = MagicMock()
            mock_get_queue.return_value = mock_queue
            video = Video.objects.create(title="Test", slug="test-signal-file-not-ready")
            vf = VideoFile.objects.create(video=video, duration=10, original_file="uploads/test.mp4", language="en")
            with patch("app_videos.signals.VideoFile.objects.get", return_value=vf):
                with patch("app_videos.signals._is_file_ready", return_value=False):
                    with patch("app_videos.signals._restart_file_check") as retry_mock:
                        check_file_and_start_processing(vf.id, 2)
                        retry_mock.assert_called_once_with(vf.id, 2)
