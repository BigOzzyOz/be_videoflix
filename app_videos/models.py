from django.db import models
from django.utils.text import slugify


class Video(models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=100, blank=True, help_text="Genre des Videos")
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
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="video_files")
    duration = models.DurationField(blank=True, null=True, help_text="Videolänge")
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)
    preview_file = models.FileField(upload_to="previews/", blank=True, null=True, help_text="Vorschau-Video")
    original_file = models.FileField(upload_to="uploads/")
    hls_master_path = models.URLField(blank=True, null=True)
    resolution = models.CharField(max_length=20, blank=True, help_text="z. B. 1080p, 720p")
    language = models.CharField(max_length=50, default="en")
    is_default = models.BooleanField(default=False)
    is_ready = models.BooleanField(default=False, help_text="HLS-Conversion abgeschlossen")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("video", "resolution", "language")
        ordering = ["resolution"]

    def __str__(self):
        return f"{self.video.title} – {self.resolution or 'Original'} [{self.language}]"
