from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from bookings.models import Booking

from .forms import IssueReportForm, ReviewForm
from .models import IssueReport


@login_required
def leave_review(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related("technician__user", "service"),
        pk=booking_id,
    )
    if booking.customer_id != request.user.id:
        return HttpResponseForbidden("Only the customer of this job can review it.")
    if not booking.is_completed:
        messages.error(request, "You can only review a job after it is completed.")
        return redirect(booking)
    if hasattr(booking, "review"):
        messages.info(request, "You have already reviewed this job.")
        return redirect(booking)

    form = ReviewForm(request.POST or None, booking=booking, reviewer=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thank you. Your review has been posted.")
        return redirect(
            "technicians:technician_public_profile",
            username=booking.technician.user.username,
        )
    return render(
        request, "reviews/review_form.html", {"form": form, "booking": booking}
    )


@login_required
def report_issue(request):
    initial = {}
    booking_id = request.GET.get("booking", "")
    if booking_id.isdigit():
        initial["booking"] = booking_id
    form = IssueReportForm(request.POST or None, user=request.user, initial=initial)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your report was sent to the FixNaija team.")
        return redirect("reviews:my_reports")
    return render(request, "reviews/report_form.html", {"form": form})


@login_required
def my_reports(request):
    reports = IssueReport.objects.filter(reporter=request.user).select_related("booking")
    return render(request, "reviews/my_reports.html", {"reports": reports})
