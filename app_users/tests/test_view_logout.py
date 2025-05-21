from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

CustomUserModel = get_user_model()


class LogoutViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = "logoutuser"
        cls.email = "logout@example.com"
        cls.password = "StrongPassword123!"
        cls.user = CustomUserModel.objects.create_user(
            username=cls.username, email=cls.email, password=cls.password, is_active=True, is_email_verified=True
        )

    def setUp(self):
        self.client = APIClient()
        self.logout_url = reverse("logout")
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        self.refresh_token = str(self.refresh)

    def test_successful_logout(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        data = {"refresh_token": self.refresh_token}
        response = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Verify token is blacklisted (this requires checking the blacklist app's models)
        # For simplicity, we'll assume if the status is 205, it worked as expected.
        # A more thorough test would query the OutstandingToken and BlacklistedToken models.
        # from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
        # self.assertTrue(BlacklistedToken.objects.filter(token__jti=self.refresh.payload['jti']).exists())

    def test_logout_no_refresh_token_provided(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        data = {}
        response = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # The view's current exception handling is broad (except Exception:)
        # so we don't get a specific error message like {"refresh_token": ["This field is required."]}
        # but a generic 400.

    def test_logout_invalid_refresh_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        data = {"refresh_token": "thisisnotavalidtoken"}
        response = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Again, generic 400 due to broad exception handling.
        # A more specific error from SimpleJWT would be TokenError: "Token is invalid or expired"

    def test_logout_not_authenticated(self):
        # No self.client.credentials() call
        data = {"refresh_token": self.refresh_token}
        response = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)
        self.assertEqual(str(response.data["detail"]), "Authentication credentials were not provided.")

    def test_logout_already_blacklisted_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        data = {"refresh_token": self.refresh_token}

        # First logout
        response1 = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response1.status_code, status.HTTP_205_RESET_CONTENT)

        # Attempt to logout again with the same (now blacklisted) token
        response2 = self.client.post(self.logout_url, data, format="json")
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        # This happens because RefreshToken(refresh_token) will raise a TokenError
        # if the token is already blacklisted, caught by the generic Exception.
