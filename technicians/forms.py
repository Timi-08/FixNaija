from django import forms
from .models import ServiceListing, ServiceCategory, ServiceArea, TechnicianProfile, TechnicianVerificationRequest, PortfolioImage


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
    def __init__(self, *args, technician=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['category'].queryset = ServiceCategory.objects.filter(
            is_active=True
        )
        if technician and technician.categories.filter(is_active=True).exists():
            self.fields['category'].queryset = technician.categories.filter(
                is_active=True
            )
            if self.instance.pk:
                self.fields['category'].queryset = (
                    self.fields['category'].queryset
                    | ServiceCategory.objects.filter(
                        pk=self.instance.category_id,
                        is_active=True,
                    )
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
    phone = forms.CharField(label="Phone number", max_length=20)

    class Meta:
        model = TechnicianProfile
        fields = [
            'categories',
            'base_locations',
            'professional_info',
            'profile_picture',
        ]

        widgets = {
            'categories': forms.SelectMultiple(attrs={
                'size': 6,
            }),
            'base_locations': forms.SelectMultiple(attrs={
                'size': 8,
            }),
            'professional_info': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Describe your skills and experience',
            }),
        }

    def __init__(self, *args, user=None, user_profile=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user or getattr(self.instance, 'user', None)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email
        if user_profile:
            self.fields['phone'].initial = user_profile.phone

        self.fields['categories'].queryset = ServiceCategory.objects.filter(
            is_active=True
        )
        self.fields['base_locations'].queryset = ServiceArea.objects.filter(
            is_active=True
        )
        self.fields['categories'].required = True
        self.fields['base_locations'].required = True
        self.fields['phone'].required = True

        self.order_fields([
                'username',
                'email',
                'phone',
                'categories',
                'base_locations',
                'professional_info',
                'profile_picture',
            ])

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not phone:
            raise forms.ValidationError("Phone number is required.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        if not self.user:
            raise forms.ValidationError("A user account is required.")
        return cleaned_data

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

# uploading a portfolio picture
class PortfolioImageForm(forms.ModelForm):
    class Meta:
        model = PortfolioImage
        fields = ["image", "caption"]

    def clean_image(self):
        image = self.cleaned_data["image"]
        if image.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Image must be 5MB or smaller.")
        return image
