import subprocess
import os
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from tempfile import NamedTemporaryFile
from .models import VideoFile


def generate_hls_versions(video_file_id):
    video_file = VideoFile.objects.get(id=video_file_id)

    input_path = video_file.original_file.path
    video_slug = video_file.video.slug
    output_dir = os.path.join(settings.MEDIA_ROOT, "hls", video_slug)

    os.makedirs(output_dir, exist_ok=True)

    resolutions = {
        "480p": "854x480",
        "720p": "1280x720",
        "1080p": "1920x1080",
    }

    variant_playlists = []

    for label, resolution in resolutions.items():
        output_file = os.path.join(output_dir, f"{label}.m3u8")
        command = [
            "ffmpeg",
            "-i",
            input_path,
            "-vf",
            f"scale={resolution}",
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
            "2000k",
            "-maxrate",
            "2000k",
            "-bufsize",
            "4000k",
            "-b:a",
            "128k",
            "-hls_segment_filename",
            os.path.join(output_dir, f"{label}_%03d.ts"),
            output_file,
        ]
        subprocess.run(command, check=True)
        variant_playlists.append(f"#EXT-X-STREAM-INF:BANDWIDTH=2000000,RESOLUTION={resolution}\n{label}.m3u8")

    # Master-Playlist schreiben
    master_playlist_path = os.path.join(output_dir, "master.m3u8")
    with open(master_playlist_path, "w") as f:
        f.write("#EXTM3U\n")
        for variant in variant_playlists:
            f.write(variant)

    # DB aktualisieren
    video_file.hls_master_path = f"{settings.MEDIA_URL}hls/{video_slug}/master.m3u8"
    video_file.is_ready = True
    video_file.save()


def generate_thumbnail_and_duration(video_file_id):
    video_file_instance = VideoFile.objects.get(id=video_file_id)
    video_path = video_file_instance.original_file.path

    with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_thumb:
        subprocess.run(
            ["ffmpeg", "-y", "-ss", "00:00:01.000", "-i", video_path, "-vframes", "1", temp_thumb.name],
            check=True,
        )
    with open(temp_thumb.name, "rb") as f:
        video_file_instance.thumbnail.save(f"{video_file_instance.pk}_thumb.jpg", ContentFile(f.read()), save=False)

    os.remove(temp_thumb.name)

    # Dauer auslesen
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            video_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    duration_seconds = float(result.stdout.strip())

    from datetime import timedelta

    video_file_instance.duration = timedelta(seconds=duration_seconds)

    video_file_instance.save()
