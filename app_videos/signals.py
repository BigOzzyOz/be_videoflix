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
    if created and instance.original_file and not instance.is_ready:
        queue = get_queue("default", default_timeout=21600)  # 6 hours

        queue.enqueue(generate_thumbnail_and_duration, instance.id)
        queue.enqueue(generate_video_preview, instance.id)

        for res in ["480p", "720p", "1080p"]:
            queue.enqueue(generate_hls_for_resolution, instance.id, res)

        queue.enqueue(generate_master_playlist_waiting, instance.id)
