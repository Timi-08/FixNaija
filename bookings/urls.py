from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    # customer books a service (login required)
    path("book/<int:service_id>/", views.book_service, name="book"),

    # customer: jobs I have booked
    path("mine/", views.my_bookings, name="my_bookings"),

    # technician: requests sent to me
    path("incoming/", views.incoming_requests, name="incoming"),

    # booking detail (customer or technician of that booking only)
    path("<int:booking_id>/", views.booking_detail, name="detail"),

    # move a booking along the status workflow (POST only)
    path(
        "<int:booking_id>/status/<str:new_status>/",
        views.change_status,
        name="change_status",
    ),
]
