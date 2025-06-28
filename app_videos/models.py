import uuid
from django.db import models
from django.utils.text import slugify


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Video(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Video ID")
    title = models.CharField(max_length=255)
    genre = models.ManyToManyField(Genre, related_name="videos", blank=True, verbose_name="Genres")
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
    duration = models.DurationField(blank=True, null=True, help_text="Videolänge")
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)
    preview_file = models.FileField(upload_to="previews/", blank=True, null=True, help_text="Vorschau-Video")
    original_file = models.FileField(upload_to="uploads/")
    hls_master_path = models.URLField(blank=True, null=True)
    language = models.CharField(choices=LANGUAGE_CHOICES, default="en")
    is_default = models.BooleanField(default=False)
    is_ready = models.BooleanField(default=False, help_text="HLS-Conversion abgeschlossen")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("video", "language")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.video.title} – [{self.language}]"
