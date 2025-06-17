from django.urls import path
from app_videos.api.views import VideoFileDetailView, VideoFileListView

urlpatterns = [
    path("", VideoFileListView.as_view(), name="video_list"),
    path("<uuid:pk>/", VideoFileDetailView.as_view(), name="video_detail"),
]
