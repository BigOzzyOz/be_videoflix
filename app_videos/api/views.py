from django.db.models import Count
from rest_framework import generics
from rest_framework.response import Response
from app_videos.models import VideoFile, Genre
from .filters import VideoFileFilter
from .serializers import VideoFileSerializer
from .pagination import VideoPagination


class VideoFileListView(generics.ListAPIView):
    queryset = VideoFile.objects.filter(is_ready=True).select_related("video")
    serializer_class = VideoFileSerializer
    filterset_class = VideoFileFilter
    pagination_class = VideoPagination


class VideoFileDetailView(generics.RetrieveAPIView):
    queryset = VideoFile.objects.filter(is_ready=True).select_related("video")
    serializer_class = VideoFileSerializer


class VideoFileSummaryView(generics.RetrieveAPIView):
    queryset = VideoFile.objects.filter(is_ready=True).select_related("video")
    serializer_class = VideoFileSerializer


class GenreVideoCountView(generics.RetrieveAPIView):
    def get(self, request):
        queryset = Genre.objects.annotate(video_count=Count("videos"))
        data = {genre.name.lower(): genre.video_count for genre in queryset}
        return Response(data)
