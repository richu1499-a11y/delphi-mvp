from __future__ import annotations

from collections import Counter
from typing import Dict, Tuple

from django.db.models import Q
from django.utils import timezone

from .models import RoundItem, Response, FeedbackStat, Item


LIKERT_LEVELS = [1, 2, 3, 4, 5]


def compute_feedback_for_round_item(round_item: RoundItem, overwrite: bool = True) -> FeedbackStat:
    """Compute group feedback for one item in one round using the latest response per panelist (enforced by unique constraint)."""
    item = round_item.item
    qs = Response.objects.filter(round_item=round_item)

    if item.response_type == Item.ResponseType.LIKERT_5:
        vals = [r.likert_value for r in qs if r.likert_value is not None]
        n = len(vals)
        dist = Counter(vals)
        dist_json = {str(k): int(dist.get(k, 0)) for k in LIKERT_LEVELS}
        mean = (sum(vals) / n) if n else None

        agree = sum(dist.get(k, 0) for k in (4, 5))
        disagree = sum(dist.get(k, 0) for k in (1, 2))
        pct_agree = (agree / n) if n else None
        pct_disagree = (disagree / n) if n else None

        # Protocol: consensus if either agreement or disagreement exceeds 75%
        consensus = bool(n) and (pct_agree >= 0.75 or pct_disagree >= 0.75)

    else:
        vals = [r.either_or_value for r in qs if r.either_or_value in ("A", "B")]
        n = len(vals)
        dist = Counter(vals)
        dist_json = {"A": int(dist.get("A", 0)), "B": int(dist.get("B", 0))}
        mean = None
        # Map consensus to % on majority option
        maj = max(dist_json.values()) if n else 0
        pct_agree = (maj / n) if n else None
        pct_disagree = None
        consensus = bool(n) and (pct_agree >= 0.75)

    stat, created = FeedbackStat.objects.get_or_create(round_item=round_item)
    if overwrite or created:
        stat.n = n
        stat.mean = mean
        stat.pct_agree = pct_agree
        stat.pct_disagree = pct_disagree
        stat.consensus = consensus
        stat.distribution_json = dist_json
        stat.computed_at = timezone.now()
        stat.save()
    return stat


def compute_feedback_for_round(round_id: int, overwrite: bool = True) -> int:
    count = 0
    for ri in RoundItem.objects.filter(round_id=round_id).select_related("item"):
        compute_feedback_for_round_item(ri, overwrite=overwrite)
        count += 1
    return count
