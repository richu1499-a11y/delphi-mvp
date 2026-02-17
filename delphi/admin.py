from django.contrib import admin
from django.utils.html import format_html

from .models import (
    FeedbackAggregate,
    Item,
    MagicLink,
    Panelist,
    Response,
    Round,
    RoundItem,
    Study,
    RoundSubmission,
)


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ("study", "number", "is_open", "show_feedback_immediately", "created_at")
    list_filter = ("study", "is_open", "show_feedback_immediately")
    search_fields = ("study__name",)
    ordering = ("study", "number")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("study", "item_type", "prompt_short", "created_at")
    list_filter = ("study", "item_type")
    search_fields = ("prompt",)

    def prompt_short(self, obj):
        return (obj.prompt[:60] + "...") if len(obj.prompt) > 60 else obj.prompt


@admin.register(RoundItem)
class RoundItemAdmin(admin.ModelAdmin):
    list_display = ("round", "order", "item_short")
    list_filter = ("round__study", "round__number")
    search_fields = ("item__prompt",)
    ordering = ("round__study", "round__number", "order")

    def item_short(self, obj):
        return (obj.item.prompt[:60] + "...") if len(obj.item.prompt) > 60 else obj.item.prompt


@admin.register(Panelist)
class PanelistAdmin(admin.ModelAdmin):
    list_display = ("study", "email", "name", "is_active", "created_at")
    list_filter = ("study", "is_active")
    search_fields = ("email", "name")


@admin.register(MagicLink)
class MagicLinkAdmin(admin.ModelAdmin):
    list_display = ("panelist", "token", "expires_at", "login_link", "created_at")
    list_filter = ("panelist__study",)
    search_fields = ("panelist__email",)

    def login_link(self, obj):
        url = f"https://delphi-mvp.onrender.com/magic/{obj.token}/"
        return format_html('<a href="{}" target="_blank">{}</a>', url, "open link")


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("panelist", "round_item", "value", "created_at")
    list_filter = ("panelist__study", "round_item__round__number")
    search_fields = ("panelist__email", "round_item__item__prompt", "value")


@admin.register(RoundSubmission)
class RoundSubmissionAdmin(admin.ModelAdmin):
    list_display = ("panelist", "round", "submitted_at")
    list_filter = ("round__study", "round__number")
    search_fields = ("panelist__email",)


@admin.register(FeedbackAggregate)
class FeedbackAggregateAdmin(admin.ModelAdmin):
    list_display = ("round_item", "mean", "median", "n", "computed_at")
