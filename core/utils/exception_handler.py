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


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # If DRF's default handler provides a response, use its data directly
        # This ensures that the original error structure (e.g., for ValidationError)
        # is preserved, which is what many tests expect.
        return Response(response.data, status=response.status_code)

    # Custom handling for specific unhandled exceptions or to standardize other errors
    if isinstance(exc, (NotFound, Http404, ObjectDoesNotExist)):
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, PermissionDenied):
        return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

    # It's generally better to let DRF handle ValidationErrors, but if one slips through:
    if isinstance(exc, ValidationError):  # This might be redundant if response above catches it
        return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return Response({"detail": str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

    if isinstance(exc, MethodNotAllowed):
        return Response({"detail": str(exc)}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    # Default catch-all for unhandled exceptions
    return Response(
        {"detail": "Internal server error."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
