from django.test import TestCase, RequestFactory
from app_users.api.serializers import (
    CustomUserSerializer,
    UserProfileSerializer,
    RegisterSerializer,
    PasswordResetConfirmSerializer,
)
from app_users.models import UserProfiles, CustomUserModel
import uuid


class TestUserProfileSerializer(TestCase):
    def setUp(self):
        self.user = CustomUserModel.objects.create(username="testuser", email="test@example.com")
        self.profile = UserProfiles.objects.create(profile_name="Test", user=self.user)
        self.factory = RequestFactory()

    def test_get_profile_picture_url_with_request(self):
        self.profile.profile_picture = type("FakeImage", (), {"url": "/media/test.jpg"})()
        request = self.factory.get("/api/")
        serializer = UserProfileSerializer(context={"request": request})
        url = serializer.get_profile_picture_url(self.profile)
        self.assertTrue(url.startswith("http"))

    def test_get_profile_picture_url_without_request(self):
        self.profile.profile_picture = type("FakeImage", (), {"url": "/media/test.jpg"})()
        serializer = UserProfileSerializer()
        url = serializer.get_profile_picture_url(self.profile)
        self.assertEqual(url, "/media/test.jpg")

    def test_get_profile_picture_url_none(self):
        serializer = UserProfileSerializer()
        url = serializer.get_profile_picture_url(self.profile)
        self.assertIsNone(url)

    def test_get_video_progress_not_userprofiles(self):
        serializer = UserProfileSerializer()
        result = serializer.get_video_progress(object())
        self.assertEqual(result, [])

    def test_get_watch_statistics_not_userprofiles(self):
        serializer = UserProfileSerializer()
        result = serializer.get_watch_statistics(object())
        self.assertEqual(result, [])


class TestRegisterSerializer(TestCase):
    def test_validate_email_new(self):
        serializer = RegisterSerializer()
        email = "unique@example.com"
        result = serializer.validate_email(email)
        self.assertEqual(result, email)


class TestPasswordResetConfirmSerializer(TestCase):
    def test_validate_token_format(self):
        serializer = PasswordResetConfirmSerializer()
        valid_token = str(uuid.uuid4())
        data = {"token": valid_token, "new_password": "Test1234!", "new_password2": "Test1234!"}
        result = serializer.validate(data)
        self.assertEqual(result["token"], valid_token)

    def test_password_reset_confirm_serializer_invalid_token(self):
        data = {
            "token": "not-a-uuid",
            "new_password": "TestPassword123!",
            "new_password2": "TestPassword123!",
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert "token" in serializer.errors
        assert serializer.errors["token"] == ["Invalid token format."]

    def test_password_reset_confirm_serializer_invalid_new_password(self):
        data = {
            "token": "123e4567-e89b-12d3-a456-426614174000",  # gültiger UUID
            "new_password": "123",  # absichtlich ungültig
            "new_password2": "123",
        }
        serializer = PasswordResetConfirmSerializer(data=data)
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors
        assert isinstance(serializer.errors["new_password"], list)
        assert any("too short" in msg.lower() or "password" in msg.lower() for msg in serializer.errors["new_password"])


class TestCustomUserSerializer(TestCase):
    def test_custom_user_serializer_create(self):
        data = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "user_infos": "",
        }
        serializer = CustomUserSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        user = serializer.save()
        assert user.email == "newuser@example.com"
