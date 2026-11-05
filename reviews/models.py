from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from bookings.models import Booking
from technicians.models import TechnicianProfile


class Review(models.Model):
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="review"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews_written",
    )
    technician = models.ForeignKey(
        TechnicianProfile, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        user = self.technician.user
        return f"{self.rating}/5 for {user.get_full_name() or user.username}"

    def clean(self):
        if not self.booking_id:
            return
        errors = {}
        if self.booking.status != Booking.COMPLETED:
            errors["booking"] = "You can only review a completed job."
        elif self.reviewer_id and self.booking.customer_id != self.reviewer_id:
            errors["reviewer"] = "Only the customer of this booking can review it."
        elif self.technician_id and self.booking.technician_id != self.technician_id:
            errors["technician"] = "The technician does not match the booking."
        elif Review.objects.filter(booking_id=self.booking_id).exclude(pk=self.pk).exists():
            errors["booking"] = "This booking has already been reviewed."
        if errors:
            raise ValidationError(errors)


class IssueReport(models.Model):
    """A dispute or platform issue reported by a user, handled in Django Admin."""

    OPEN = "open"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    STATUS_CHOICES = [
        (OPEN, "Open"),
        (REVIEWING, "Under review"),
        (RESOLVED, "Resolved"),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="issue_reports",
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issue_reports",
    )
    subject = models.CharField(max_length=140)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=OPEN)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"
