import time
import os
import subprocess
from django.core.files.base import ContentFile
from django.conf import settings
from tempfile import NamedTemporaryFile
from .models import VideoFile

HLS_RESOLUTIONS = {
    "480p": {"res": "854x480", "bitrate": "800k", "bandwidth": 800000},
    "720p": {"res": "1280x720", "bitrate": "2000k", "bandwidth": 2000000},
    "1080p": {"res": "1920x1080", "bitrate": "5000k", "bandwidth": 5000000},
}


class VideoFileHandler:
    """VideoFile DB access helper."""

    @staticmethod
    def get_video_file(video_file_id):
        """Return VideoFile by id or None."""
        try:
            return VideoFile.objects.get(id=video_file_id)
        except VideoFile.DoesNotExist:
            print(f"VideoFile with id {video_file_id} does not exist.")
            return None


class FFmpegCommandBuilder:
    """Builds FFmpeg/FFprobe commands."""

    @staticmethod
    def build_hls_command(input_path, output_dir, resolution_label, settings_dict):
        """FFmpeg command for HLS."""
        output_file = os.path.join(output_dir, f"{resolution_label}.m3u8")
        scale_filter = f"scale={settings_dict['res']}"
        bitrate = settings_dict["bitrate"]
        bufsize = str(int(bitrate[:-1]) * 2) + "k"

        return [
            "ffmpeg",
            "-i",
            input_path,
            "-vf",
            scale_filter,
            "-c:a",
            "aac",
            "-ar",
            "48000",
            "-c:v",
            "h264",
            "-profile:v",
            "main",
            "-crf",
            "20",
            "-sc_threshold",
            "0",
            "-g",
            "48",
            "-keyint_min",
            "48",
            "-hls_time",
            "4",
            "-hls_playlist_type",
            "vod",
            "-b:v",
            bitrate,
            "-maxrate",
            bitrate,
            "-bufsize",
            bufsize,
            "-b:a",
            "128k",
            "-hls_segment_filename",
            os.path.join(output_dir, f"{resolution_label}_%03d.ts"),
            output_file,
        ]

    @staticmethod
    def build_preview_command(input_path, output_path):
        """FFmpeg command for preview."""
        return [
            "ffmpeg",
            "-i",
            input_path,
            "-ss",
            "00:00:05",
            "-t",
            "00:00:20",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-strict",
            "experimental",
            "-b:v",
            "1000k",
            "-y",
            output_path,
        ]

    @staticmethod
    def build_thumbnail_command(input_path, output_path):
        """FFmpeg command for thumbnail."""
        return ["ffmpeg", "-y", "-ss", "00:00:10.000", "-i", input_path, "-vframes", "1", output_path]

    @staticmethod
    def build_duration_command(input_path):
        """FFprobe command for duration."""
        return [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            input_path,
        ]


class DirectoryManager:
    """Creates output directories."""

    @staticmethod
    def create_hls_directory(video_slug, language):
        """Create HLS output dir."""
        output_dir = os.path.join(settings.MEDIA_ROOT, "hls", video_slug, language)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    @staticmethod
    def create_preview_directory(video_slug, language):
        """Create preview output dir."""
        output_dir = os.path.join(settings.MEDIA_ROOT, "previews", video_slug, language)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir


class FFmpegExecutor:
    """Runs FFmpeg/FFprobe commands."""

    @staticmethod
    def execute_command(command, error_message):
        """Run FFmpeg command, handle errors."""
        try:
            subprocess.run(command, check=True, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            print(f"{error_message}: {e}")
            return False

    @staticmethod
    def execute_with_output(command, error_message):
        """Run command, return output."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"{error_message}: {e}")
            return None


class PlaylistGenerator:
    """Creates/checks HLS playlists."""

    @staticmethod
    def create_master_playlist(output_dir):
        """Create master playlist file."""
        master_path = os.path.join(output_dir, "master.m3u8")
        try:
            with open(master_path, "w") as f:
                f.write("#EXTM3U\n")
                for label, conf in HLS_RESOLUTIONS.items():
                    playlist = os.path.join(output_dir, f"{label}.m3u8")
                    if os.path.exists(playlist):
                        f.write(
                            f"#EXT-X-STREAM-INF:BANDWIDTH={conf['bandwidth']},RESOLUTION={conf['res']}\n{label}.m3u8\n"
                        )
            return True
        except IOError as e:
            print(f"Error writing master playlist: {e}")
            return False

    @staticmethod
    def check_playlist_files(output_dir):
        """Check all playlist files exist."""
        expected_files = ["480p.m3u8", "720p.m3u8", "1080p.m3u8"]
        return all(os.path.exists(os.path.join(output_dir, f)) for f in expected_files)


# Refactored Tasks
def generate_hls_for_resolution(video_file_id, resolution_label):
    """Generate HLS for one resolution."""
    video_file = VideoFileHandler.get_video_file(video_file_id)
    if not video_file:
        return

    if resolution_label not in HLS_RESOLUTIONS:
        print(f"Resolution {resolution_label} is not supported.")
        return

    settings_dict = HLS_RESOLUTIONS[resolution_label]
    input_path = video_file.original_file.path
    output_dir = DirectoryManager.create_hls_directory(video_file.video.slug, video_file.language)

    command = FFmpegCommandBuilder.build_hls_command(input_path, output_dir, resolution_label, settings_dict)

    success = FFmpegExecutor.execute_command(command, f"Error generating {resolution_label}")

    if success:
        print(f"{resolution_label} generation completed.")


def generate_master_playlist(video_file_id):
    """Generate master playlist for video."""
    video_file = VideoFileHandler.get_video_file(video_file_id)
    if not video_file:
        return

    output_dir = DirectoryManager.create_hls_directory(video_file.video.slug, video_file.language)

    if PlaylistGenerator.create_master_playlist(output_dir):
        video_file.hls_master_path = (
            f"{settings.MEDIA_URL}hls/{video_file.video.slug}/{video_file.language}/master.m3u8"
        )
        video_file.is_ready = True
        video_file.save()


def generate_master_playlist_waiting(video_file_id, retries=60, interval=30):
    """Wait for playlists, then master playlist."""
    video_file = VideoFileHandler.get_video_file(video_file_id)
    if not video_file:
        return

    output_dir = DirectoryManager.create_hls_directory(video_file.video.slug, video_file.language)

    for _ in range(retries):
        if PlaylistGenerator.check_playlist_files(output_dir):
            generate_master_playlist(video_file_id)
            return
        time.sleep(interval)

    print("Master playlist could not be created - files are missing.")


def generate_video_preview(video_file_id):
    """Generate video preview file."""
    video_file = VideoFileHandler.get_video_file(video_file_id)
    if not video_file:
        return

    input_path = video_file.original_file.path
    output_dir = DirectoryManager.create_preview_directory(video_file.video.slug, video_file.language)
    output_path = os.path.join(output_dir, "preview.mp4")

    command = FFmpegCommandBuilder.build_preview_command(input_path, output_path)

    success = FFmpegExecutor.execute_command(command, "Error generating video preview")

    if success:
        video_file.preview_file = f"previews/{video_file.video.slug}/{video_file.language}/preview.mp4"
        video_file.save()


def generate_thumbnail_and_duration(video_file_id):
    """Generate thumbnail and duration."""
    video_file = VideoFileHandler.get_video_file(video_file_id)
    if not video_file:
        return

    _generate_thumbnail(video_file)
    _get_video_duration(video_file)
    video_file.save()


def _generate_thumbnail(video_file):
    """Generate thumbnail for video file."""
    video_path = video_file.original_file.path

    try:
        with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_thumb:
            command = FFmpegCommandBuilder.build_thumbnail_command(video_path, temp_thumb.name)

            if FFmpegExecutor.execute_command(command, "Error generating thumbnail"):
                with open(temp_thumb.name, "rb") as f:
                    data = f.read()
                video_file.thumbnail.save(f"{video_file.pk}_thumb.jpg", ContentFile(data), save=False)
            os.remove(temp_thumb.name)
    except Exception as e:
        print(f"Error in thumbnail process: {e}")


def _get_video_duration(video_file):
    """Calculate video duration."""
    video_path = video_file.original_file.path
    command = FFmpegCommandBuilder.build_duration_command(video_path)

    duration_str = FFmpegExecutor.execute_with_output(command, "Error reading video duration")

    if duration_str:
        try:
            video_file.duration = float(duration_str)
        except ValueError as e:
            print(f"Error parsing video duration: {e}")
    else:
        video_file.duration = 0.0
