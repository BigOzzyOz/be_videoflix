from rest_framework.views import exception_handler
from rest_framework.response import Response
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


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return Response(response.data, status=response.status_code)

    if isinstance(exc, (NotFound, Http404, ObjectDoesNotExist)):
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, PermissionDenied):
        return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, (ValidationError, TokenError)):
        return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

    if isinstance(exc, MethodNotAllowed):
        return Response({"detail": str(exc)}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    (print(f"Unhandled exception: {exc}, {context}"),)
    return Response(
        {"detail": "Internal server error. "},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
