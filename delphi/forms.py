from __future__ import annotations

from django import forms

from .models import Item


class Likert5Form(forms.Form):
    likert_value = forms.ChoiceField(
        choices=[
            ("1", "Strongly disagree"),
            ("2", "Disagree"),
            ("3", "Neutral"),
            ("4", "Agree"),
            ("5", "Strongly agree"),
        ],
        widget=forms.RadioSelect,
        required=True,
    )
    comment = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
    suggested_revision = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Optional: suggest revised wording"}),
        required=False,
    )


class EitherOrForm(forms.Form):
    either_or_value = forms.ChoiceField(
        choices=[("A", "Option A"), ("B", "Option B")],
        widget=forms.RadioSelect,
        required=True,
    )
    comment = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}), required=False)
    suggested_revision = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Optional: suggest revised wording"}),
        required=False,
    )

    def set_option_labels(self, option_a: str, option_b: str):
        self.fields["either_or_value"].choices = [("A", option_a), ("B", option_b)]
