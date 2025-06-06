from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from app_users.api.serializers import (
    RegisterSerializer,
    CustomUserSerializer,
    MyTokenObtainPairSerializer,
    UserProfileSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from app_users.models import UserProfiles
from app_users.utils import send_verification_email, send_password_reset_email
import uuid
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

CustomUserModel = get_user_model()


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = (permissions.AllowAny,)


class RegisterView(generics.CreateAPIView):
    queryset = CustomUserModel.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        send_verification_email(user, self.request)


class EmailVerifyView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, token):
        try:
            token_uuid = uuid.UUID(token)
            user = CustomUserModel.objects.get(email_verification_token=token_uuid, is_active=False)
        except (ValueError, CustomUserModel.DoesNotExist, TypeError):
            return Response(
                {"detail": "Invalid or expired verification token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = True
        user.is_email_verified = True
        user.email_verification_token = None
        user.save()

        if not UserProfiles.objects.filter(user=user).exists():
            UserProfiles.objects.create(user=user, profile_name=user.username)

        return Response(
            {"message": "Email successfully verified. You can now login."},
            status=status.HTTP_200_OK,
        )


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = CustomUserModel.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class UserProfileListCreateView(generics.ListCreateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProfiles.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if UserProfiles.objects.filter(user=self.request.user).count() >= 4:
            raise ValidationError({"detail": "You can only have a maximum of 4 profiles."})
        serializer.save(user=self.request.user)


class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProfiles.objects.filter(user=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        obj = generics.get_object_or_404(queryset, pk=self.kwargs["profile_id"])
        self.check_object_permissions(self.request, obj)
        return obj


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({"detail": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = CustomUserModel.objects.get(email=email, is_active=True)
            user.password_reset_token = uuid.uuid4()
            user.password_reset_token_created_at = timezone.now()
            user.save(update_fields=["password_reset_token", "password_reset_token_created_at"])
            send_password_reset_email(user, request)
        except CustomUserModel.DoesNotExist:
            pass

        return Response(
            {"message": "If an account with this email exists, a password reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_uuid_str = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            if not isinstance(token_uuid_str, str):
                raise ValueError("Token must be a string.")
            token_uuid = uuid.UUID(token_uuid_str)
            user = CustomUserModel.objects.get(password_reset_token=token_uuid)
        except (ValueError, CustomUserModel.DoesNotExist, TypeError):
            return Response({"detail": "Invalid or expired password reset token."}, status=status.HTTP_400_BAD_REQUEST)

        timeout_hours = getattr(settings, "PASSWORD_RESET_TIMEOUT_HOURS", 1)
        if user.password_reset_token_created_at < timezone.now() - timedelta(hours=timeout_hours):
            user.password_reset_token = None
            user.password_reset_token_created_at = None
            user.save(update_fields=["password_reset_token", "password_reset_token_created_at"])
            return Response({"detail": "Password reset token has expired."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.password_reset_token = None
        user.password_reset_token_created_at = None
        user.save()

        return Response({"message": "Password has been reset successfully."}, status=status.HTTP_200_OK)
