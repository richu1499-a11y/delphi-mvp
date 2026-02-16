from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from delphi.models import Study, Response


class Command(BaseCommand):
    help = "Export responses for a study to CSV."

    def add_arguments(self, parser):
        parser.add_argument("--study_id", type=int, required=True)
        parser.add_argument("--out", type=str, required=True)

    def handle(self, *args, **options):
        study_id = options["study_id"]
        out_path = Path(options["out"])

        study = Study.objects.get(id=study_id)

        qs = (
            Response.objects.filter(panelist__study=study)
            .select_related("panelist", "round_item__round", "round_item__item")
            .order_by("round_item__round__number", "round_item__item__order_index", "round_item__item__stable_code", "panelist__email")
        )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                "study_id",
                "round_number",
                "round_name",
                "stable_code",
                "item_version",
                "domain_tag",
                "stem_text",
                "response_type",
                "panelist_email",
                "likert_value",
                "either_or_value",
                "comment",
                "suggested_revision",
                "updated_at",
            ])
            for r in qs:
                item = r.round_item.item
                rnd = r.round_item.round
                w.writerow([
                    study_id,
                    rnd.number,
                    rnd.name,
                    item.stable_code,
                    item.version,
                    item.domain_tag,
                    item.stem_text,
                    item.response_type,
                    r.panelist.email,
                    r.likert_value or "",
                    r.either_or_value or "",
                    r.comment,
                    r.suggested_revision,
                    r.updated_at.isoformat(),
                ])

        self.stdout.write(self.style.SUCCESS(f"Exported {qs.count()} responses to {out_path}"))
