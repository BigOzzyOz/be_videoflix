import uuid
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import get_language_from_request
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
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
from app_videos.models import VideoFile, VideoProgress

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
            browser_language = get_language_from_request(request)
            preferred_language = self.map_browser_to_video_language(browser_language)

            UserProfiles.objects.create(user=user, profile_name=user.username, preferred_language=preferred_language)

        return Response(
            {"message": "Email successfully verified. You can now login."},
            status=status.HTTP_200_OK,
        )

    def map_browser_to_video_language(self, browser_lang):
        """Map browser language to VideoFile language choices"""
        lang_code = browser_lang.split("-")[0].lower() if browser_lang else "en"
        language_mapping = {"de": "de", "en": "en", "fr": "fr", "es": "es", "it": "it"}
        return language_mapping.get(lang_code, "en")


class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = CustomUserModel.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class UserProfileListCreateView(generics.ListCreateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return UserProfiles.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        if UserProfiles.objects.filter(user=self.request.user).count() >= 4:
            raise ValidationError({"detail": "You can only have a maximum of 4 profiles."})
        if not serializer.validated_data.get("profile_name"):
            raise ValidationError({"profile_name": ["This field is required."]})
        serializer.save(user=self.request.user)


class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return UserProfiles.objects.filter(user=self.request.user)

    def get_object(self):
        queryset = self.get_queryset()
        obj = generics.get_object_or_404(queryset, pk=self.kwargs["profile_id"])
        self.check_object_permissions(self.request, obj)
        return obj


class LogoutView(APIView):
    permission_classes = (permissions.AllowAny,)
    authentication_classes = []

    def post(self, request):
        refresh_token = request.data.get("refresh_token")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass

        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)


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


class VideoProgressUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, profile_id, video_file_id):
        """Update video progress for a specific profile"""
        profile = get_object_or_404(UserProfiles, id=profile_id, user=request.user)
        video_file = get_object_or_404(VideoFile, id=video_file_id)
        current_time = request.data.get("current_time")

        if current_time is None:
            raise ValidationError({"current_time": "This field is required."})

        try:
            current_time = float(current_time)
        except (ValueError, TypeError):
            raise ValidationError({"current_time": "Must be a valid number."})

        if current_time < 0:
            raise ValidationError({"current_time": "Cannot be negative."})

        progress, created = VideoProgress.objects.get_or_create(
            profile=profile, video_file=video_file, defaults={"current_time": current_time}
        )

        progress.current_time = current_time
        progress.save()

        serializer = UserProfileSerializer(profile, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, profile_id, video_file_id):
        """Delete video progress for a specific profile"""
        profile = get_object_or_404(UserProfiles, id=profile_id, user=request.user)

        try:
            progress = VideoProgress.objects.get(profile=profile, video_file_id=video_file_id)
            progress.delete()

            serializer = UserProfileSerializer(profile, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except VideoProgress.DoesNotExist:
            raise ValidationError({"detail": "No progress found for this video."})
