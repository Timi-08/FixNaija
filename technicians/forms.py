from django import forms
from .models import ServiceListing, ServiceCategory, ServiceArea, TechnicianProfile


# Creating a service
class ServiceListingForm(forms.ModelForm):
    class Meta:
        model = ServiceListing
        fields = [
            'title',
            'category',
            'description',
            'min_price',
            'max_price',
            'service_areas',
        ]

# filter out inactive fields i.e categories and areas
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['category'].queryset = ServiceCategory.objects.filter(
            is_active=True
        )

        self.fields['service_areas'].queryset = ServiceArea.objects.filter(
            is_active=True
    )

# Creating a technician profile
class TechnicianProfileForm(forms.ModelForm):
    class Meta:
        model = TechnicianProfile
        fields = [
            'professional_info',
            'base_location',
            'profile_picture',
        ]