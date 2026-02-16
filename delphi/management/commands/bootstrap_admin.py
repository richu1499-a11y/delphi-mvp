import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create (or promote) a superuser from env vars (idempotent)."

    def handle(self, *args, **options):
        User = get_user_model()

        username = (
            os.environ.get("DJANGO_SUPERUSER_USERNAME")
            or os.environ.get("ADMIN_USERNAME")
            or "admin"
        )
        email = (
            os.environ.get("DJANGO_SUPERUSER_EMAIL")
            or os.environ.get("ADMIN_EMAIL")
            or ""
        )
        password = (
            os.environ.get("DJANGO_SUPERUSER_PASSWORD")
            or os.environ.get("ADMIN_PASSWORD")
        )

        if not password:
            self.stdout.write(self.style.WARNING(
                "bootstrap_admin: no password env var set (DJANGO_SUPERUSER_PASSWORD or ADMIN_PASSWORD). Skipping."
            ))
            return

        user = User.objects.filter(username=username).first()

        if user:
            # Promote existing user if needed
            changed = False
            if not user.is_staff:
                user.is_staff = True
                changed = True
            if not user.is_superuser:
                user.is_superuser = True
                changed = True

            if changed:
                user.set_password(password)
                if email and not user.email:
                    user.email = email
                user.save()
                self.stdout.write(self.style.SUCCESS(
                    f"bootstrap_admin: promoted existing user '{username}' to superuser."
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"bootstrap_admin: superuser '{username}' already exists; nothing to do."
                ))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(
            f"bootstrap_admin: created superuser '{username}'."
        ))
