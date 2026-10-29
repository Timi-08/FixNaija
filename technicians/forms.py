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
    username = forms.CharField(
        label="Username",
        required=False,
        disabled=True,
    )

    email = forms.EmailField(
        label="Email",
        required=False,
        disabled=True,
    )

    class Meta:
        model = TechnicianProfile
        fields = [
            'professional_info',
            'base_location',
            'profile_picture',
        ]

        widgets = {
            'professional_info': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe your skills and experience',
            }),
            'base_location': forms.TextInput(attrs={
                'placeholder': 'Enter your service location',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['username'].initial = (
                self.instance.user.username
            )
            self.fields['email'].initial = (
                self.instance.user.email
            )

        self.order_fields([
                'username',
                'email',
                'professional_info',
                'base_location',
                'profile_picture',
            ])
