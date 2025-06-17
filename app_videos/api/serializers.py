from rest_framework import serializers
from app_videos.models import VideoFile


class VideoFileSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    hls_url = serializers.SerializerMethodField()
    title = serializers.CharField(source="video.title", read_only=True)
    genre = serializers.CharField(source="video.genre", read_only=True)

    class Meta:
        model = VideoFile
        fields = [
            "id",
            "title",
            "genre",
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
