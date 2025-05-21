from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from app_users.models import UserProfiles
import uuid

CustomUserModel = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfiles
        fields = ["id", "profile_name", "profile_picture", "is_kid", "preferred_language"]
        read_only_fields = ["id"]
        extra_kwargs = {"profile_name": {"required": True, "allow_blank": False}}


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
        validated_data.pop("password", None)  # Remove password if present, but don't use it

        # Prevent username changes after creation, as it's set to email
        validated_data.pop("username", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)  # Ensure email is explicitly required
    first_name = serializers.CharField(required=False, allow_blank=True)  # Optional
    last_name = serializers.CharField(required=False, allow_blank=True)  # Optional

    class Meta:
        model = CustomUserModel
        fields = ("id", "email", "password", "password2", "first_name", "last_name")
        read_only_fields = ("id",)
        extra_kwargs = {  # Ensure all required fields are explicitly marked if not by default
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
            # This implicitly also means a user with this username (email) exists.
            raise serializers.ValidationError("This email address is already in use.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        # Set username to the email
        user = CustomUserModel.objects.create_user(
            username=validated_data["email"],  # Set username as email
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
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
        }
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)  # Ensure email is required


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password2 = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except serializers.ValidationError as e:  # Catch Django's ValidationError
            raise serializers.ValidationError(list(e.messages))  # Convert to DRF's ValidationError
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError({"non_field_errors": ["Password fields didn't match."]})

        # Validate token format as UUID here
        try:
            uuid.UUID(attrs["token"])
        except ValueError:
            raise serializers.ValidationError({"token": ["Invalid token format."]})
        return attrs
