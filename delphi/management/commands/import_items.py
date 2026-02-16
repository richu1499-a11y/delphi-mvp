from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from delphi.models import Study, Item


class Command(BaseCommand):
    help = "Import items from CSV with columns: stable_code,domain_tag,stem_text,response_type,option_a,option_b,order_index"

    def add_arguments(self, parser):
        parser.add_argument("--study_id", type=int, required=True)
        parser.add_argument("--csv", type=str, required=True)

    def handle(self, *args, **options):
        study_id = options["study_id"]
        csv_path = Path(options["csv"])
        if not csv_path.exists():
            raise CommandError(f"CSV not found: {csv_path}")

        study = Study.objects.get(id=study_id)

        created = 0
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stable_code = (row.get("stable_code") or "").strip()
                stem_text = (row.get("stem_text") or "").strip()
                if not stable_code or not stem_text:
                    continue

                item = Item.objects.create(
                    study=study,
                    stable_code=stable_code,
                    domain_tag=(row.get("domain_tag") or "").strip(),
                    stem_text=stem_text,
                    response_type=(row.get("response_type") or Item.ResponseType.LIKERT_5).strip() or Item.ResponseType.LIKERT_5,
                    option_a=(row.get("option_a") or "").strip(),
                    option_b=(row.get("option_b") or "").strip(),
                    order_index=int(row.get("order_index") or 0),
                    version=int(row.get("version") or 1),
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {created} items into study {study_id}."))
