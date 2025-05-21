from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
import uuid

CustomUserModel = get_user_model()


class RegisterViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_user_email_for_taken_test = "existing@example.com"

        CustomUserModel.objects.create_user(
            username=cls.existing_user_email_for_taken_test,
            email=cls.existing_user_email_for_taken_test,
            password="password123",
            is_active=True,
        )

    def setUp(self):
        self.register_url = reverse("register")

    @patch("app_users.api.views.send_verification_email")
    def test_successful_registration(self, mock_send_email):
        email_for_success = "success@example.com"
        data = {
            "email": email_for_success,
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
            "first_name": "Test",
            "last_name": "User",
        }

        def mock_send_email_side_effect(user_obj_passed_to_mock, request_obj_passed_to_mock):
            if not user_obj_passed_to_mock.email_verification_token:
                user_obj_passed_to_mock.email_verification_token = uuid.uuid4()
                user_obj_passed_to_mock.save(update_fields=["email_verification_token"])

        mock_send_email.side_effect = mock_send_email_side_effect

        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(CustomUserModel.objects.filter(email=email_for_success).exists())
        registered_user = CustomUserModel.objects.get(email=email_for_success)

        self.assertEqual(registered_user.username, email_for_success)
        self.assertFalse(registered_user.is_active)
        self.assertFalse(registered_user.is_email_verified)
        self.assertIsNotNone(registered_user.email_verification_token)

        mock_send_email.assert_called_once()
        user_arg_in_mock_call = mock_send_email.call_args[0][0]
        request_arg_in_mock_call = mock_send_email.call_args[0][1]

        self.assertEqual(user_arg_in_mock_call.id, registered_user.id)
        self.assertEqual(user_arg_in_mock_call.email, email_for_success)
        self.assertIsNotNone(request_arg_in_mock_call)

    def test_registration_email_taken(self):
        data = {
            "email": self.existing_user_email_for_taken_test,
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(str(response.data["email"][0]), "This email address is already in use.")

    def test_registration_password_mismatch(self):
        data = {"email": "mismatch@example.com", "password": "StrongPassword123!", "password2": "DifferentPassword123!"}
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(str(response.data["password"][0]), "Password fields didn't match.")

    def test_registration_missing_fields(self):
        data_missing_email = {"password": "StrongPassword123!", "password2": "StrongPassword123!"}
        response = self.client.post(self.register_url, data_missing_email, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(response.data["email"][0].code, "required")

        data_missing_password = {
            "email": "nopass@example.com",
            "password2": "StrongPassword123!",
        }
        response = self.client.post(self.register_url, data_missing_password, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(response.data["password"][0].code, "required")

        data_missing_password2 = {
            "email": "nopass2@example.com",
            "password": "StrongPassword123!",
        }
        response = self.client.post(self.register_url, data_missing_password2, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password2", response.data)
        self.assertEqual(response.data["password2"][0].code, "required")
