import uuid
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Genres(models.Model):
    """Genre/category for videos."""

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Genres"
        verbose_name_plural = "Genre"

    def __str__(self):
        """String representation: genre name."""
        return self.name


class Video(models.Model):
    """Main video object."""

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
        """Auto-generate slug from title if not set."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        """String representation: video title."""
        return self.title


class VideoFileManager(models.Manager):
    """Custom queryset for video files."""

    def published_and_ready(self):
        """Return only published and ready video files."""
        return self.filter(
            is_ready=True, video__is_published=True, video__release_date__lte=timezone.now()
        ).select_related("video")


class VideoFile(models.Model):
    """File and metadata for a video in a specific language."""

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
        verbose_name = "Video File"
        verbose_name_plural = "Video Files"

    def __str__(self):
        """String representation: video title and language."""
        return f"{self.video.title} – [{self.language}]"

    @property
    def display_title(self):
        """Returns localized title if available, otherwise falls back to video title"""
        return self.localized_title or self.video.title

    @property
    def display_description(self):
        """Returns localized description if available, otherwise falls back to video description"""
        return self.localized_description or self.video.description


class VideoProgress(models.Model):
    """Tracks user progress for a video file."""

    profile = models.ForeignKey("app_users.UserProfiles", on_delete=models.CASCADE, related_name="video_progress")
    video_file = models.ForeignKey(VideoFile, on_delete=models.CASCADE, related_name="progress_entries")

    current_time = models.FloatField(
        default=0.0, validators=[MinValueValidator(0.0)], help_text="Current playback position in seconds"
    )

    progress_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Progress as percentage (0-100)",
    )

    is_completed = models.BooleanField(default=False)
    is_started = models.BooleanField(default=False)
    completion_count = models.PositiveIntegerField(default=0)
    total_watch_time = models.FloatField(default=0.0)

    first_watched = models.DateTimeField(null=True, blank=True)
    last_watched = models.DateTimeField(auto_now=True)
    last_completed = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "video_file")
        ordering = ["-last_watched"]
        verbose_name = "Video Progress"
        verbose_name_plural = "Video Progress Entries"

    def save(self, *args, **kwargs):
        """Update progress, completion, and watch time on save."""
        if not self.first_watched and self.current_time > 0:
            self.first_watched = timezone.now()

        if self.video_file.duration > 0:
            self.progress_percentage = (self.current_time / self.video_file.duration) * 100

            was_completed = self.is_completed
            self.is_completed = self.progress_percentage >= 90
            self.is_started = self.current_time > 5

            if self.is_completed:
                self.current_time = 0
                self.progress_percentage = 0.0
                if not was_completed:
                    self.completion_count += 1
                    self.last_completed = timezone.now()
                    self.total_watch_time += self.video_file.duration
                self.is_started = False
            elif not self.is_completed and was_completed:
                pass

        super().save(*args, **kwargs)

    @property
    def status(self):
        """Returns the current status of the video progress."""
        if self.is_completed:
            return "completed"
        elif self.is_started and self.progress_percentage >= 5:
            return "continue_watching"
        elif self.is_started:
            return "just_started"
        else:
            return "not_started"

    def __str__(self):
        """String representation: profile, title, percent."""
        return f"{self.profile.profile_name} - {self.video_file.display_title} ({self.progress_percentage:.1f}%)"
