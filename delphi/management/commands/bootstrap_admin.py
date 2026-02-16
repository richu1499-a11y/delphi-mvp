import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a default superuser from env vars if none exists (idempotent)."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not (username and email and password):
            self.stdout.write(self.style.WARNING(
                "bootstrap_admin: env vars not fully set; skipping."
            ))
            return

        User = get_user_model()

        # If any superuser already exists, do nothing
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS(
                "bootstrap_admin: superuser already exists; nothing to do."
            ))
            return

        # If a user with the same username exists but isn't superuser, fail loudly
        if User.objects.filter(username=username).exists():
            raise Exception(
                f"bootstrap_admin: user '{username}' exists but is not a superuser. "
                f"Delete/rename that user or change DJANGO_SUPERUSER_USERNAME."
            )

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(
            f"bootstrap_admin: created superuser '{username}'."
        ))
