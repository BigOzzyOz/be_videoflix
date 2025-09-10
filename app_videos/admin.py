from django.contrib import admin
from django.utils.html import format_html
from .models import Video, VideoFile, Genres


class VideoFileInline(admin.TabularInline):
    """Inline admin for VideoFile objects in Video admin."""

    model = VideoFile
    extra = 1
    readonly_fields = ("thumbnail_preview", "duration")
    fields = (
        "original_file",
        "language",
        "localized_title",
        "localized_description",
        "is_ready",
        "thumbnail_preview",
        "duration",
    )

    def thumbnail_preview(self, obj):
        """Return HTML img tag for thumbnail or '-' if not available."""
        if obj.thumbnail:
            return format_html('<img src="{}" style="height: 80px;"/>', obj.thumbnail.url)
        return "-"

    thumbnail_preview.short_description = "Thumbnail"


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin configuration for Video model."""

    list_display = ("title", "get_genres", "available_languages_short", "is_published", "release_date", "created_at")
    list_filter = ("is_published", "release_date", "genres")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-created_at",)
    inlines = [VideoFileInline]
    filter_horizontal = ("genres",)
    readonly_fields = ("available_languages_detailed",)

    fieldsets = (
        ("Basic Information", {"fields": ("title", "slug", "description", "genres")}),
        ("Publishing", {"fields": ("is_published", "release_date")}),
        (
            "Available Languages",
            {"fields": ("available_languages_detailed",), "description": "Languages with completed HLS conversion"},
        ),
    )

    def get_genres(self, obj):
        """Return comma-separated genre names for a video."""
        return ", ".join([genres.name for genres in obj.genres.all()])

    def available_languages_short(self, obj):
        """Return short list of ready languages for list display."""
        ready_languages = obj.video_files.filter(is_ready=True).values_list("language", flat=True)
        if ready_languages:
            return ", ".join(ready_languages)
        return "None ready"

    def available_languages_detailed(self, obj):
        """Return detailed language status for detail view."""
        video_files = obj.video_files.all().order_by("language")
        if not video_files.exists():
            return "No video files uploaded yet"
        language_status = []
        for vf in video_files:
            lang_display = dict(VideoFile.LANGUAGE_CHOICES).get(vf.language, vf.language)
            if vf.is_ready:
                status = f"✅ {lang_display} ({vf.language})"
            else:
                status = f"⏳ {lang_display} ({vf.language}) - Processing"
            language_status.append(status)
        return format_html("<br>".join(language_status))

    get_genres.short_description = "Genres"
    available_languages_short.short_description = "Languages"
    available_languages_detailed.short_description = "Available Languages"


@admin.register(VideoFile)
class VideoFileAdmin(admin.ModelAdmin):
    """Admin configuration for VideoFile model."""

    list_display = (
        "video",
        "language",
        "display_title_admin",
        "is_ready",
        "created_at",
        "thumbnail_preview",
        "duration",
    )
    readonly_fields = ("thumbnail_preview", "duration", "display_title_admin", "display_description_admin")
    list_filter = ("is_ready", "language")
    search_fields = ("video__title", "localized_title", "localized_description")
    raw_id_fields = ("video",)
    ordering = ("-created_at",)

    fieldsets = (
        ("Video Reference", {"fields": ("video",)}),
        (
            "File Information",
            {"fields": ("original_file", "language", "duration", "thumbnail", "thumbnail_preview", "preview_file")},
        ),
        (
            "Localization",
            {
                "fields": (
                    "localized_title",
                    "localized_description",
                    "display_title_admin",
                    "display_description_admin",
                ),
                "description": "Language-specific title and description. If empty, defaults to video's main title/description.",
            },
        ),
        ("HLS & Status", {"fields": ("hls_master_path", "is_ready")}),
    )

    def thumbnail_preview(self, obj):
        """Return HTML img tag for thumbnail or '-' if not available."""
        if obj.thumbnail:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.thumbnail.url)
        return "-"

    def display_title_admin(self, obj):
        """Show effective title with origin indicator."""
        if obj.localized_title:
            return f"🌐 {obj.localized_title}"
        return f"📄 {obj.video.title} (origin)"

    def display_description_admin(self, obj):
        """Show effective description with origin indicator."""
        if obj.localized_description:
            return f"🌐 {obj.localized_description[:100]}..."
        return f"📄 {obj.video.description[:100]}... (origin)"

    thumbnail_preview.short_description = "Thumbnail"
    display_title_admin.short_description = "Effective Title"
    display_description_admin.short_description = "Effective Description"


@admin.register(Genres)
class GenreAdmin(admin.ModelAdmin):
    """Admin configuration for Genres model."""

    list_display = ("name", "video_count")
    search_fields = ("name",)

    def video_count(self, obj):
        """Return the number of videos for a genre."""
        return obj.videos.count()

    video_count.short_description = "Videos"
