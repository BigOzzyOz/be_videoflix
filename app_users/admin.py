from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUserModel, UserProfiles
from app_videos.models import VideoProgress


class VideoProgressInline(admin.TabularInline):
    """Inline for VideoProgress in admin."""

    model = VideoProgress
    extra = 0
    readonly_fields = ("progress_percentage", "is_completed", "is_started", "last_watched")
    fields = ("video_file", "current_time", "progress_percentage", "is_completed", "is_started")
    raw_id_fields = ("video_file",)


class UserProfileInline(admin.TabularInline):
    """Inline for UserProfiles in admin."""

    model = UserProfiles
    extra = 0
    max_num = 4
    can_delete = True
    show_change_link = True


@admin.register(CustomUserModel)
class CustomUserAdmin(UserAdmin):
    """Admin for CustomUserModel with profile overview."""

    model = CustomUserModel
    list_display = ("username", "email", "role", "created_at", "last_login", "display_profiles", "profile_count")
    list_filter = ("role", "is_staff", "is_active", "created_at")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-created_at",)
    inlines = [UserProfileInline]

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "role", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
        ("Additional Info", {"fields": ("user_infos",)}),
        ("Email Verification", {"fields": ("is_email_verified", "email_verification_token")}),
    )
    readonly_fields = ("created_at", "updated_at", "date_joined", "email_verification_token")

    def display_profiles(self, obj):
        """Shows up to 4 profiles as a string."""
        profiles = obj.profiles.all()[:4]
        profile_list = []
        for p in profiles:
            name = p.profile_name or "Unnamed"
            if p.is_kid:
                name += " 👶"
            profile_list.append(name)
        return ", ".join(profile_list)

    def profile_count(self, obj):
        """Returns the number of profiles."""
        count = obj.profiles.count()
        return f"{count}/4"

    display_profiles.short_description = "Profiles"
    profile_count.short_description = "Profile Count"


@admin.register(UserProfiles)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfiles with video progress and watch time."""

    list_display = (
        "profile_name",
        "user",
        "is_kid",
        "preferred_language",
        "video_progress_count",
        "watch_time_display",
    )
    list_filter = ("is_kid", "preferred_language")
    search_fields = ("profile_name", "user__username", "user__email")
    ordering = ("profile_name",)
    inlines = [VideoProgressInline]

    fieldsets = (("Profile Info", {"fields": ("user", "profile_name", "is_kid", "preferred_language")}),)

    def video_progress_count(self, obj):
        """Number of videos with progress."""
        started = obj.video_progress.filter(is_started=True).count()
        completed = obj.video_progress.filter(is_completed=True).count()
        return f"{started} started / {completed} completed"

    def watch_time_display(self, obj):
        """Total watch time in hours and minutes."""
        total_seconds = sum(p.current_time for p in obj.video_progress.all())
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    video_progress_count.short_description = "Video Progress"
    watch_time_display.short_description = "Watch Time"
