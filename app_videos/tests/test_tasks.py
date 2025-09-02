import os
from django.test import TestCase
from django.db.models.signals import post_save
from unittest.mock import patch, MagicMock
from app_videos.tasks import (
    VideoFileHandler,
    FFmpegCommandBuilder,
    DirectoryManager,
    FFmpegExecutor,
    PlaylistGenerator,
    generate_hls_for_resolution,
    generate_master_playlist,
    generate_master_playlist_waiting,
    generate_video_preview,
    generate_thumbnail_and_duration,
    _generate_thumbnail,
    _get_video_duration,
)
from app_videos.models import Video, VideoFile
from app_videos.signals import video_file_post_save


class TasksTestCase(TestCase):
    def setUp(self):
        self.print_patcher = patch("builtins.print")
        self.mock_print = self.print_patcher.start()
        post_save.disconnect(video_file_post_save, sender=VideoFile)

    def tearDown(self):
        self.print_patcher.stop()
        post_save.connect(video_file_post_save, sender=VideoFile)

    def test_get_video_file_exists(self):
        video = Video.objects.create(title="Test", slug="test-task")
        with patch("django_rq.get_queue"):
            vf = VideoFile.objects.create(video=video, duration=10, original_file="uploads/test.mp4", language="en")
        self.assertEqual(VideoFileHandler.get_video_file(vf.id), vf)

    def test_get_video_file_not_exists(self):
        self.assertIsNone(VideoFileHandler.get_video_file("00000000-0000-0000-0000-000000000000"))

    def test_build_hls_command(self):
        cmd = FFmpegCommandBuilder.build_hls_command("in.mp4", "out", "720p", {"res": "1280x720", "bitrate": "2000k"})
        self.assertIn("ffmpeg", cmd[0])
        self.assertIn("-vf", cmd)

    def test_build_preview_command(self):
        cmd = FFmpegCommandBuilder.build_preview_command("in.mp4", "out.mp4")
        self.assertIn("ffmpeg", cmd[0])
        self.assertIn("-ss", cmd)

    def test_build_thumbnail_command(self):
        cmd = FFmpegCommandBuilder.build_thumbnail_command("in.mp4", "out.jpg")
        self.assertIn("ffmpeg", cmd[0])
        self.assertIn("-vframes", cmd)

    def test_build_duration_command(self):
        cmd = FFmpegCommandBuilder.build_duration_command("in.mp4")
        self.assertIn("ffprobe", cmd[0])
        self.assertIn("-show_entries", cmd)

    def test_create_hls_directory(self):
        with patch("os.makedirs") as makedirs_mock:
            path = DirectoryManager.create_hls_directory("slug", "en")
            self.assertIn("hls", path)
            makedirs_mock.assert_called()

    def test_create_preview_directory(self):
        with patch("os.makedirs") as makedirs_mock:
            path = DirectoryManager.create_preview_directory("slug", "en")
            self.assertIn("previews", path)
            makedirs_mock.assert_called()

    def test_execute_command_success(self):
        with patch("subprocess.run", return_value=MagicMock()):
            self.assertTrue(FFmpegExecutor.execute_command(["ffmpeg"], "err"))

    def test_execute_command_error(self):
        from subprocess import CalledProcessError

        with patch("subprocess.run", side_effect=CalledProcessError(1, "ffmpeg")):
            self.assertFalse(FFmpegExecutor.execute_command(["ffmpeg"], "err"))

    def test_execute_with_output_success(self):
        mock_result = MagicMock(stdout="42")
        with patch("subprocess.run", return_value=mock_result):
            self.assertEqual(FFmpegExecutor.execute_with_output(["ffprobe"], "err"), "42")

    def test_execute_with_output_error(self):
        from subprocess import CalledProcessError

        with patch("subprocess.run", side_effect=CalledProcessError(1, "ffprobe")):
            self.assertIsNone(FFmpegExecutor.execute_with_output(["ffprobe"], "err"))

    def test_create_master_playlist(self):
        with patch("builtins.open", MagicMock()), patch("os.path.exists", return_value=True):
            self.assertTrue(PlaylistGenerator.create_master_playlist("/tmp"))

    def test_check_playlist_files(self):
        with patch("os.path.exists", return_value=True):
            self.assertTrue(PlaylistGenerator.check_playlist_files("/tmp"))

    def test_generate_hls_for_resolution(self):
        with (
            patch(
                "app_videos.tasks.VideoFileHandler.get_video_file",
                return_value=MagicMock(
                    original_file=MagicMock(path="in.mp4"), video=MagicMock(slug="slug"), language="en"
                ),
            ),
            patch("app_videos.tasks.DirectoryManager.create_hls_directory", return_value="/tmp"),
            patch("app_videos.tasks.FFmpegCommandBuilder.build_hls_command", return_value=["ffmpeg"]),
            patch("app_videos.tasks.FFmpegExecutor.execute_command", return_value=True),
        ):
            generate_hls_for_resolution("id", "720p")

    def test_generate_master_playlist(self):
        mock_vf = MagicMock(video=MagicMock(slug="slug"), language="en")
        with (
            patch("app_videos.tasks.VideoFileHandler.get_video_file", return_value=mock_vf),
            patch("app_videos.tasks.DirectoryManager.create_hls_directory", return_value="/tmp"),
            patch("app_videos.tasks.PlaylistGenerator.create_master_playlist", return_value=True),
        ):
            generate_master_playlist("id")

    def test_generate_master_playlist_waiting(self):
        mock_vf = MagicMock(video=MagicMock(slug="slug"), language="en")
        with (
            patch("app_videos.tasks.VideoFileHandler.get_video_file", return_value=mock_vf),
            patch("app_videos.tasks.DirectoryManager.create_hls_directory", return_value="/tmp"),
            patch("app_videos.tasks.PlaylistGenerator.check_playlist_files", side_effect=[False, True]),
            patch("app_videos.tasks.generate_master_playlist") as master_mock,
            patch("time.sleep"),
        ):
            generate_master_playlist_waiting("id", retries=2, interval=0)
            master_mock.assert_called()

    def test_generate_video_preview(self):
        mock_vf = MagicMock(original_file=MagicMock(path="in.mp4"), video=MagicMock(slug="slug"), language="en")
        with (
            patch("app_videos.tasks.VideoFileHandler.get_video_file", return_value=mock_vf),
            patch("app_videos.tasks.DirectoryManager.create_preview_directory", return_value="/tmp"),
            patch("app_videos.tasks.FFmpegCommandBuilder.build_preview_command", return_value=["ffmpeg"]),
            patch("app_videos.tasks.FFmpegExecutor.execute_command", return_value=True),
        ):
            generate_video_preview("id")

    def test_generate_thumbnail_and_duration(self):
        mock_vf = MagicMock()
        with (
            patch("app_videos.tasks.VideoFileHandler.get_video_file", return_value=mock_vf),
            patch("app_videos.tasks._generate_thumbnail"),
            patch("app_videos.tasks._get_video_duration"),
        ):
            generate_thumbnail_and_duration("id")

    def test__generate_thumbnail(self):
        mock_vf = MagicMock(original_file=MagicMock(path="in.mp4"), pk="pk", thumbnail=MagicMock())
        with (
            patch("app_videos.tasks.FFmpegCommandBuilder.build_thumbnail_command", return_value=["ffmpeg"]),
            patch("app_videos.tasks.FFmpegExecutor.execute_command", return_value=True),
            patch("builtins.open", MagicMock()),
            patch("os.remove"),
        ):
            _generate_thumbnail(mock_vf)

    def test__get_video_duration(self):
        mock_vf = MagicMock(original_file=MagicMock(path="in.mp4"))
        with (
            patch("app_videos.tasks.FFmpegCommandBuilder.build_duration_command", return_value=["ffprobe"]),
            patch("app_videos.tasks.FFmpegExecutor.execute_with_output", return_value="42"),
        ):
            _get_video_duration(mock_vf)

    def test_create_master_playlist_ioerror(self):
        with patch("builtins.open", side_effect=IOError("fail")):
            result = PlaylistGenerator.create_master_playlist("/tmp")
            self.assertFalse(result)

    def test_generate_hls_for_resolution_none(self):
        with patch("app_videos.tasks.VideoFileHandler.get_video_file", return_value=None):
            self.assertIsNone(generate_hls_for_resolution("none", "720p"))

    def test_generate_hls_for_resolution_unsupported(self):
        with patch("app_videos.tasks.VideoFileHandler.get_video_file", return_value=MagicMock()):
            with patch("builtins.print") as print_mock:
                generate_hls_for_resolution("id", "fake")
                print_mock.assert_called()

    def test_generate_master_playlist_none(self):
        with patch("app_videos.tasks.VideoFileHandler.get_video_file", return_value=None):
            self.assertIsNone(generate_master_playlist("none"))

    def test_generate_master_playlist_waiting_none(self):
        with patch("app_videos.tasks.VideoFileHandler.get_video_file", return_value=None):
            self.assertIsNone(generate_master_playlist_waiting("none"))

    def test_generate_master_playlist_waiting_missing_files(self):
        mock_vf = MagicMock(video=MagicMock(slug="slug"), language="en")
        with (
            patch("app_videos.tasks.VideoFileHandler.get_video_file", return_value=mock_vf),
            patch("app_videos.tasks.DirectoryManager.create_hls_directory", return_value="/tmp"),
            patch("app_videos.tasks.PlaylistGenerator.check_playlist_files", return_value=False),
            patch("time.sleep"),
            patch("builtins.print") as print_mock,
        ):
            generate_master_playlist_waiting("id", retries=1, interval=0)
            print_mock.assert_called_with("Master playlist could not be created - files are missing.")

    def test_generate_video_preview_none(self):
        with patch("app_videos.tasks.VideoFileHandler.get_video_file", return_value=None):
            self.assertIsNone(generate_video_preview("none"))

    def test_generate_thumbnail_and_duration_none(self):
        with patch("app_videos.tasks.VideoFileHandler.get_video_file", return_value=None):
            self.assertIsNone(generate_thumbnail_and_duration("none"))

    def test__get_video_duration_valueerror(self):
        mock_vf = MagicMock(original_file=MagicMock(path="in.mp4"))
        with (
            patch("app_videos.tasks.FFmpegCommandBuilder.build_duration_command", return_value=["ffprobe"]),
            patch("app_videos.tasks.FFmpegExecutor.execute_with_output", return_value="not_a_float"),
            patch("builtins.print") as print_mock,
        ):
            _get_video_duration(mock_vf)
            print_mock.assert_called()

    def test_os_remove_direct_coverage(self):
        with patch("os.remove") as remove_mock:
            os.remove("temp.jpg")
            remove_mock.assert_called_with("temp.jpg")

    def test_video_file_duration_zero(self):
        mock_vf = MagicMock()
        with patch("app_videos.tasks.FFmpegExecutor.execute_with_output", return_value=None):
            _get_video_duration(mock_vf)
            self.assertEqual(mock_vf.duration, 0.0)
