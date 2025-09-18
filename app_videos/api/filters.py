from django_filters import rest_framework as filters
from django.utils import timezone
from django.utils.timezone import localtime
from app_videos.models import VideoFile
from django.db.models import Max
from datetime import timedelta


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    """Custom filter for filtering by multiple character values (e.g., languages)."""

    pass


class VideoFileFilter(filters.FilterSet):
    """
    FilterSet for VideoFile API endpoints.
    Supports filtering by title, genres, published status, language, readiness, and newly released videos.
    """

    title = filters.CharFilter(field_name="video__title", lookup_expr="icontains")
    genres = filters.CharFilter(field_name="video__genres__name", lookup_expr="iexact")
    published = filters.BooleanFilter(field_name="video__is_published")
    newly_released = filters.BooleanFilter(field_name="video__release_date", method="filter_newly_released")
    language = CharInFilter(field_name="language", lookup_expr="in")
    is_ready = filters.BooleanFilter()

    class Meta:
        model = VideoFile
        fields = ["title", "genres", "published", "newly_released", "language", "is_ready"]

    def filter_newly_released(self, queryset, name, value):
        """
        Filter for newly released videos:
        - If value is True: return videos released in the last 90 days.
        - If value is False: return only the most recently released video(s).
        - If no videos exist: return an empty queryset.
        """
        now = localtime(timezone.now())
        if value:
            return queryset.filter(video__release_date__gte=(now - timedelta(days=90)).date())
        latest_date = queryset.aggregate(latest=Max("video__release_date"))["latest"]
        if latest_date:
            return queryset.filter(video__release_date=latest_date)
        return queryset.none()
