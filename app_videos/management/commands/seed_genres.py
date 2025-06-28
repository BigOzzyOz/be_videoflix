from django.core.management.base import BaseCommand
from app_videos.models import Genre


class Command(BaseCommand):
    help = "Seed standard movie genres"

    GENRES = [
        "Action",
        "Adventure",
        "Animation",
        "Comedy",
        "Crime",
        "Documentary",
        "Drama",
        "Family",
        "Fantasy",
        "History",
        "Horror",
        "Music",
        "Mystery",
        "Romance",
        "Science Fiction",
        "Thriller",
        "War",
        "Western",
    ]

    def handle(self, *args, **kwargs):
        created = 0
        for genre_name in self.GENRES:
            obj, was_created = Genre.objects.get_or_create(name=genre_name)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"{created} genres created."))
