from django.test import TestCase
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from app_videos.api.pagination import VideoPagination


class VideoPaginationTest(TestCase):
    def test_pagination_class_exists(self):
        self.assertTrue(hasattr(VideoPagination, "__module__"))

    def test_get_paginated_response(self):
        paginator = VideoPagination()
        data = [{"id": 1, "title": "Test Video"}, {"id": 2, "title": "Another Video"}]

        class DummyQueryset(list):
            def count(self):
                return len(self)

        queryset = DummyQueryset(data)
        factory = APIRequestFactory()
        request = factory.get("/fake-url/", {"page_size": 10})
        request.query_params = request.GET
        page = paginator.paginate_queryset(queryset, request)
        response = paginator.get_paginated_response(page)
        self.assertIsInstance(response, Response)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["results"], page)
