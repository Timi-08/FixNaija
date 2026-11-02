from django import forms
from django.db.models import Q

from bookings.models import Booking

from .models import IssueReport, Review


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(i, f"{i} out of 5") for i in range(5, 0, -1)],
        coerce=int,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Tell others about the job (optional)"}
            )
        }

    def __init__(self, *args, booking, reviewer, **kwargs):
        super().__init__(*args, **kwargs)
        self.booking = booking
        self.reviewer = reviewer

    def clean(self):
        cleaned = super().clean()
        if self.booking.status != Booking.COMPLETED:
            raise forms.ValidationError("You can only review a completed job.")
        if self.booking.customer_id != self.reviewer.id:
            raise forms.ValidationError("Only the customer of this booking can review it.")
        if Review.objects.filter(booking=self.booking).exists():
            raise forms.ValidationError("You have already reviewed this job.")
        return cleaned

    def save(self, commit=True):
        review = super().save(commit=False)
        review.booking = self.booking
        review.reviewer = self.reviewer
        review.technician = self.booking.technician
        if commit:
            review.save()
        return review


class IssueReportForm(forms.ModelForm):
    class Meta:
        model = IssueReport
        fields = ["booking", "subject", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["booking"].required = False
        self.fields["booking"].label = "Related booking (optional)"
        self.fields["booking"].queryset = Booking.objects.filter(
            Q(customer=user) | Q(technician__user=user)
        ).select_related("service")

    def save(self, commit=True):
        report = super().save(commit=False)
        report.reporter = self.user
        if commit:
            report.save()
        return report
