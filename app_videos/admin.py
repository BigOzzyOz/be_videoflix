from django.contrib import admin
from .models import Video, VideoFile
from django.utils.html import format_html


class VideoFileInline(admin.TabularInline):
    model = VideoFile
    extra = 1

    readonly_fields = ("thumbnail_preview", "duration")
    fields = ("original_file", "resolution", "language", "is_default", "is_ready", "thumbnail_preview", "duration")

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="height: 100px;"/>', obj.thumbnail.url)
        return "-"

    thumbnail_preview.short_description = "Thumbnail"


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "is_published", "release_date", "created_at")
    list_filter = ("is_published", "release_date")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-created_at",)
    inlines = [VideoFileInline]  # Inline VideoFile im Video Admin anzeigen


@admin.register(VideoFile)
class VideoFileAdmin(admin.ModelAdmin):
    list_display = (
        "video",
        "resolution",
        "language",
        "is_ready",
        "is_default",
        "created_at",
        "thumbnail_preview",
        "duration",
    )
    readonly_fields = ("thumbnail_preview", "duration")
    list_filter = ("is_ready", "language", "resolution")
    search_fields = ("video__title",)
    raw_id_fields = ("video",)
    ordering = ("-created_at",)

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.thumbnail.url)
        return "-"

    thumbnail_preview.short_description = "Thumbnail"
