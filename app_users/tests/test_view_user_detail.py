from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from app_users.models import UserProfiles
from rest_framework_simplejwt.tokens import RefreshToken
import uuid

CustomUserModel = get_user_model()


class UserDetailViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1_username = "detailuser1"
        cls.user1_email = "detail1@example.com"
        cls.user1_password = "StrongPassword123!"
        cls.user1 = CustomUserModel.objects.create_user(
            username=cls.user1_username,
            email=cls.user1_email,
            password=cls.user1_password,
            is_active=True,
            is_email_verified=True,
            first_name="Test",
            last_name="User1",
            role="user",
        )
        UserProfiles.objects.create(user=cls.user1, profile_name="DefaultProfile1")

        cls.user2_username = "detailuser2"
        cls.user2_email = "detail2@example.com"
        cls.user2_password = "AnotherPassword456!"
        cls.user2 = CustomUserModel.objects.create_user(
            username=cls.user2_username,
            email=cls.user2_email,
            password=cls.user2_password,
            is_active=True,
            is_email_verified=True,
            role="admin",
        )

    def setUp(self):
        self.client = APIClient()
        self.user_detail_url = reverse("user_detail")  # Endpoint is /me/

    def _authenticate_user(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")

    def test_get_user_details_authenticated(self):
        self._authenticate_user(self.user1)
        response = self.client.get(self.user_detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user1_username)
        self.assertEqual(response.data["email"], self.user1_email)
        self.assertEqual(response.data["first_name"], "Test")
        self.assertEqual(response.data["last_name"], "User1")
        self.assertEqual(response.data["role"], "user")
        self.assertIn("profiles", response.data)
        self.assertEqual(len(response.data["profiles"]), 1)
        self.assertEqual(response.data["profiles"][0]["profile_name"], "DefaultProfile1")
        self.assertNotIn("password", response.data)  # Ensure password is not serialized

    def test_get_user_details_unauthenticated(self):
        response = self.client.get(self.user_detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_details_authenticated(self):
        self._authenticate_user(self.user1)
        update_data = {
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast",
            "email": "newemail@example.com",  # Assuming email can be updated
            # "username": "newusername" # Assuming username can be updated
            # Note: Updating username and email might have other implications (e.g., uniqueness)
            # The CustomUserSerializer needs to handle these fields correctly for updates.
        }
        response = self.client.patch(self.user_detail_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.first_name, "UpdatedFirst")
        self.assertEqual(self.user1.last_name, "UpdatedLast")
        self.assertEqual(self.user1.email, "newemail@example.com")
        self.assertEqual(response.data["first_name"], "UpdatedFirst")

    def test_update_user_details_partial_update(self):
        self._authenticate_user(self.user1)
        update_data = {"first_name": "PartialUpdateFirst"}
        response = self.client.patch(self.user_detail_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.first_name, "PartialUpdateFirst")
        self.assertEqual(self.user1.last_name, "User1")  # Last name should be unchanged

    def test_update_user_details_unauthenticated(self):
        update_data = {"first_name": "AttemptUpdate"}
        response = self.client.patch(self.user_detail_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_password_not_allowed(self):
        # Password updates should typically go through a dedicated endpoint.
        # The UserDetailView with CustomUserSerializer should not allow direct password update.
        self._authenticate_user(self.user1)
        update_data = {"password": "newpassword123"}
        response = self.client.patch(self.user_detail_url, update_data, format="json")
        # Depending on serializer, this might be ignored or raise an error.
        # If CustomUserSerializer excludes 'password' from writeable fields, it will be ignored.
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.check_password(self.user1_password))  # Password should not change
        self.assertNotIn("password", response.data)  # Password should not be in response

    def test_update_user_role_not_allowed_for_standard_user(self):
        # Role changes are typically admin-only operations or handled by specific logic.
        # Assuming CustomUserSerializer makes 'role' read-only or handles permissions.
        self._authenticate_user(self.user1)  # user1 has 'user' role
        original_role = self.user1.role
        update_data = {"role": "admin"}
        response = self.client.patch(self.user_detail_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Request is OK
        self.user1.refresh_from_db()
        # Check if role actually changed. If serializer makes it read-only, it won't.
        if "role" in response.data:
            self.assertEqual(response.data["role"], original_role)  # Should not change if read-only
        self.assertEqual(self.user1.role, original_role)

    # Add more tests for validation if CustomUserSerializer has specific update validations
    # e.g., trying to set an invalid email format during update.
    def test_update_user_details_invalid_email(self):
        self._authenticate_user(self.user1)
        update_data = {
            "email": "not-an-email",
        }
        response = self.client.patch(self.user_detail_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(response.data["email"][0].code, "invalid")
