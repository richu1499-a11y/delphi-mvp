from __future__ import annotations

from django.core.management.base import BaseCommand

from delphi.models import Study, Panelist, MagicLink


class Command(BaseCommand):
    help = "Mint (and optionally email) magic-link invitations for all active panelists in a study."

    def add_arguments(self, parser):
        parser.add_argument("--study_id", type=int, required=True)
        parser.add_argument("--base_url", type=str, default="http://127.0.0.1:8000")
        parser.add_argument("--ttl_hours", type=int, default=72)
        parser.add_argument("--dry_run", action="store_true")

    def handle(self, *args, **options):
        study = Study.objects.get(id=options["study_id"])
        base_url = options["base_url"].rstrip("/")
        ttl = options["ttl_hours"]
        dry_run = bool(options["dry_run"])

        panelists = Panelist.objects.filter(study=study, is_active=True).order_by("email")
        self.stdout.write(f"Minting links for {panelists.count()} panelists...")

        for p in panelists:
            link = MagicLink.mint(panelist=p, ttl_hours=ttl)
            url = f"{base_url}/login/{link.token}/"
            # TODO: integrate SMTP/SendGrid; for now print links so you can paste into an email merge.
            self.stdout.write(f"{p.email}\t{url}")

        self.stdout.write(self.style.SUCCESS("Done."))
