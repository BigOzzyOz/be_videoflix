from django.apps import AppConfig


class AppVideosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_videos"
    verbose_name = "Video Management"

    def ready(self):
        import app_videos.signals
