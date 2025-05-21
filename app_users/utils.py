from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
import uuid


def send_verification_email(user, request):
    """
    Sends a verification email to the user.
    """
    if not user.email_verification_token:
        user.email_verification_token = uuid.uuid4()
        user.save(update_fields=["email_verification_token"])

    token = user.email_verification_token
    # TODO - Edit Production Email
    # Use the frontend URL for the verification link
    verification_link = request.build_absolute_uri(reverse("email_verify", kwargs={"token": str(token)}))

    subject = "Verify your email address"
    message = f"Hi {user.username},\n\nPlease click the link below to verify your email address:\n{verification_link}\n\nThanks!"
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    try:
        send_mail(subject, message, email_from, recipient_list)
        print(f"Verification email sent to {user.email}")
        print(f"Verification link: {verification_link}")
    except Exception as e:
        print(f"Error sending verification email: {e}")
        # TODO - Handle error appropriately in production
        pass


def send_password_reset_email(user, request):
    """
    Sends a password reset email to the user.
    """
    if not user.password_reset_token:
        user.password_reset_token = uuid.uuid4()

    user.password_reset_token_created_at = timezone.now()
    user.save(update_fields=["password_reset_token", "password_reset_token_created_at"])

    token = user.password_reset_token
    # TODO - Edit Production Email
    # Use the frontend URL for the password reset link
    frontend_reset_link = f"http://localhost:4200/auth/new-password?token={str(token)}"

    subject = "Password Reset Request"
    message = f"Hi {user.username},\n\nYou requested a password reset. Please click the link below to reset your password:\n{frontend_reset_link}\n\nIf you did not request this, please ignore this email.\n\nThis link will expire in 1 hour.\n\nThanks!"
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    try:
        send_mail(subject, message, email_from, recipient_list)
        print(f"Password reset email sent to {user.email}")
        print(f"Password reset link for email: {frontend_reset_link}")
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        pass
