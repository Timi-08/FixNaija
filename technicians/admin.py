from django.contrib import admin
from .models import ServiceCategory,ServiceArea, ServiceListing, TechnicianProfile, TechnicianVerificationRequest
from .forms import TechnicianVerificationAdminForm
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html

# Register your models here.

@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    search_fields = ('name', 'slug')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ServiceArea)
class ServiceAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)
    
@admin.register(ServiceListing)
class ServiceListingAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'technician',
        'category',
        'min_price',
        'max_price',
        'is_active',
        'is_deleted',
        'created_at',
    )
    search_fields = (
        'title',
        'description',
        'technician__user__username',
        'category__name',
    )
    list_filter = (
        'category',
        'is_active',
        'is_deleted',
        'created_at',
    )
    list_select_related = ('technician__user', 'category')
    filter_horizontal = ('service_areas',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    
@admin.register(TechnicianProfile)
class TechnicianProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'base_location',
        'is_verified',
        'created_at',
    )
    search_fields = (
        'user__username',
        'user__email',
        'base_location',
    )
    list_filter = ('is_verified', 'created_at')
    list_select_related = ('user',)
    readonly_fields = ('created_at',)

@admin.register(TechnicianVerificationRequest)
class TechnicianVerificationRequestAdmin(admin.ModelAdmin):
    form = TechnicianVerificationAdminForm

    list_display = (
        "technician",
        "status",
        "submitted_at",
        "reviewed_by",
        "reviewed_at",
    )

    list_filter = ("status", "submitted_at")
    search_fields = (
        "technician__user__username",
        "technician__user__email",
    )

    fields = (
    "technician",
    "identity_document_link",
    "qualification_document_link",
    "status",
    "review_notes",
    "submitted_at",
    "reviewed_by",
    "reviewed_at",
    )

    readonly_fields = (
        "identity_document_link",
        "qualification_document_link",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
    )

    def save_model(self, request, obj, form, change):
        if obj.status in (
            TechnicianVerificationRequest.Status.APPROVED,
            TechnicianVerificationRequest.Status.REJECTED,
        ):
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()

        super().save_model(request, obj, form, change)

        if obj.status == TechnicianVerificationRequest.Status.APPROVED:
            obj.technician.is_verified = True
        elif obj.status == TechnicianVerificationRequest.Status.REJECTED:
            obj.technician.is_verified = False

        obj.technician.save(update_fields=["is_verified"])

    @admin.display(description="Identity document")
    def identity_document_link(self, obj):
        if not obj.identity_document:
            return "No document uploaded"

        url = reverse(
            "technicians:view_verification_document",
            args=[obj.pk, "identity"],
        )
        return format_html('<a href="{}" target="_blank">View document</a>', url)


    @admin.display(description="Qualification document")
    def qualification_document_link(self, obj):
        if not obj.qualification_document:
            return "No document uploaded"

        url = reverse(
            "technicians:view_verification_document",
            args=[obj.pk, "qualification"],
        )
        return format_html('<a href="{}" target="_blank">View document</a>', url)