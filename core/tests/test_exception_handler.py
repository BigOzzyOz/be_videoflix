from django.test import TestCase
from rest_framework import status
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    MethodNotAllowed,
)
from rest_framework_simplejwt.exceptions import TokenError
from core.utils.exception_handler import custom_exception_handler


class DummyContext:
    pass


class DummyException(Exception):
    pass


class ExceptionHandlerTests(TestCase):
    def test_not_found(self):
        exc = NotFound("not found")
        resp = custom_exception_handler(exc, DummyContext())
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("not found", resp.data["detail"])

    def test_http404(self):
        exc = Http404("missing")
        resp = custom_exception_handler(exc, DummyContext())
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("missing", resp.data["detail"])

    def test_object_does_not_exist(self):
        exc = ObjectDoesNotExist("obj missing")
        resp = custom_exception_handler(exc, DummyContext())
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("obj missing", resp.data["detail"])

    def test_permission_denied(self):
        exc = PermissionDenied("forbidden")
        from unittest.mock import patch

        with patch("rest_framework.views.exception_handler", return_value=None):
            resp = custom_exception_handler(exc, DummyContext())
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(resp.data["detail"], str(exc))

    def test_validation_error(self):
        exc = ValidationError({"field": "invalid"})
        resp = custom_exception_handler(exc, DummyContext())
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("field", resp.data)

    def test_token_error(self):
        exc = TokenError("token fail")
        exc.detail = {"token": "fail"}
        resp = custom_exception_handler(exc, DummyContext())
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", resp.data)

    def test_authentication_failed(self):
        exc = AuthenticationFailed("auth fail")
        from unittest.mock import patch

        with patch("rest_framework.views.exception_handler", return_value=None):
            resp = custom_exception_handler(exc, DummyContext())
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp.data["detail"], str(exc))

    def test_not_authenticated(self):
        exc = NotAuthenticated("not auth")
        from unittest.mock import patch

        with patch("rest_framework.views.exception_handler", return_value=None):
            resp = custom_exception_handler(exc, DummyContext())
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(resp.data["detail"], str(exc))

    def test_method_not_allowed(self):
        exc = MethodNotAllowed("POST")
        from unittest.mock import patch

        with patch("rest_framework.views.exception_handler", return_value=None):
            resp = custom_exception_handler(exc, DummyContext())
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(resp.data["detail"], str(exc))

    def test_unhandled_exception(self):
        exc = DummyException("fail")
        resp = custom_exception_handler(exc, DummyContext())
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Internal server error", resp.data["detail"])
