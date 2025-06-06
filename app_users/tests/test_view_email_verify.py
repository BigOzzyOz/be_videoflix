import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from app_users.models import UserProfiles

CustomUserModel = get_user_model()


class EmailVerifyViewTests(APITestCase):
    def setUp(self):
        self.username = "verifyuser"
        self.email = "verify@example.com"
        self.password = "StrongPassword123!"
        self.verification_token = uuid.uuid4()
        self.user = CustomUserModel.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password,
            is_active=False,
            is_email_verified=False,
            email_verification_token=self.verification_token,
        )
        self.verify_url_name = "email_verify"

    def test_successful_email_verification(self):
        url = reverse(self.verify_url_name, kwargs={"token": str(self.verification_token)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Email successfully verified. You can now login.")

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)
        self.assertIsNone(self.user.email_verification_token)

        self.assertTrue(self.user.profiles.exists())
        profile = self.user.profiles.first()
        self.assertEqual(profile.profile_name, self.user.username)

    def test_email_verification_invalid_token_format(self):
        url = reverse(self.verify_url_name, kwargs={"token": "not-a-uuid"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid or expired verification token.")

    def test_email_verification_nonexistent_token(self):
        non_existent_token = uuid.uuid4()
        url = reverse(self.verify_url_name, kwargs={"token": str(non_existent_token)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid or expired verification token.")

    def test_email_verification_user_already_active(self):
        self.user.is_active = True
        self.user.save()
        url = reverse(self.verify_url_name, kwargs={"token": str(self.verification_token)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid or expired verification token.")

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_email_verified)
        self.assertEqual(self.user.email_verification_token, self.verification_token)

    def test_email_verification_token_already_used_or_cleared(self):
        url_success = reverse(self.verify_url_name, kwargs={"token": str(self.verification_token)})
        self.client.get(url_success)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)
        self.assertIsNone(self.user.email_verification_token)

        response_again = self.client.get(url_success)
        self.assertEqual(response_again.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_again.data["detail"], "Invalid or expired verification token.")

    def test_email_verification_profile_already_exists(self):
        UserProfiles.objects.create(user=self.user, profile_name="existing_profile")

        url = reverse(self.verify_url_name, kwargs={"token": str(self.verification_token)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.is_email_verified)
        self.assertIsNone(self.user.email_verification_token)

        self.assertEqual(self.user.profiles.count(), 1)
        self.assertEqual(self.user.profiles.first().profile_name, "existing_profile")
