# Generated by Django 5.2.1 on 2025-06-09 03:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_videos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='videofile',
            name='duration',
            field=models.DurationField(blank=True, help_text='Videolänge', null=True),
        ),
        migrations.AddField(
            model_name='videofile',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to='thumbnails/'),
        ),
    ]
