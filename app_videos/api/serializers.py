from rest_framework import serializers
from app_videos.models import VideoFile


class VideoFileSerializer(serializers.ModelSerializer):
    """
    Serializer for VideoFile model, providing custom fields for URLs, genres, languages, and localization.
    """

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
        """
        Return absolute URL for thumbnail if present, else None.
        """
        if obj.thumbnail:
            return self.context["request"].build_absolute_uri(obj.thumbnail.url)
        return None

    def get_preview_url(self, obj):
        """
        Return absolute URL for preview file if present, else None.
        """
        if obj.preview_file:
            return self.context["request"].build_absolute_uri(obj.preview_file.url)
        return None

    def get_hls_url(self, obj):
        """
        Return absolute URL for HLS master path if present, else None.
        """
        if obj.hls_master_path:
            return self.context["request"].build_absolute_uri(obj.hls_master_path)
        return None

    def get_genres(self, obj):
        """
        Return a list of genre names for the related video.
        """
        if obj.video.genres.exists():
            return [g.name for g in obj.video.genres.all()]
        return []

    def get_available_languages(self, obj):
        """
        Return a dict of ready languages and their VideoFile IDs for the video.
        """
        video_files = obj.video.video_files.filter(is_ready=True)
        return {vf.language: str(vf.id) for vf in video_files}

    def get_title(self, obj):
        """
        Return localized title if available, else original title.
        """
        return obj.display_title

    def get_description(self, obj):
        """
        Return localized description if available, else original description.
        """
        return obj.display_description
