from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from app_users.utils import send_verification_email, send_password_reset_email

CustomUserModel = get_user_model()


class TestUtils(TestCase):
    @patch("app_users.utils.EmailMultiAlternatives")
    @patch("app_users.utils.render_to_string", return_value="text")
    def test_send_verification_email(self, mock_render, mock_email):
        user = CustomUserModel(username="testuser", email="test@example.com")
        user.email_verification_token = None
        user.save = MagicMock()
        send_verification_email(user, request=None)
        self.assertTrue(user.email_verification_token)
        user.save.assert_called_once()
        mock_email.return_value.send.assert_called_once()

    @patch("app_users.utils.EmailMultiAlternatives")
    @patch("app_users.utils.render_to_string", return_value="text")
    def test_send_password_reset_email(self, mock_render, mock_email):
        user = CustomUserModel(username="testuser", email="test@example.com")
        user.password_reset_token = None
        user.save = MagicMock()
        send_password_reset_email(user, request=None)
        self.assertTrue(user.password_reset_token)
        self.assertTrue(user.password_reset_token_created_at)
        user.save.assert_called_once()
        mock_email.return_value.send.assert_called_once()
