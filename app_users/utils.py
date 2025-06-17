from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import uuid

BASE_URL = "http://localhost:8000"



def send_verification_email(user, request):
    """
    Sends a verification email to the user.
    """
    if not user.email_verification_token:
        user.email_verification_token = uuid.uuid4()
        user.save(update_fields=["email_verification_token"])

    token = user.email_verification_token
    frontend_reset_link = f"{BASE_URL}/verify?token={str(token)}"

    context = {
        "username": user.username,
        "verification_link": frontend_reset_link,
    }

    subject = "Confirm your email"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_email = [user.email]

    text_content = render_to_string("emails/verify_email.txt", context)
    html_content = render_to_string("emails/verify_email.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=recipient_email,
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_password_reset_email(user, request):
    """
    Sends a password reset email to the user.
    """
    if not user.password_reset_token:
        user.password_reset_token = uuid.uuid4()

    user.password_reset_token_created_at = timezone.now()
    user.save(update_fields=["password_reset_token", "password_reset_token_created_at"])

    token = user.password_reset_token
    frontend_reset_link = f"{BASE_URL}/password/reset?reset=true&token={str(token)}"

    context = {
        "url": frontend_reset_link,
    }

    subject = "Reset your Password"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_email = [user.email]

    text_content = render_to_string("emails/password_reset.txt", context)
    html_content = render_to_string("emails/password_reset.html", context)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=recipient_email,
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
