from rest_framework.pagination import PageNumberPagination


class VideoPagination(PageNumberPagination):
    """Video pagination."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        """Paginated response."""
        return super().get_paginated_response(data)
