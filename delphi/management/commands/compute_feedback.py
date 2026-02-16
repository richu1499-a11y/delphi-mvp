from __future__ import annotations

from django.core.management.base import BaseCommand

from delphi.services import compute_feedback_for_round


class Command(BaseCommand):
    help = "Compute feedback stats for every item in a round."

    def add_arguments(self, parser):
        parser.add_argument("--round_id", type=int, required=True)
        parser.add_argument("--overwrite", action="store_true")

    def handle(self, *args, **options):
        round_id = options["round_id"]
        overwrite = bool(options["overwrite"])
        n = compute_feedback_for_round(round_id, overwrite=overwrite)
        self.stdout.write(self.style.SUCCESS(f"Computed feedback for {n} items in round {round_id}."))
