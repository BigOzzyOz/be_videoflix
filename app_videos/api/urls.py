from django.urls import path
from app_videos.api.views import VideoFileDetailView, VideoFileListView, GenreVideoCountView

urlpatterns = [
    path("", VideoFileListView.as_view(), name="video_list"),
    path("<uuid:pk>/", VideoFileDetailView.as_view(), name="video_detail"),
    path("genre-count/", GenreVideoCountView.as_view(), name="genre_video_count"),
]
