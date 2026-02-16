from django.contrib import admin

from .models import Study, Round, Item, Panelist, MagicLink, RoundItem, Response, FeedbackStat


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at")
    search_fields = ("title",)


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ("id", "study", "number", "name", "status", "opens_at", "closes_at", "show_feedback_immediately")
    list_filter = ("status", "study")
    ordering = ("study", "number")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "study", "stable_code", "version", "response_type", "domain_tag", "order_index", "updated_at")
    list_filter = ("study", "response_type")
    search_fields = ("stable_code", "stem_text", "domain_tag")
    ordering = ("study", "order_index", "stable_code", "version")


@admin.register(Panelist)
class PanelistAdmin(admin.ModelAdmin):
    list_display = ("id", "study", "email", "display_name", "affiliation", "is_active", "created_at")
    list_filter = ("study", "is_active")
    search_fields = ("email", "display_name", "affiliation")


@admin.register(MagicLink)
class MagicLinkAdmin(admin.ModelAdmin):
    list_display = ("id", "panelist", "created_at", "expires_at", "used_at")
    list_filter = ("panelist__study",)


@admin.register(RoundItem)
class RoundItemAdmin(admin.ModelAdmin):
    list_display = ("id", "round", "item")
    list_filter = ("round__study", "round")
    search_fields = ("item__stable_code", "item__stem_text")


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ("id", "round_item", "panelist", "likert_value", "either_or_value", "updated_at")
    list_filter = ("round_item__round", "round_item__round__study")
    search_fields = ("panelist__email", "round_item__item__stable_code")


@admin.register(FeedbackStat)
class FeedbackStatAdmin(admin.ModelAdmin):
    list_display = ("id", "round_item", "n", "mean", "pct_agree", "pct_disagree", "consensus", "computed_at")
    list_filter = ("round_item__round", "round_item__round__study", "consensus")
