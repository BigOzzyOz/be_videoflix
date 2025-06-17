from rest_framework import generics
from app_videos.api.filters import VideoFileFilter
from app_videos.api.serializers import VideoFileSerializer
from app_videos.models import VideoFile
from .pagination import VideoPagination


class VideoFileListView(generics.ListAPIView):
    queryset = VideoFile.objects.filter(is_ready=True).select_related("video")
    serializer_class = VideoFileSerializer
    filterset_class = VideoFileFilter
    pagination_class = VideoPagination


class VideoFileDetailView(generics.RetrieveAPIView):
    queryset = VideoFile.objects.filter(is_ready=True).select_related("video")
    serializer_class = VideoFileSerializer
