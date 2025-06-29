from rest_framework import serializers
from app_videos.models import VideoFile


class VideoFileSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    hls_url = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    title = serializers.CharField(source="video.title", read_only=True)
    description = serializers.CharField(source="video.description", read_only=True)

    class Meta:
        model = VideoFile
        fields = [
            "id",
            "title",
            "genres",
            "language",
            "duration",
            "thumbnail_url",
            "preview_url",
            "hls_url",
            "is_ready",
            "is_default",
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

    def get_genre(self, obj):
        if obj.video.genres.exists():
            return [g.name for g in obj.video.genres.all()]
        return []
