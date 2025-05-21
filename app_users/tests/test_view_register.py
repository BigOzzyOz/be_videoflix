from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
import uuid  # Added import

CustomUserModel = get_user_model()


class RegisterViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_user_email_for_taken_test = "existing@example.com"

        CustomUserModel.objects.create_user(
            username=cls.existing_user_email_for_taken_test,  # Username is now email
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

        # Define a side effect for the mock
        # This function will run when app_users.api.views.send_verification_email is called
        def mock_send_email_side_effect(user_obj_passed_to_mock, request_obj_passed_to_mock):
            # Simulate the token generation and saving part of the real function
            if not user_obj_passed_to_mock.email_verification_token:
                user_obj_passed_to_mock.email_verification_token = uuid.uuid4()
                user_obj_passed_to_mock.save(update_fields=["email_verification_token"])
            # The mock doesn't actually send an email or return anything specific

        mock_send_email.side_effect = mock_send_email_side_effect

        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify the user in the database
        self.assertTrue(CustomUserModel.objects.filter(email=email_for_success).exists())
        registered_user = CustomUserModel.objects.get(email=email_for_success)  # Fresh from DB

        self.assertEqual(registered_user.username, email_for_success)  # Check username is set to email
        self.assertFalse(registered_user.is_active)
        self.assertFalse(registered_user.is_email_verified)
        self.assertIsNotNone(registered_user.email_verification_token)  # This should now pass

        # Verify that the mock was called correctly
        mock_send_email.assert_called_once()
        # The first argument to mock_send_email (call_args[0][0]) should be the user instance
        # that was created and saved by serializer.save() and then passed to send_verification_email
        user_arg_in_mock_call = mock_send_email.call_args[0][0]
        request_arg_in_mock_call = mock_send_email.call_args[0][1]

        self.assertEqual(user_arg_in_mock_call.id, registered_user.id)  # Compare by ID
        self.assertEqual(user_arg_in_mock_call.email, email_for_success)
        self.assertIsNotNone(request_arg_in_mock_call)  # Check that a request object was passed

    def test_registration_email_taken(self):
        data = {
            "email": self.existing_user_email_for_taken_test,  # Use pre-existing email
            "password": "StrongPassword123!",
            "password2": "StrongPassword123!",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        # The message comes from RegisterSerializer.validate_email
        self.assertEqual(str(response.data["email"][0]), "This email address is already in use.")

    def test_registration_password_mismatch(self):
        data = {"email": "mismatch@example.com", "password": "StrongPassword123!", "password2": "DifferentPassword123!"}
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(
            str(response.data["password"][0]), "Password fields didn't match."
        )  # Adjusted to match serializer error

    def test_registration_missing_fields(self):
        # Test missing email
        data_missing_email = {"password": "StrongPassword123!", "password2": "StrongPassword123!"}
        response = self.client.post(self.register_url, data_missing_email, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(response.data["email"][0].code, "required")

        # Test missing password
        data_missing_password = {
            "email": "nopass@example.com",
            "password2": "StrongPassword123!",
        }
        response = self.client.post(self.register_url, data_missing_password, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(response.data["password"][0].code, "required")

        # Test missing password2
        data_missing_password2 = {
            "email": "nopass2@example.com",
            "password": "StrongPassword123!",
        }
        response = self.client.post(self.register_url, data_missing_password2, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password2", response.data)
        self.assertEqual(response.data["password2"][0].code, "required")
