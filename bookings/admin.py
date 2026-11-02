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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "service" and field:
            field.label_from_instance = lambda service: (
                f"{service.title} - "
                f"{service.technician.user.get_full_name() or service.technician.user.username} "
                f"({service.category.name}, #{service.pk})"
            )
        return field
