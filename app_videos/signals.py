import time
import os
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rq import get_queue
from .models import VideoFile
from .tasks import (
    generate_hls_for_resolution,
    generate_master_playlist_waiting,
    generate_video_preview,
    generate_thumbnail_and_duration,
)


@receiver(post_save, sender=VideoFile)
def video_file_post_save(sender, instance, created, **kwargs):
    """Signal: enqueue file processing when new VideoFile is created."""
    if created and instance.original_file and not instance.is_ready:
        queue = get_queue("default", default_timeout=21600)
        queue.enqueue(check_file_and_start_processing, instance.id)


def check_file_and_start_processing(video_file_id, retry_count=0):
    """Check if file is ready and start processing or retry."""
    try:
        video_file = VideoFile.objects.get(id=video_file_id)
    except VideoFile.DoesNotExist:
        if retry_count < 10:
            _restart_file_check(video_file_id, retry_count)
            return
        else:
            print(f"VideoFile with id {video_file_id} still does not exist after 10 retries. Giving up.")
            return

    if not _is_file_ready(video_file.original_file):
        if retry_count < 10:
            _restart_file_check(video_file_id, retry_count)
            return
        else:
            print(f"File {video_file.original_file.name} is still not ready after 10 retries. Giving up.")
            return
    _enqueue_video_processing_jobs(video_file)


def _restart_file_check(video_file_id, retry_count):
    """Enqueue a delayed retry for file readiness."""
    queue = get_queue("default", default_timeout=21600)
    delay = min(30 + (retry_count * 30), 360)
    queue.enqueue_in(timedelta(seconds=delay), check_file_and_start_processing, video_file_id, retry_count + 1)


def _is_file_ready(file_field):
    """Return True if file exists, is readable, and stable."""
    try:
        if not file_field or not file_field.name:
            return False

        file_path = file_field.path

        if not os.path.exists(file_path):
            return False

        if not os.access(file_path, os.R_OK):
            return False

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False

        time.sleep(1)
        new_file_size = os.path.getsize(file_path)
        if new_file_size != file_size:
            return False

        try:
            with open(file_path, "rb") as f:
                f.read(1024)
        except IOError:
            return False

        return True

    except (ValueError, OSError, AttributeError) as e:
        print(f"Error checking file readiness: {e}")
        return False


def _enqueue_video_processing_jobs(instance):
    """Enqueue all video processing jobs for a file."""
    queue = get_queue("default", default_timeout=21600)
    queue.enqueue(generate_thumbnail_and_duration, instance.id)
    queue.enqueue(generate_video_preview, instance.id)
    for res in ["480p", "720p", "1080p"]:
        queue.enqueue(generate_hls_for_resolution, instance.id, res)
    queue.enqueue(generate_master_playlist_waiting, instance.id)
