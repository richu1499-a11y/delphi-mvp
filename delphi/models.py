from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import Optional

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class Study(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.title


class Round(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"

    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="rounds")
    number = models.PositiveSmallIntegerField()  # 1, 2, ...
    name = models.CharField(max_length=255, default="")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)

    # Protocol behavior:
    # - In round 1, show group average only AFTER participant's first submission in that round.
    # - In round 2, show group average immediately (and optionally show participant's prior round rating).
    show_feedback_immediately = models.BooleanField(default=False)
    show_prior_round_rating = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.study_id} - R{self.number} {self.name or ''}".strip()

    @property
    def is_open(self) -> bool:
        if self.status != Round.Status.OPEN:
            return False
        now = timezone.now()
        if self.opens_at and now < self.opens_at:
            return False
        if self.closes_at and now > self.closes_at:
            return False
        return True


class Item(models.Model):
    class ResponseType(models.TextChoices):
        LIKERT_5 = "LIKERT_5", "Likert 5-point"
        EITHER_OR = "EITHER_OR", "Either/Or"

    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="items")
    stable_code = models.CharField(max_length=50)  # e.g., Q1, Q2...
    domain_tag = models.CharField(max_length=100, blank=True)
    stem_text = models.TextField()

    response_type = models.CharField(max_length=16, choices=ResponseType.choices, default=ResponseType.LIKERT_5)

    # For EITHER_OR, store option labels:
    option_a = models.CharField(max_length=255, blank=True)
    option_b = models.CharField(max_length=255, blank=True)

    order_index = models.PositiveIntegerField(default=0)

    # Versioning (for moderator-edited canonical wording between rounds)
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("study", "stable_code", "version")
        ordering = ["order_index", "stable_code", "version"]

    def __str__(self) -> str:
        return f"{self.stable_code} (v{self.version})"


class Panelist(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="panelists")
    email = models.EmailField()
    display_name = models.CharField(max_length=255, blank=True)
    affiliation = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("study", "email")
        ordering = ["email"]

    def __str__(self) -> str:
        return self.display_name or self.email


class MagicLink(models.Model):
    panelist = models.ForeignKey(Panelist, on_delete=models.CASCADE, related_name="magic_links")
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    @staticmethod
    def mint(panelist: Panelist, ttl_hours: int = 72) -> "MagicLink":
        token = secrets.token_urlsafe(32)
        return MagicLink.objects.create(
            panelist=panelist,
            token=token,
            expires_at=timezone.now() + timedelta(hours=ttl_hours),
        )

    @property
    def is_valid(self) -> bool:
        if self.used_at is not None:
            return False
        return timezone.now() <= self.expires_at

    def __str__(self) -> str:
        return f"MagicLink({self.panelist.email})"


class RoundItem(models.Model):
    """Snapshot of which item version is used in a given round."""
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="round_items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="round_items")

    class Meta:
        unique_together = ("round", "item")
        ordering = ["item__order_index", "item__stable_code"]

    def __str__(self) -> str:
        return f"R{self.round.number}: {self.item}"


class Response(models.Model):
    round_item = models.ForeignKey(RoundItem, on_delete=models.CASCADE, related_name="responses")
    panelist = models.ForeignKey(Panelist, on_delete=models.CASCADE, related_name="responses")

    # Likert 1-5
    likert_value = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )

    # Either/Or: store 'A' or 'B'
    either_or_value = models.CharField(max_length=1, null=True, blank=True)

    comment = models.TextField(blank=True)
    suggested_revision = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("round_item", "panelist")

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.panelist.email} - {self.round_item}"


class FeedbackStat(models.Model):
    """Cached group summary for an item within a round (supports real-time updates or freeze-on-close)."""
    round_item = models.OneToOneField(RoundItem, on_delete=models.CASCADE, related_name="feedback")
    n = models.PositiveIntegerField(default=0)
    mean = models.FloatField(null=True, blank=True)
    pct_agree = models.FloatField(null=True, blank=True)      # % in 4-5
    pct_disagree = models.FloatField(null=True, blank=True)   # % in 1-2
    consensus = models.BooleanField(default=False)
    distribution_json = models.JSONField(default=dict)        # {'1':x,'2':y,'3':z,'4':a,'5':b} or {'A':x,'B':y}
    computed_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return f"Feedback({self.round_item})"
