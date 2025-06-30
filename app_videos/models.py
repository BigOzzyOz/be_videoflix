import uuid
from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class Genres(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Video(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Video ID")
    genres = models.ManyToManyField(Genres, related_name="videos", blank=True, verbose_name="Genres")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, blank=True)
    release_date = models.DateField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class VideoFileManager(models.Manager):
    def published_and_ready(self):
        return self.filter(
            is_ready=True, video__is_published=True, video__release_date__lte=timezone.now()
        ).select_related("video")


class VideoFile(models.Model):
    LANGUAGE_CHOICES = (
        ("en", "English"),
        ("de", "Deutsch"),
        ("fr", "Français"),
        ("es", "Español"),
        ("it", "Italiano"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Video File ID")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="video_files")
    duration = models.FloatField(default=0.0, help_text="Duration of the video in seconds")
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)
    preview_file = models.FileField(upload_to="previews/", blank=True, null=True, help_text="Preview video file")
    original_file = models.FileField(upload_to="uploads/")
    hls_master_path = models.FileField(blank=True, null=True)
    language = models.CharField(choices=LANGUAGE_CHOICES, default="en")
    localized_title = models.CharField(max_length=255, blank=True, help_text="Title in the specific language")
    localized_description = models.TextField(blank=True, help_text="Description in the specific language")
    is_ready = models.BooleanField(default=False, help_text="HLS conversion completed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = VideoFileManager()

    class Meta:
        unique_together = ("video", "language")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.video.title} – [{self.language}]"

    @property
    def display_title(self):
        """Returns localized title if available, otherwise falls back to video title"""
        return self.localized_title or self.video.title

    @property
    def display_description(self):
        """Returns localized description if available, otherwise falls back to video description"""
        return self.localized_description or self.video.description
