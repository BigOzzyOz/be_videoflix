import subprocess
import os
from datetime import timedelta
from django.core.files.base import ContentFile
from django.conf import settings
from tempfile import NamedTemporaryFile
from .models import VideoFile


def process_video_file(video_file_id):
    """
    Process the video file to generate HLS versions, a preview, and a thumbnail.
    This function is intended to be run as a background task.
    """
    generate_hls_versions(video_file_id)
    generate_video_preview(video_file_id)
    generate_thumbnail_and_duration(video_file_id)


def generate_hls_versions(video_file_id):
    try:
        video_file = VideoFile.objects.get(id=video_file_id)
    except VideoFile.DoesNotExist:
        print(f"VideoFile with id {video_file_id} does not exist.")
        return

    input_path = video_file.original_file.path
    video_slug = video_file.video.slug
    output_dir = os.path.join(settings.MEDIA_ROOT, "hls", video_slug)

    os.makedirs(output_dir, exist_ok=True)

    resolutions = {
        "480p": {"res": "854x480", "bitrate": "800k", "bandwidth": 800000},
        "720p": {"res": "1280x720", "bitrate": "2000k", "bandwidth": 2000000},
        "1080p": {"res": "1920x1080", "bitrate": "5000k", "bandwidth": 5000000},
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
        try:
            subprocess.run(command, check=True)
            variant_playlists.append(f"#EXT-X-STREAM-INF:BANDWIDTH=2000000,RESOLUTION={resolution}\n{label}.m3u8")
        except subprocess.CalledProcessError as e:
            print(f"Fehler bei der Erstellung der HLS-Version {label}: {e}")
            return

    # Master-Playlist schreiben
    master_playlist_path = os.path.join(output_dir, "master.m3u8")
    try:
        with open(master_playlist_path, "w") as f:
            f.write("#EXTM3U\n")
            for variant in variant_playlists:
                f.write(variant)
    except IOError as e:
        print(f"Fehler beim Schreiben der Master-Playlist: {e}")
        return

    # DB aktualisieren
    video_file.hls_master_path = f"{settings.MEDIA_URL}hls/{video_slug}/master.m3u8"
    video_file.is_ready = True
    video_file.save()


def generate_video_preview(video_file_id):
    try:
        video_file = VideoFile.objects.get(id=video_file_id)
    except VideoFile.DoesNotExist:
        print(f"VideoFile with id {video_file_id} does not exist.")
        return

    input_path = video_file.original_file.path
    video_slug = video_file.video.slug

    output_dir = os.path.join(settings.MEDIA_ROOT, "previews", video_slug)
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, "preview.mp4")

    command = [
        "ffmpeg",
        "-i",
        input_path,
        "-ss",
        "00:00:05",  # Startzeitpunkt
        "-t",
        "00:00:20",  # Dauer
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

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Generieren der Video-Vorschau: {e}")
        return

    # optional: Preview-Datei im Model speichern
    video_file.preview_file = f"previews/{video_slug}/preview.mp4"
    video_file.save()


def generate_thumbnail_and_duration(video_file_id):
    try:
        video_file_instance = VideoFile.objects.get(id=video_file_id)
    except VideoFile.DoesNotExist:
        print(f"VideoFile with id {video_file_id} does not exist.")
        return

    video_path = video_file_instance.original_file.path

    try:
        with NamedTemporaryFile(suffix=".jpg", delete=False) as temp_thumb:
            subprocess.run(
                ["ffmpeg", "-y", "-ss", "00:00:10.000", "-i", video_path, "-vframes", "1", temp_thumb.name],
                check=True,
            )
        with open(temp_thumb.name, "rb") as f:
            video_file_instance.thumbnail.save(f"{video_file_instance.pk}_thumb.jpg", ContentFile(f.read()), save=False)
        os.remove(temp_thumb.name)
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Generieren des Thumbnails: {e}")
        return

    # Dauer auslesen
    try:
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
        video_file_instance.duration = timedelta(seconds=duration_seconds)
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Auslesen der Videodauer: {e}")
        return

    video_file_instance.save()
