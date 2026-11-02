from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    # customer reviews a completed booking
    path("booking/<int:booking_id>/", views.leave_review, name="leave"),

    # report a dispute or platform issue
    path("report/", views.report_issue, name="report"),

    # my submitted reports
    path("reports/", views.my_reports, name="my_reports"),
]
