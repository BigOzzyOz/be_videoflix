from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import uuid


def send_verification_email(user, request):
    """
    Sends a verification email to the user.
    """
    # Ensure the user has a verification token
    if not user.email_verification_token:
        user.email_verification_token = uuid.uuid4()
        user.save(update_fields=["email_verification_token"])

    token = user.email_verification_token
    # Construct the verification URL
    # Make sure to replace 'your_frontend_url' with the actual URL
    # where your frontend handles email verification.
    # For now, we'll use the backend URL and assume the frontend will proxy or redirect.
    verification_link = request.build_absolute_uri(reverse("email_verify", kwargs={"token": str(token)}))

    subject = "Verify your email address"
    message = f"Hi {user.username},\n\nPlease click the link below to verify your email address:\n{verification_link}\n\nThanks!"
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    try:
        send_mail(subject, message, email_from, recipient_list)
        print(f"Verification email sent to {user.email}")
        print(f"Verification link: {verification_link}")  # For debugging with console backend
    except Exception as e:
        print(f"Error sending verification email: {e}")
        # In a production environment, you might want to log this error
        # or add more robust error handling.
        pass  # Or raise an error to be caught by the caller


def send_password_reset_email(user, request):
    """
    Sends a password reset email to the user.
    """
    # Ensure the user has a password reset token
    if not user.password_reset_token:
        user.password_reset_token = uuid.uuid4()
    # Update the token creation time
    from django.utils import timezone

    user.password_reset_token_created_at = timezone.now()
    user.save(update_fields=["password_reset_token", "password_reset_token_created_at"])

    token = user.password_reset_token

    # Placeholder for the frontend URL that handles the password reset form
    # In a real app, this would come from settings or be a known frontend route
    # The frontend URL should include the token, e.g., http://localhost:4200/auth/new-password?token=<token_value>
    # For the email, we provide a link that the user clicks.
    # The reverse lookup for a backend confirm view is not directly used in the email link to the user,
    # but the frontend will ultimately POST to a backend confirmation URL.

    # Example frontend link (adjust to your actual frontend routing)
    frontend_reset_link = f"http://localhost:4200/auth/new-password?token={str(token)}"

    subject = "Password Reset Request"
    message = f"Hi {user.username},\n\nYou requested a password reset. Please click the link below to reset your password:\n{frontend_reset_link}\n\nIf you did not request this, please ignore this email.\n\nThis link will expire in 1 hour.\n\nThanks!"
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    try:
        send_mail(subject, message, email_from, recipient_list)
        print(f"Password reset email sent to {user.email}")
        print(f"Password reset link for email: {frontend_reset_link}")  # For debugging
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        pass
