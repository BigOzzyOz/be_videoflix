from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

CustomUserModel = get_user_model()


class LoginViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.username = "loginuser"
        cls.email = "login@example.com"
        cls.password = "StrongPassword123!"
        cls.user = CustomUserModel.objects.create_user(
            username=cls.username,
            email=cls.email,
            password=cls.password,
            is_active=True,
            is_email_verified=True,
        )

    def setUp(self):
        self.login_url = reverse("token_obtain_pair")

    def test_successful_login(self):
        data = {"username": self.username, "password": self.password}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], self.username)
        self.assertEqual(response.data["user"]["email"], self.email)
        self.assertIn("role", response.data["user"])

    def test_login_inactive_user(self):
        CustomUserModel.objects.create_user(
            username="inactiveuser", email="inactive@example.com", password="password123", is_active=False
        )
        data = {"username": "inactiveuser", "password": "password123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_login_wrong_password(self):
        data = {"username": self.username, "password": "WrongPassword!"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_login_wrong_username(self):
        data = {"username": "nonexistentuser", "password": self.password}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_login_missing_password(self):
        data = {"username": self.username}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("password", response.data)
        self.assertEqual(response.data["password"][0].code, "required")

    def test_login_missing_username(self):
        data = {"password": self.password}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("username", response.data)
        self.assertEqual(response.data["username"][0].code, "required")
