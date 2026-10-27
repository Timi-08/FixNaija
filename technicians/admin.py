from django.contrib import admin
from .models import ServiceCategory,ServiceArea, ServiceListing, TechnicianProfile
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