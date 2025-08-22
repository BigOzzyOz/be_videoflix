from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from app_users.models import UserProfiles
import uuid

CustomUserModel = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    video_progress = serializers.SerializerMethodField()
    watch_statistics = serializers.SerializerMethodField()

    class Meta:
        model = UserProfiles
        fields = [
            "id",
            "profile_name",
            "preferred_language",
            "video_progress",
            "watch_statistics",
        ]

    def get_video_progress(self, obj):
        """All video progress with status"""
        progress_qs = obj.video_progress.select_related("video_file__video").order_by("-last_watched")

        return [
            {
                "video_file_id": str(p.video_file.id),
                "title": p.video_file.display_title,
                "thumbnail_url": (
                    self.context["request"].build_absolute_uri(p.video_file.thumbnail.url)
                    if p.video_file.thumbnail and self.context.get("request")
                    else (p.video_file.thumbnail.url if p.video_file.thumbnail else None)
                ),
                "current_time": p.current_time,
                "progress_percentage": round(p.progress_percentage, 1),
                "duration": p.video_file.duration,
                "status": p.status,
                "is_completed": p.is_completed,
                "is_started": p.is_started,
                "completion_count": p.completion_count,
                "total_watch_time": p.total_watch_time,
                "first_watched": p.first_watched,
                "last_watched": p.last_watched,
                "last_completed": p.last_completed,
            }
            for p in progress_qs
        ]

    def get_watch_statistics(self, obj):
        """Watch statistics from video progress"""
        from django.db.models import Sum

        progress_qs = obj.video_progress.all()
        started_time = progress_qs.filter(is_started=True).aggregate(total=Sum("current_time"))["total"] or 0
        completed_time = progress_qs.aggregate(total=Sum("total_watch_time"))["total"] or 0
        total_watch_time = started_time + completed_time

        return {
            "total_videos_started": progress_qs.filter(is_started=True).count(),
            "total_videos_completed": progress_qs.filter(completion_count__gt=0).count(),
            "total_completions": sum(p.completion_count for p in progress_qs),
            "total_watch_time": round(total_watch_time, 1),
            "unique_videos_watched": progress_qs.filter(is_started=True).count(),
            "completion_rate": round(
                (
                    progress_qs.filter(completion_count__gt=0).count()
                    / max(progress_qs.filter(is_started=True).count(), 1)
                )
                * 100,
                1,
            ),
        }


class CustomUserSerializer(serializers.ModelSerializer):
    profiles = UserProfileSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUserModel
        fields = ["id", "username", "email", "first_name", "last_name", "role", "user_infos", "profiles"]
        read_only_fields = ["id", "role", "profiles", "username"]

    def create(self, validated_data):
        user = CustomUserModel(**validated_data)
        user.save()
        return user

    def update(self, instance, validated_data):
        validated_data.pop("password", None)

        validated_data.pop("username", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CustomUserModel
        fields = ("id", "email", "password", "password2", "first_name", "last_name")
        read_only_fields = ("id",)
        extra_kwargs = {
            "email": {"required": True},
            "password": {"required": True},
            "password2": {"required": True},
        }

    def validate_email(self, value):
        """
        Check if the email is already in use.
        Since username will be the email, this also checks username uniqueness.
        """
        if CustomUserModel.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email address is already in use.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        user = CustomUserModel.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            is_active=False,
        )
        user.set_password(validated_data["password"])
        user.save()

        return user


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["username"] = user.username
        token["email"] = user.email
        token["role"] = user.role

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data["user"] = {
            "id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "role": self.user.role,
            "profiles": UserProfileSerializer(self.user.profiles.all(), many=True).data,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password2 = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except serializers.ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError({"non_field_errors": ["Password fields didn't match."]})

        try:
            uuid.UUID(attrs["token"])
        except ValueError:
            raise serializers.ValidationError({"token": ["Invalid token format."]})
        return attrs
