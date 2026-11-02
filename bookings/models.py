from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

from technicians.models import ServiceArea, ServiceListing, TechnicianProfile


class Booking(models.Model):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

    STATUS_CHOICES = [
        (REQUESTED, "Requested"),
        (ACCEPTED, "Accepted"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
        (REJECTED, "Rejected"),
    ]

    # current status -> statuses it may move to
    TRANSITIONS = {
        REQUESTED: {ACCEPTED, REJECTED},
        ACCEPTED: {IN_PROGRESS, CANCELLED},
        IN_PROGRESS: {COMPLETED, CANCELLED},
        COMPLETED: set(),
        CANCELLED: set(),
        REJECTED: set(),
    }
    # only the technician may do these
    TECHNICIAN_ONLY = {ACCEPTED, REJECTED, IN_PROGRESS, COMPLETED}
    # the customer or the technician may do these
    EITHER_PARTY = {CANCELLED}

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings_made",
    )
    technician = models.ForeignKey(
        TechnicianProfile,
        on_delete=models.CASCADE,
        related_name="bookings_received",
    )
    service = models.ForeignKey(
        ServiceListing,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    area = models.ForeignKey(
        ServiceArea,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    address = models.CharField("Address", max_length=255)
    description = models.TextField("What needs fixing?", blank=True)
    preferred_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=12, choices=STATUS_CHOICES, default=REQUESTED
    )
    request_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-request_date"]

    def __str__(self):
        return f"Booking #{self.pk}: {self.service.title} ({self.get_status_display()})"

    def get_absolute_url(self):
        return reverse("bookings:detail", args=[self.pk])

    # ---------- validation ----------
    def clean(self):
        errors = {}
        if self.customer_id and self.technician_id:
            if self.customer_id == self.technician.user_id:
                errors["technician"] = "You cannot book your own service."
        if self.service_id and self.technician_id:
            if self.service.technician_id != self.technician_id:
                errors["service"] = "This service does not belong to that technician."
            elif not self.service.is_active or self.service.is_deleted:
                errors["service"] = "This service is not available right now."
        if self.service_id and self.area_id:
            if not self.service.service_areas.filter(pk=self.area_id).exists():
                errors["area"] = "The technician does not offer this service in that area."
        if self.pk is None and self.preferred_date:
            if self.preferred_date < timezone.localdate():
                errors["preferred_date"] = "The preferred date cannot be in the past."
        if errors:
            raise ValidationError(errors)

    # ---------- workflow ----------
    def is_technician(self, user):
        return user.is_authenticated and self.technician.user_id == user.id

    def is_customer(self, user):
        return user.is_authenticated and self.customer_id == user.id

    def allowed_actions(self, user):
        """Statuses this user may move the booking to right now."""
        allowed = set()
        for target in self.TRANSITIONS[self.status]:
            if target in self.TECHNICIAN_ONLY and self.is_technician(user):
                allowed.add(target)
            elif target in self.EITHER_PARTY and (
                self.is_technician(user) or self.is_customer(user)
            ):
                allowed.add(target)
        return allowed

    def change_status(self, new_status, user):
        labels = dict(self.STATUS_CHOICES)
        if new_status not in labels:
            raise ValidationError("Unknown status.")
        if new_status not in self.TRANSITIONS[self.status]:
            raise ValidationError(
                f"A {self.get_status_display()} booking cannot be changed to "
                f"{labels[new_status]}."
            )
        if new_status not in self.allowed_actions(user):
            raise ValidationError("You are not allowed to do this on this booking.")
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])

    @property
    def is_completed(self):
        return self.status == self.COMPLETED
