from django.contrib import admin, messages
from django.db import transaction
from django.utils.html import format_html, mark_safe

from .models import Puzzle, PuzzleImage


class PuzzleImageInline(admin.TabularInline):
    model = PuzzleImage
    extra = 0
    readonly_fields = ['level', 'preview']
    fields = ['level', 'preview']

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" height="80" style="border-radius:4px"/>',
                obj.image.url,
            )
        return "—"
    preview.short_description = "Preview"


@admin.register(Puzzle)
class PuzzleAdmin(admin.ModelAdmin):
    list_display = ['date', 'answer_display', 'category', 'stat_plays', 'stat_wins', 'admin_win_rate', 'admin_avg_guesses', 'thumb']
    list_filter = ['category']
    search_fields = ['answer_display', 'answer']
    date_hierarchy = 'date'
    readonly_fields = ['thumb', 'admin_plays', 'admin_wins', 'admin_win_rate', 'admin_avg_guesses', 'admin_distribution']
    fieldsets = [
        (None, {'fields': ['date', 'category']}),
        ('Answer', {'fields': ['answer', 'answer_display', 'aliases', 'hint']}),
        ('Image', {'fields': ['image', 'thumb']}),
        ('Stats', {'fields': ['admin_plays', 'admin_wins', 'admin_win_rate', 'admin_avg_guesses', 'admin_distribution']}),
    ]
    inlines = [PuzzleImageInline]

    def thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" height="60" style="border-radius:4px"/>',
                obj.image.url,
            )
        return "—"
    thumb.short_description = "Original"

    def admin_plays(self, obj):
        return obj.stat_plays
    admin_plays.short_description = "Total plays"

    def admin_wins(self, obj):
        return obj.stat_wins
    admin_wins.short_description = "Total wins"

    def admin_win_rate(self, obj):
        if obj.stat_plays == 0:
            return "—"
        return f"{round(obj.stat_wins / obj.stat_plays * 100)}%"
    admin_win_rate.short_description = "Win rate"

    def admin_avg_guesses(self, obj):
        avg = obj.stat_avg_guesses
        return f"{avg}" if avg is not None else "—"
    admin_avg_guesses.short_description = "Avg guesses"

    def admin_distribution(self, obj):
        dist = obj.stat_guess_distribution
        if not dist or sum(dist) == 0:
            return "No data yet"
        max_count = max(dist) or 1
        rows = []
        for i, count in enumerate(dist):
            bar_pct = round(count / max_count * 100)
            bar = (
                f'<div style="display:flex;align-items:center;gap:8px;margin:2px 0">'
                f'<span style="width:12px;text-align:right;font-weight:bold">{i+1}</span>'
                f'<div style="background:#4a90d9;height:16px;width:{max(bar_pct,2)}%;'
                f'min-width:2px;border-radius:2px"></div>'
                f'<span>{count}</span>'
                f'</div>'
            )
            rows.append(bar)
        return mark_safe(''.join(rows))
    admin_distribution.short_description = "Guess distribution"

    def save_model(self, request, obj, form, change):
        """Wrap save in a transaction so a Pillow error rolls back the DB row."""
        try:
            with transaction.atomic():
                super().save_model(request, obj, form, change)
        except Exception as e:
            self.message_user(
                request,
                f"Could not save puzzle — image processing failed: {e}",
                messages.ERROR,
            )


@admin.register(PuzzleImage)
class PuzzleImageAdmin(admin.ModelAdmin):
    list_display = ['puzzle', 'level']
