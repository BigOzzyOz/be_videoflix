from django.apps import AppConfig


class AppVideosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app_videos"

    def ready(self):
        import app_videos.signals
