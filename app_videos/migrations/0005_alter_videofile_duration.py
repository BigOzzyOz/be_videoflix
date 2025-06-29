from django.db import migrations, models
from datetime import timedelta


def convert_duration_to_float(apps, schema_editor):
    VideoFile = apps.get_model("app_videos", "VideoFile")

    for video_file in VideoFile.objects.all():
        if video_file.duration:
            # Konvertiere timedelta zu Sekunden (Float)
            if isinstance(video_file.duration, timedelta):
                total_seconds = video_file.duration.total_seconds()
                video_file.duration_temp = total_seconds
            else:
                video_file.duration_temp = float(video_file.duration)
            video_file.save()


def reverse_convert_duration(apps, schema_editor):
    # Reverse operation falls nötig
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("app_videos", "0004_genre_remove_video_genre_video_genre"),
    ]

    operations = [
        migrations.AddField(
            model_name="videofile",
            name="duration_temp",
            field=models.FloatField(default=0.0),
        ),
        migrations.RunPython(convert_duration_to_float, reverse_convert_duration),
        migrations.RemoveField(
            model_name="videofile",
            name="duration",
        ),
        migrations.RenameField(
            model_name="videofile",
            old_name="duration_temp",
            new_name="duration",
        ),
    ]
