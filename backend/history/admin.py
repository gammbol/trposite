from django.contrib import admin

from .models import Solution


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ("id", "equation_preview", "created_at")
    search_fields = ("equation", "solution")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    @admin.display(description="Equation")
    def equation_preview(self, obj):
        value = obj.equation or ""
        return value if len(value) <= 80 else f"{value[:77]}..."
