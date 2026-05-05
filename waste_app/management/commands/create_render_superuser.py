import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the default Render superuser if it does not exist."

    def handle(self, *args, **options):
        if not os.environ.get("RENDER"):
            self.stdout.write("Skipping superuser creation outside Render.")
            return

        User = get_user_model()
        username = "admin"

        if User.objects.filter(username=username).exists():
            self.stdout.write("Render superuser already exists.")
            return

        User.objects.create_superuser(
            username=username,
            email="admin@example.com",
            password="admin123",
        )
        self.stdout.write(self.style.SUCCESS("Created Render superuser."))
