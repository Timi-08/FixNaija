from django.contrib import admin

from .models import IssueReport, Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("technician", "reviewer", "rating", "booking", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("technician__user__username", "reviewer__username", "comment")
    list_select_related = ("technician__user", "reviewer", "booking")
    readonly_fields = ("created_at",)


@admin.action(description="Mark selected reports as resolved")
def mark_resolved(modeladmin, request, queryset):
    queryset.update(status=IssueReport.RESOLVED)


@admin.register(IssueReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = ("subject", "reporter", "booking", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("subject", "message", "reporter__username")
    list_editable = ("status",)
    list_select_related = ("reporter", "booking")
    actions = [mark_resolved]
