import uuid
from django.db import models
from django.utils import timezone


class Study(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Studies"

    def __str__(self):
        return self.name


class Round(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="rounds")
    number = models.PositiveIntegerField()
    is_open = models.BooleanField(default=True)
    show_feedback_immediately = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("study", "number")
        ordering = ["study_id", "number"]

    def __str__(self):
        return f"{self.study.name} — Round {self.number}"


class Item(models.Model):
    SCALE_CHOICES = [
        ("likert5", "Likert 1–5 (Strongly Disagree to Strongly Agree)"),
        ("yesno", "Yes/No"),
        ("multiple", "Multiple Choice (Custom Options)"),
        ("text", "Free text"),
        ("matrix", "Matrix (Checkbox grid)"),
        ("checkbox", "Checkbox (Select multiple)"),
    ]
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="items")
    prompt = models.TextField(help_text="The question or statement to present to panelists")
    item_type = models.CharField(max_length=20, choices=SCALE_CHOICES, default="likert5")

    # Custom options for multiple choice questions
    option_a = models.CharField(max_length=500, blank=True, help_text="Option A (for multiple choice)")
    option_b = models.CharField(max_length=500, blank=True, help_text="Option B (for multiple choice)")
    option_c = models.CharField(max_length=500, blank=True, help_text="Option C (for multiple choice)")
    option_d = models.CharField(max_length=500, blank=True, help_text="Option D (for multiple choice)")
    option_e = models.CharField(max_length=500, blank=True, help_text="Option E (for multiple choice)")
    option_f = models.CharField(max_length=500, blank=True, help_text="Option F (for multiple choice)")

    # For matrix questions - stores JSON list of row labels
    matrix_rows = models.TextField(blank=True, help_text="JSON list of row labels for matrix questions")
    # For matrix questions - stores JSON list of column headers
    matrix_columns = models.TextField(blank=True, help_text="JSON list of column headers for matrix questions")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.study.name}] {self.prompt[:50]}..."

    def get_options(self):
        """Returns a list of non-empty options for multiple choice questions."""
        options = []
        if self.option_a:
            options.append(('A', self.option_a))
        if self.option_b:
            options.append(('B', self.option_b))
        if self.option_c:
            options.append(('C', self.option_c))
        if self.option_d:
            options.append(('D', self.option_d))
        if self.option_e:
            options.append(('E', self.option_e))
        if self.option_f:
            options.append(('F', self.option_f))
        return options

    def get_matrix_rows(self):
        """Returns list of row labels for matrix questions."""
        import json
        if self.matrix_rows:
            return json.loads(self.matrix_rows)
        return []

    def get_matrix_columns(self):
        """Returns list of column headers for matrix questions."""
        import json
        if self.matrix_columns:
            return json.loads(self.matrix_columns)
        return []

class RoundItem(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="round_items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="round_items")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("round", "item")
        ordering = ["order", "id"]

    def __str__(self):
        return f"Round {self.round.number}: {self.item.prompt[:40]}..."


class Panelist(models.Model):
    study = models.ForeignKey(Study, on_delete=models.CASCADE, related_name="panelists")
    email = models.EmailField()
    name = models.CharField(max_length=255, blank=True)
    institution = models.CharField(max_length=255, blank=True, help_text="Institution/Affiliation")
    is_active = models.BooleanField(default=True)
    
    # Permanent access token - auto-generated, never expires
    token = models.UUIDField(default=uuid.uuid4, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("study", "email")

    def __str__(self):
        return f"{self.name} ({self.email})" if self.name else self.email
    
    def get_login_url(self):
        """Returns the full login URL for this panelist."""
        return f"/login/{self.token}/"


# Keep MagicLink for backward compatibility, but we won't use it anymore
class MagicLink(models.Model):
    panelist = models.ForeignKey(Panelist, on_delete=models.CASCADE, related_name="magic_links")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        if not self.panelist.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def __str__(self):
        return f"Link for {self.panelist.email}"


class Response(models.Model):
    panelist = models.ForeignKey(Panelist, on_delete=models.CASCADE, related_name="responses")
    round_item = models.ForeignKey(RoundItem, on_delete=models.CASCADE, related_name="responses")
    value = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("panelist", "round_item")

    def __str__(self):
        return f"{self.panelist.email} — R{self.round_item.round.number} item {self.round_item_id}"


class RoundSubmission(models.Model):
    """Marks a panelist's round as final/locked."""
    panelist = models.ForeignKey(Panelist, on_delete=models.CASCADE, related_name="round_submissions")
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="submissions")
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("panelist", "round")
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.panelist.email} — submitted R{self.round.number}"


class FeedbackAggregate(models.Model):
    """Stores summary stats per (RoundItem) after round is closed or after submissions."""
    round_item = models.OneToOneField(RoundItem, on_delete=models.CASCADE, related_name="aggregate")
    mean = models.FloatField(null=True, blank=True)
    median = models.FloatField(null=True, blank=True)
    std_dev = models.FloatField(null=True, blank=True)
    n = models.PositiveIntegerField(default=0)
    pct_agree = models.FloatField(null=True, blank=True, help_text="Percentage of 4 or 5 ratings")
    pct_disagree = models.FloatField(null=True, blank=True, help_text="Percentage of 1 or 2 ratings")
    consensus_reached = models.BooleanField(default=False, help_text="True if >=75% agreement")
    computed_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Agg for RoundItem {self.round_item_id}"