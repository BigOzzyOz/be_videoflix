from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUserModel, UserProfile


class UserProfileInline(admin.TabularInline):
    model = UserProfile
    extra = 0
    max_num = 4
    can_delete = True
    show_change_link = True


@admin.register(CustomUserModel)
class CustomUserAdmin(UserAdmin):
    model = CustomUserModel
    list_display = ("username", "email", "role", "created_at", "last_login", "display_profiles")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("-created_at",)
    inlines = [UserProfileInline]

    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "role", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
        ("Additional Info", {"fields": ("user_infos",)}),
    )
    readonly_fields = ("created_at", "updated_at", "date_joined")

    def display_profiles(self, obj):
        profiles = obj.profiles.all()[:4]
        return ", ".join(p.profile_name or "Unnamed" for p in profiles)

    display_profiles.short_description = "Profiles"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("profile_name", "user", "is_kid", "preferred_language")
    list_filter = ("is_kid", "preferred_language")
    search_fields = ("profile_name", "user__username", "user__email")
    ordering = ("user__created_at",)
