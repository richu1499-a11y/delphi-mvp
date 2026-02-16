from __future__ import annotations

from collections import defaultdict

from django.core.management.base import BaseCommand

from delphi.models import Round, Item, RoundItem


class Command(BaseCommand):
    help = "Attach latest item versions in a study to a given round."

    def add_arguments(self, parser):
        parser.add_argument("--round_id", type=int, required=True)
        parser.add_argument("--overwrite", action="store_true")

    def handle(self, *args, **options):
        round_id = options["round_id"]
        overwrite = bool(options["overwrite"])

        rnd = Round.objects.select_related("study").get(id=round_id)

        if overwrite:
            RoundItem.objects.filter(round=rnd).delete()

        # pick latest version per stable_code
        latest = {}
        for item in Item.objects.filter(study=rnd.study).order_by("stable_code", "-version"):
            if item.stable_code not in latest:
                latest[item.stable_code] = item

        created = 0
        for code, item in sorted(latest.items(), key=lambda kv: (kv[1].order_index, kv[0])):
            _, was_created = RoundItem.objects.get_or_create(round=rnd, item=item)
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Round {round_id}: attached {created} items (latest versions)."))
