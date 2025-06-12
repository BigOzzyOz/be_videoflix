from django.db.models.signals import post_save
from django.dispatch import receiver
from django_rq import get_queue
from .models import VideoFile
from .tasks import process_video_file


@receiver(post_save, sender=VideoFile)
def video_file_post_save(sender, instance, created, **kwargs):
    if created and instance.original_file:
        if not instance.is_ready and not instance.hls_master_path:
            queue = get_queue("default")
            queue.enqueue(process_video_file, instance.id)
