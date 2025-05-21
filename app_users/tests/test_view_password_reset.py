from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
import uuid
from django.utils import timezone
from datetime import timedelta
from django.conf import settings  # Import Django settings

from app_users.api.views import PasswordResetConfirmView  # Import the view for testing

CustomUserModel = get_user_model()


class PasswordResetRequestViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.active_user_email = "resetrequest@example.com"
        cls.active_user = CustomUserModel.objects.create_user(
            username="resetuser",
            email=cls.active_user_email,
            password="password123",
            is_active=True,
            is_email_verified=True,
        )
        cls.inactive_user_email = "inactive_reset@example.com"
        CustomUserModel.objects.create_user(
            username="inactiveresetuser",
            email=cls.inactive_user_email,
            password="password123",
            is_active=False,  # Important: user is inactive
        )

    def setUp(self):
        self.url = reverse("password_reset_request")

    @patch("app_users.api.views.send_password_reset_email")
    def test_successful_password_reset_request_active_user(self, mock_send_email):
        data = {"email": self.active_user_email}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "If an account with this email exists, a password reset link has been sent."
        )

        self.active_user.refresh_from_db()
        self.assertIsNotNone(self.active_user.password_reset_token)
        self.assertIsNotNone(self.active_user.password_reset_token_created_at)

        mock_send_email.assert_called_once()
        called_args, _ = mock_send_email.call_args
        self.assertEqual(called_args[0], self.active_user)
        self.assertIsNotNone(called_args[1])  # Request object

    @patch("app_users.api.views.send_password_reset_email")
    def test_password_reset_request_non_existent_email(self, mock_send_email):
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Generic message
        self.assertEqual(
            response.data["message"], "If an account with this email exists, a password reset link has been sent."
        )
        mock_send_email.assert_not_called()

    @patch("app_users.api.views.send_password_reset_email")
    def test_password_reset_request_inactive_user(self, mock_send_email):
        data = {"email": self.inactive_user_email}

        # Ensure the user is indeed inactive before the request
        user_before_request = CustomUserModel.objects.get(email=self.inactive_user_email)
        self.assertFalse(user_before_request.is_active)
        self.assertIsNone(user_before_request.password_reset_token)  # Should be None initially

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "If an account with this email exists, a password reset link has been sent."
        )

        inactive_user_db = CustomUserModel.objects.get(email=self.inactive_user_email)
        self.assertFalse(inactive_user_db.is_active)  # Re-check is_active, should not have changed
        self.assertIsNone(inactive_user_db.password_reset_token)  # Token should not be set
        mock_send_email.assert_not_called()

    def test_password_reset_request_missing_email_field(self):
        data = {}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(response.data["email"][0].code, "required")

    def test_password_reset_request_invalid_email_format(self):
        data = {"email": "notanemail"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(response.data["email"][0].code, "invalid")


class PasswordResetConfirmViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_email = "confirmreset@example.com"
        cls.password = "oldPassword123!"
        cls.reset_token = uuid.uuid4()
        cls.user = CustomUserModel.objects.create_user(
            username="confirmresetuser",
            email=cls.user_email,
            password=cls.password,
            is_active=True,
            is_email_verified=True,
            password_reset_token=cls.reset_token,
            password_reset_token_created_at=timezone.now(),
        )

    def setUp(self):
        self.url_name_generic = "password_reset_confirm"  # Assuming a generic URL name for the view
        self.new_password = "newStrongPassword456!"

    def test_successful_password_reset_confirm(self):
        url = reverse(self.url_name_generic)  # Use generic URL, token is in body
        data = {
            "token": str(self.reset_token),
            "new_password": self.new_password,
            "new_password2": self.new_password,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Password has been reset successfully.")

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(self.new_password))
        self.assertFalse(self.user.check_password(self.password))  # Old password should not work
        self.assertIsNone(self.user.password_reset_token)
        self.assertIsNone(self.user.password_reset_token_created_at)

    def test_password_reset_confirm_invalid_token_in_url(self):
        # This test is tricky if the URL token is not used by the POST logic.
        # If PasswordResetConfirmView.post uses token from body, URL token is irrelevant for it.
        # Assuming the intention is to test that an invalid *body* token fails.
        invalid_token = uuid.uuid4()
        url = reverse(self.url_name_generic)  # Use generic URL
        data = {
            "token": str(invalid_token),  # Invalid token in body
            "new_password": self.new_password,
            "new_password2": self.new_password,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid or expired password reset token.")

    def test_password_reset_confirm_invalid_token_in_body(self):
        url = reverse(self.url_name_generic)  # Use generic URL
        invalid_token_body = uuid.uuid4()
        data = {
            "token": str(invalid_token_body),
            "new_password": self.new_password,
            "new_password2": self.new_password,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid or expired password reset token.")

    def test_password_reset_confirm_token_expired(self):
        # Make token expired based on settings
        self.user.password_reset_token_created_at = timezone.now() - timedelta(
            hours=settings.PASSWORD_RESET_TIMEOUT_HOURS + 1
        )
        self.user.save()

        url = reverse(self.url_name_generic)  # Use generic URL
        data = {
            "token": str(self.reset_token),
            "new_password": self.new_password,
            "new_password2": self.new_password,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Password reset token has expired.")

    def test_password_reset_confirm_password_mismatch(self):
        url = reverse(self.url_name_generic)  # Use generic URL
        data = {
            "token": str(self.reset_token),
            "new_password": self.new_password,
            "new_password2": "ADifferentPassword!",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)
        # The specific message comes from the serializer
        self.assertEqual(str(response.data["non_field_errors"][0]), "Password fields didn't match.")

    def test_password_reset_confirm_missing_fields(self):
        url = reverse(self.url_name_generic)  # Use generic URL
        # Missing new_password
        data_missing_pass = {"token": str(self.reset_token), "new_password2": self.new_password}
        response = self.client.post(url, data_missing_pass, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password", response.data)

        # Missing new_password2
        data_missing_confirm = {"token": str(self.reset_token), "new_password": self.new_password}
        response = self.client.post(url, data_missing_confirm, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("new_password2", response.data)  # Changed from confirm_new_password

        # Missing token
        data_missing_token = {"new_password": self.new_password, "new_password2": self.new_password}
        response = self.client.post(url, data_missing_token, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response.data)
