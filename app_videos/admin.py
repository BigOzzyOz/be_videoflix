from django.contrib import admin
from django.utils.html import format_html
from .models import Video, VideoFile, Genre


class VideoFileInline(admin.TabularInline):
    model = VideoFile
    extra = 1
    readonly_fields = ("thumbnail_preview", "duration")
    fields = ("original_file", "language", "is_default", "is_ready", "thumbnail_preview", "duration")

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="height: 100px;"/>', obj.thumbnail.url)
        return "-"

    thumbnail_preview.short_description = "Thumbnail"


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "get_genres", "is_published", "release_date", "created_at")
    list_filter = ("is_published", "release_date", "genre")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-created_at",)
    inlines = [VideoFileInline]
    filter_horizontal = ("genre",)

    def get_genres(self, obj):
        return ", ".join([genre.name for genre in obj.genre.all()])

    get_genres.short_description = "Genres"


@admin.register(VideoFile)
class VideoFileAdmin(admin.ModelAdmin):
    list_display = (
        "video",
        "language",
        "is_ready",
        "is_default",
        "created_at",
        "thumbnail_preview",
        "duration",
    )
    readonly_fields = ("thumbnail_preview", "duration")
    list_filter = ("is_ready", "language")
    search_fields = ("video__title",)
    raw_id_fields = ("video",)
    ordering = ("-created_at",)

    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="height: 50px;"/>', obj.thumbnail.url)
        return "-"

    thumbnail_preview.short_description = "Thumbnail"


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
