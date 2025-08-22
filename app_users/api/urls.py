from django.urls import path
from app_users.api.views import (
    MyTokenObtainPairView,
    RegisterView,
    EmailVerifyView,
    UserDetailView,
    UserProfileListCreateView,
    UserProfileDetailView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    VideoProgressUpdateView,
)

urlpatterns = [
    path("login/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-email/<str:token>/", EmailVerifyView.as_view(), name="email_verify"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password_reset_request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("me/", UserDetailView.as_view(), name="user_detail"),
    path("me/profiles/", UserProfileListCreateView.as_view(), name="user_profile_list_create"),
    path("me/profiles/<uuid:profile_id>/", UserProfileDetailView.as_view(), name="user_profile_detail"),
    path(
        "me/profiles/<uuid:profile_id>/progress/<uuid:video_file_id>/update/",
        VideoProgressUpdateView.as_view(),
        name="update_video_progress",
    ),
]
