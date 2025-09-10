from django.db.models import Count
from rest_framework import generics, status
from rest_framework.response import Response
from app_videos.models import VideoFile, Genres
from .filters import VideoFileFilter
from .serializers import VideoFileSerializer
from .pagination import VideoPagination


class VideoFileListView(generics.ListAPIView):
    """List published and ready video files."""

    queryset = VideoFile.objects.published_and_ready()
    serializer_class = VideoFileSerializer
    filterset_class = VideoFileFilter
    pagination_class = VideoPagination


class VideoFileDetailView(generics.RetrieveAPIView):
    """Retrieve a single published and ready video file."""

    queryset = VideoFile.objects.published_and_ready()
    serializer_class = VideoFileSerializer


class GenreVideoCountView(generics.GenericAPIView):
    """Return video count for each genre."""

    def get(self, request):
        queryset = Genres.objects.annotate(video_count=Count("videos"))
        data = {genres.name.lower(): genres.video_count for genres in queryset}
        return Response(data, status=status.HTTP_200_OK)
