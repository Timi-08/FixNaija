from django import forms
from django.utils import timezone

from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["area", "address", "preferred_date", "description"]
        widgets = {
            "address": forms.TextInput(attrs={"placeholder": "Street and landmark"}),
            "preferred_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, customer, service, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer = customer
        self.service = service
        self.fields["area"].queryset = service.service_areas.filter(is_active=True)
        self.fields["area"].label = "Area"
        self.fields["area"].empty_label = "Choose your area"

    def clean_address(self):
        address = self.cleaned_data["address"].strip()
        if len(address) < 8:
            raise forms.ValidationError(
                "Give a fuller address so the technician can find you."
            )
        return address

    def clean_preferred_date(self):
        date = self.cleaned_data.get("preferred_date")
        if date and date < timezone.localdate():
            raise forms.ValidationError("The preferred date cannot be in the past.")
        return date

    def clean(self):
        cleaned = super().clean()
        technician = self.service.technician
        if technician.user_id == self.customer.id:
            raise forms.ValidationError("You cannot book your own service.")
        if not self.service.is_active or self.service.is_deleted:
            raise forms.ValidationError("This service is not available right now.")
        if not technician.user.is_active:
            raise forms.ValidationError("This technician is not available.")
        return cleaned

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.customer = self.customer
        booking.service = self.service
        booking.technician = self.service.technician
        if commit:
            booking.save()
        return booking
