from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from delphi.models import Study, Panelist


class Command(BaseCommand):
    help = "Import panelists from CSV with columns: email,display_name,affiliation"

    def add_arguments(self, parser):
        parser.add_argument("--study_id", type=int, required=True)
        parser.add_argument("--csv", type=str, required=True)

    def handle(self, *args, **options):
        study_id = options["study_id"]
        csv_path = Path(options["csv"])
        if not csv_path.exists():
            raise CommandError(f"CSV not found: {csv_path}")

        study = Study.objects.get(id=study_id)

        created, updated = 0, 0
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = (row.get("email") or "").strip().lower()
                if not email:
                    continue
                obj, was_created = Panelist.objects.update_or_create(
                    study=study,
                    email=email,
                    defaults={
                        "display_name": (row.get("display_name") or "").strip(),
                        "affiliation": (row.get("affiliation") or "").strip(),
                        "is_active": True,
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(f"Panelists created={created}, updated={updated} for study {study_id}."))
