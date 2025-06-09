from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rq import get_queue  # <-- wichtig für RQ
from .models import VideoFile
from .tasks import generate_hls_versions, generate_thumbnail_and_duration


@receiver(post_save, sender=VideoFile)
def video_file_post_save(sender, instance, created, **kwargs):
    if created and instance.original_file:
        if not instance.is_ready and not instance.hls_master_path:
            # RQ-Job in die Queue geben
            queue = get_queue("default")
            queue.enqueue(generate_thumbnail_and_duration, instance.id)
            queue.enqueue(generate_hls_versions, instance.id)
