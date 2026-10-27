
from django.urls import path
from . import views

app_name = "technicians"

urlpatterns = [
    path(
        "services/create/",
        views.create_service_listing,
        name="create_service_listing",
    ),
    path(
    "services/<int:service_id>/edit/",
    views.edit_service,
    name="edit_service"
    ),  
    path(
        "services/<int:service_id>/delete/",
        views.delete_service,
        name="delete_service"
    ),
    
    path(
        "services/<int:service_id>/toggle-status/",
        views.toggle_service_status,
        name="toggle_service_status"
    ),
    path(
    "services/<int:service_id>/",
    views.service_detail,
    name="service_detail",
    ),
    path(
        "services/",
        views.service_list,
        name="service_list",
    ),
    path(
        "my-services/",
        views.my_services,
        name="my_services",
    ),
    path(
        "technician-setup/",
        views.technician_setup,
        name="technician_setup",
    ),
]
