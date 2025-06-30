from rest_framework import serializers
from app_videos.models import VideoFile


class VideoFileSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    hls_url = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    available_languages = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = VideoFile
        fields = [
            "id",
            "title",
            "description",
            "genres",
            "language",
            "available_languages",
            "duration",
            "thumbnail_url",
            "preview_url",
            "hls_url",
            "is_ready",
            "created_at",
            "updated_at",
        ]

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return self.context["request"].build_absolute_uri(obj.thumbnail.url)
        return None

    def get_preview_url(self, obj):
        if obj.preview_file:
            return self.context["request"].build_absolute_uri(obj.preview_file.url)
        return None

    def get_hls_url(self, obj):
        if obj.hls_master_path:
            return self.context["request"].build_absolute_uri(obj.hls_master_path)
        return None

    def get_genres(self, obj):
        if obj.video.genres.exists():
            return [g.name for g in obj.video.genres.all()]
        return []

    def get_available_languages(self, obj):
        """Returns all available languages with their VideoFile IDs"""
        video_files = obj.video.video_files.filter(is_ready=True)
        return {vf.language: str(vf.id) for vf in video_files}

    def get_title(self, obj):
        """Returns localized title if available, otherwise original title"""
        return obj.display_title

    def get_description(self, obj):
        """Returns localized description if available, otherwise original description"""
        return obj.display_description
