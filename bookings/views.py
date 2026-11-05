from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from technicians.models import ServiceListing, TechnicianProfile

from .forms import BookingForm
from .models import Booking


@login_required
def book_service(request, service_id):
    service = get_object_or_404(
        ServiceListing.objects.select_related("technician__user", "category")
        .prefetch_related("service_areas"),
        pk=service_id,
        is_active=True,
        is_deleted=False,
        technician__user__is_active=True,
    )

    if service.technician.user_id == request.user.id:
        messages.error(request, "You cannot book your own service.")
        return redirect("technicians:service_detail", service_id=service.pk)

    form = BookingForm(
        request.POST or None, customer=request.user, service=service
    )
    if request.method == "POST" and form.is_valid():
        booking = form.save()
        messages.success(
            request,
            f"Your request has been sent to "
            f"{service.technician.user.get_full_name() or service.technician.user.username}. "
            "You will see the status change here.",
        )
        return redirect(booking)

    return render(
        request, "bookings/book.html", {"form": form, "service": service}
    )


@login_required
def my_bookings(request):
    """Jobs I booked as a customer."""
    status = request.GET.get("status", "")
    bookings = Booking.objects.filter(customer=request.user).select_related(
        "technician__user", "service", "area"
    ).prefetch_related("review")
    if status in dict(Booking.STATUS_CHOICES):
        bookings = bookings.filter(status=status)
    else:
        status = ""

    page_obj = Paginator(bookings, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "bookings/my_bookings.html",
        {
            "page_obj": page_obj,
            "statuses": Booking.STATUS_CHOICES,
            "current_status": status,
        },
    )


@login_required
def incoming_requests(request):
    """Jobs customers booked with me as a technician."""
    technician = TechnicianProfile.objects.filter(user=request.user).first()
    if technician is None:
        messages.info(request, "Create a technician profile to receive job requests.")
        return redirect("technicians:technician_setup")

    status = request.GET.get("status", "")
    bookings = Booking.objects.filter(technician=technician).select_related(
        "customer", "service", "area"
    )
    if status in dict(Booking.STATUS_CHOICES):
        bookings = bookings.filter(status=status)
    else:
        status = ""

    page_obj = Paginator(bookings, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "bookings/incoming.html",
        {
            "page_obj": page_obj,
            "statuses": Booking.STATUS_CHOICES,
            "current_status": status,
        },
    )


@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related(
            "customer", "technician__user", "service", "area"
        ),
        pk=booking_id,
    )
    if not (booking.is_customer(request.user) or booking.is_technician(request.user)):
        return HttpResponseForbidden("You are not part of this booking.")

    review = getattr(booking, "review", None)
    return render(
        request,
        "bookings/booking_detail.html",
        {
            "booking": booking,
            "actions": booking.allowed_actions(request.user),
            "viewer_is_technician": booking.is_technician(request.user),
            "review": review,
            "can_review": (
                booking.is_customer(request.user)
                and booking.is_completed
                and review is None
            ),
        },
    )


@login_required
@require_POST
def change_status(request, booking_id, new_status):
    booking = get_object_or_404(
        Booking.objects.select_related("technician__user"), pk=booking_id
    )
    if not (booking.is_customer(request.user) or booking.is_technician(request.user)):
        return HttpResponseForbidden("You are not part of this booking.")

    try:
        booking.change_status(new_status, request.user)
    except ValidationError as error:
        messages.error(request, " ".join(error.messages))
    else:
        messages.success(
            request, f"Booking #{booking.pk} is now {booking.get_status_display()}."
        )
    return redirect(booking)
