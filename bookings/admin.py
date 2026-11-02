from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "technician",
        "service",
        "area",
        "status",
        "request_date",
    )
    list_filter = ("status", "area", "request_date")
    search_fields = (
        "customer__username",
        "technician__user__username",
        "service__title",
        "address",
    )
    list_select_related = ("customer", "technician__user", "service", "area")
    date_hierarchy = "request_date"
    readonly_fields = ("request_date", "updated_at")
    list_per_page = 25
