from django import forms
from .models import ServiceListing, ServiceCategory, ServiceArea, TechnicianProfile, TechnicianVerificationRequest


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

# technician verificaton form
class TechnicianVerificationRequestForm(forms.ModelForm):
    class Meta:
        model = TechnicianVerificationRequest
        fields = [
            "identity_document",
            "qualification_document",
        ]

        labels = {
            "identity_document": "Identity document",
            "qualification_document": "Trade certificate or qualification (optional)",
        }

        help_texts = {
            "identity_document": "Upload a document that can help verify your identity.",
            "qualification_document": "Optional evidence of your trade skills or qualifications.",
        }

# admin review form for technician verification
class TechnicianVerificationAdminForm(forms.ModelForm):
    class Meta:
        model = TechnicianVerificationRequest
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get("status")
        reason = cleaned_data.get("review_notes", "").strip()

        if (
            status == TechnicianVerificationRequest.Status.REJECTED
            and not reason
        ):
            self.add_error(
                "review_notes",
                "You must provide a reason when rejecting a verification request."
            )

        return cleaned_data