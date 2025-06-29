from django_filters import rest_framework as filters
from django.utils import timezone
from app_videos.models import VideoFile


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class VideoFileFilter(filters.FilterSet):
    title = filters.CharFilter(field_name="video__title", lookup_expr="icontains")
    genres = filters.CharFilter(field_name="video__genres__name", lookup_expr="iexact")
    published = filters.BooleanFilter(field_name="video__is_published")
    newly_released = filters.BooleanFilter(field_name="video__release_date", method="filter_newly_released")
    language = CharInFilter(field_name="language", lookup_expr="in")
    is_ready = filters.BooleanFilter()
    is_default = filters.BooleanFilter()

    class Meta:
        model = VideoFile
        fields = ["title", "genres", "published", "newly_released", "language", "is_ready", "is_default"]

    def filter_newly_released(self, queryset, name, value):
        if value:
            return queryset.filter(video__release_date__gte=timezone.now() - timezone.timedelta(days=90))
