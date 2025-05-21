import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUserModel(AbstractUser):
    """
    Custom user model that extends the AbstractUser class.
    """

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("staff", "Staff"),
        ("user", "User"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="User ID")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated")
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="Last login")
    role = models.CharField(choices=ROLE_CHOICES, max_length=50, default="user", verbose_name="Role")
    user_infos = models.TextField(blank=True, null=True, verbose_name="User info notes")
    is_email_verified = models.BooleanField(default=False, verbose_name="Email verified")
    email_verification_token = models.UUIDField(null=True, blank=True, editable=False, default=None)
    password_reset_token = models.UUIDField(null=True, blank=True, editable=False, default=None)
    password_reset_token_created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.username


class UserProfiles(models.Model):
    """
    User profiles model that extends the CustomUserModel.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, verbose_name="Profile ID")
    user = models.ForeignKey(CustomUserModel, on_delete=models.CASCADE, related_name="profiles", verbose_name="User")
    profile_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Profile name")
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True, verbose_name="Profile picture"
    )
    is_kid = models.BooleanField(default=False, verbose_name="Child profile")
    preferred_language = models.CharField(max_length=10, default="de", verbose_name="Preferred language")

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ["-user__created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.profile_name}"
