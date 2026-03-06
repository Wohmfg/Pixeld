from django.contrib import admin, messages
from django.db import transaction
from django.utils.html import format_html

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
    list_display = ['date', 'answer_display', 'category', 'thumb']
    list_filter = ['category']
    search_fields = ['answer_display', 'answer']
    date_hierarchy = 'date'
    readonly_fields = ['thumb']
    fieldsets = [
        (None, {'fields': ['date', 'category']}),
        ('Answer', {'fields': ['answer', 'answer_display', 'aliases', 'hint']}),
        ('Image', {'fields': ['image', 'thumb']}),
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
