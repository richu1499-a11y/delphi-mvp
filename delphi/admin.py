from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Study, Round, Item, RoundItem, Panelist, 
    MagicLink, Response, RoundSubmission, FeedbackAggregate
)


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')


@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ('study', 'number', 'is_open', 'show_feedback_immediately', 'created_at')
    list_filter = ('study', 'is_open')
    list_editable = ('is_open', 'show_feedback_immediately')


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('prompt_short', 'study', 'item_type', 'created_at')
    list_filter = ('study', 'item_type')
    search_fields = ('prompt',)
    
    fieldsets = (
        (None, {
            'fields': ('study', 'prompt', 'item_type')
        }),
        ('Multiple Choice Options', {
            'fields': ('option_a', 'option_b', 'option_c', 'option_d', 'option_e', 'option_f'),
            'classes': ('collapse',),
            'description': 'Used for Multiple Choice and Checkbox question types'
        }),
        ('Matrix Question Settings', {
            'fields': ('matrix_rows', 'matrix_columns'),
            'classes': ('collapse',),
            'description': 'Used for Matrix (checkbox grid) question types. Enter as JSON arrays.'
        }),
    )
    
    def prompt_short(self, obj):
        return obj.prompt[:75] + "..." if len(obj.prompt) > 75 else obj.prompt
    prompt_short.short_description = "Prompt"


@admin.register(RoundItem)
class RoundItemAdmin(admin.ModelAdmin):
    list_display = ('round', 'item', 'order')
    list_filter = ('round__study', 'round')
    list_editable = ('order',)
    ordering = ('round', 'order')


@admin.register(Panelist)
class PanelistAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'institution', 'study', 'is_active', 'login_link')
    list_filter = ('study', 'is_active')
    search_fields = ('email', 'name', 'institution')
    list_editable = ('is_active',)
    readonly_fields = ('token', 'login_url_display', 'created_at')
    
    fieldsets = (
        (None, {
            'fields': ('study', 'email', 'name', 'institution', 'is_active')
        }),
        ('Access Token', {
            'fields': ('token', 'login_url_display'),
            'description': 'Share the login URL with this panelist. The token never expires.'
        }),
        ('Info', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def login_link(self, obj):
        url = f"/login/{obj.token}/"
        return format_html('<a href="{}" target="_blank">Login Link</a>', url)
    login_link.short_description = "Quick Link"
    
    def login_url_display(self, obj):
        url = f"/login/{obj.token}/"
        full_url = f"https://delphi-mvp.onrender.com{url}"
        return format_html(
            '<input type="text" value="{}" readonly style="width: 100%; padding: 8px; font-family: monospace;" onclick="this.select()">',
            full_url
        )
    login_url_display.short_description = "Full Login URL (click to select, then copy)"


@admin.register(MagicLink)
class MagicLinkAdmin(admin.ModelAdmin):
    list_display = ('panelist', 'token', 'created_at', 'expires_at', 'used_at')
    list_filter = ('panelist__study',)
    search_fields = ('panelist__email',)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('panelist', 'round_item', 'value', 'created_at')
    list_filter = ('round_item__round__study', 'round_item__round')
    search_fields = ('panelist__email',)


@admin.register(RoundSubmission)
class RoundSubmissionAdmin(admin.ModelAdmin):
    list_display = ('panelist', 'round', 'submitted_at')
    list_filter = ('round__study', 'round')


@admin.register(FeedbackAggregate)
class FeedbackAggregateAdmin(admin.ModelAdmin):
    list_display = ('round_item', 'n', 'mean', 'pct_agree', 'consensus_reached', 'computed_at')
    list_filter = ('round_item__round__study', 'round_item__round', 'consensus_reached')